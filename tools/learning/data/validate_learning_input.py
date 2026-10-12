#!/usr/bin/env python3
"""Update-free learning-input reader and zero-tempo-delta verification.

Accepts provisional data for validation only. No search, loss, gradient or
parameter update is implemented; held-out teacher quality is not measured.
"""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

from tools.learning.data.audit_learning_provenance import audit
from tools.learning.data.prepare_learning_data import ROOT, VERSION, Probe, digest, outcome, teacher_rejection, validate_game, zero_copy

CHECKPOINT_SCHEMA = "rakuyou-zero-tempo-delta-v1"


def check_zero_delta(state, base_sha):
    if state.get("schema") != CHECKPOINT_SCHEMA or state.get("base_sha256") != base_sha:
        raise ValueError("Checkpoint schema/base mismatch")
    if type(state.get("updates")) is not int or state["updates"] != 0:
        raise ValueError("This entry accepts zero updates only")
    values = state.get("tempo_delta_cp")
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError("Exactly three tempo deltas required")
    if any(type(x) not in (int, float) or not math.isfinite(x) or x != 0 for x in values):
        raise ValueError("This entry accepts finite zero deltas only")


def read_rows(path, expected, split):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise ValueError("JSONL digest mismatch: " + split)
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    if not rows or len(rows) != expected["positions"]:
        raise ValueError("JSONL count mismatch: " + split)
    for row in rows:
        if row.get("schema") != VERSION or row.get("split") != split:
            raise ValueError("JSONL schema/split mismatch")
        if type(row.get("teacher_cp")) is not int or abs(row["teacher_cp"]) > 1000:
            raise ValueError("Invalid cp teacher")
        if type(row.get("depth")) is not int or row["depth"] != 15:
            raise ValueError("Unexpected teacher depth")
        if row.get("ShinYonenagaGyoku") is not True:
            raise ValueError("OFF teacher in ON dataset")
    return rows


def verify_row(row, source):
    if type(row.get("game")) is not int or not 1 <= row["game"] <= len(source["games"]):
        raise ValueError("Invalid source game")
    game = source["games"][row["game"]-1]
    validate_game(game, source["settings"])
    if type(row.get("ply")) is not int or not 24 <= row["ply"] <= 80:
        raise ValueError("Invalid source ply")
    if row["ply"] > len(game["records"]):
        raise ValueError("Ply outside game")
    record = game["records"][row["ply"]-1]
    if teacher_rejection(record) is not None:
        raise ValueError("Source record is not an eligible teacher")
    before = game["moves"][:row["ply"]-1]
    expected = {"moves_before": before, "move": record["move"],
                "pv": record["analysis"]["pv"], "teacher_cp": int(record["analysis"]["score"]),
                "side_to_move": record["color"], "result": game["result"],
                "termination": game["reason"], "outcome": outcome(game, record["color"]),
                "prefix24": " ".join(game["moves"][:24]),
                "stratum": record["color"] + ":" + game["result"]}
    if any(row.get(k) != v for k, v in expected.items()):
        raise ValueError("Teacher/source semantic mismatch")
    if row.get("id") != f"{row['run']}:{row['game']}:{row['ply']}":
        raise ValueError("Teacher ID mismatch")
    if row.get("provenance_status") != "historical_runtime_not_verified":
        raise ValueError("Unexpected provenance promotion")


def load_input(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get("schema") != VERSION or manifest.get("training_ready") is not False:
        raise ValueError("Expected provisional preparation manifest")
    if set(manifest.get("outputs", {})) != {"train", "validation", "test"}:
        raise ValueError("All three split definitions are required")
    audit(manifest_path)  # Original sources and split hashes, with archived report refs.
    sources = {}
    for s in manifest["sources"]:
        if s.get("excluded"):
            continue
        raw = (ROOT / s["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != s["sha256"]:
            raise ValueError("Source changed while reading")
        sources[(s["path"], s["sha256"])] = json.loads(raw)
    parts, seen = {}, {k: {} for k in ("run", "sfen", "prefix24", "id")}
    for split, expected in manifest["outputs"].items():
        path = manifest_path.parent / expected["path"]
        if not path.resolve().is_relative_to(manifest_path.parent):
            raise ValueError("Split path escapes preparation directory")
        rows = read_rows(path, expected, split)
        counts, roots, ids = Counter(), set(), set()
        for row in rows:
            if row.get("run") != row.get("source_sha256"):
                raise ValueError("Run/source identity mismatch")
            key = (row.get("source_path"), row["run"])
            if key not in sources or manifest["run_assignments"].get(row["run"]) != split:
                raise ValueError("Source or split assignment mismatch")
            verify_row(row, sources[key])
            if row["sfen"] in roots or row["id"] in ids:
                raise ValueError("Duplicate root/ID inside split")
            roots.add(row["sfen"]); ids.add(row["id"])
            counts[(row["run"], row["game"])] += 1
            if counts[(row["run"], row["game"])] > 8:
                raise ValueError("Per-game cap exceeded")
            for field, values in seen.items():
                if row[field] in values and values[row[field]] != split:
                    raise ValueError("Cross-split overlap: " + field)
                values[row[field]] = split
        parts[split] = rows
    return manifest, parts


def validate_native(parts, original, copied):
    counts = {}
    for split, rows in parts.items():
        for row in rows:
            # Validate the full teacher PV, and read static evaluation at its ROOT.
            moves = row["moves_before"] + row["pv"]
            a, b = original.replay(moves), copied.replay(moves)
            if not a.get("ok") or a != b:
                raise ValueError("Native replay or zero-delta reread mismatch")
            positions = a["positions"]
            if any(p["occurrences"] > 1 for p in positions):
                raise ValueError("Repeated root/PV history")
            root = positions[row["ply"]-1]
            if root["sfen"] != row["sfen"] or root["huffman_hex"] != row["huffman_hex"]:
                raise ValueError("Serialized root does not match replay")
            expected_side = "b" if row["side_to_move"] == "black" else "w"
            if root["sfen"].split()[1] != expected_side:
                raise ValueError("Native side-to-move mismatch")
            if not math.isfinite(root["progress"]) or not 0 <= root["progress"] <= 1:
                raise ValueError("Invalid progress")
        counts[split] = {"positions_checked": len(rows),
                         "strata": dict(Counter(r["stratum"] for r in rows))}
        print(f"Validated {split}: {len(rows)} roots and PVs", flush=True)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--base", type=Path, default=ROOT / "bin/params.bin")
    parser.add_argument("--probe", type=Path, default=ROOT / "results/learning-tools/learning-data-probe")
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    manifest, parts = load_input(args.manifest)
    runtime = {name: digest(ROOT / name) for name in manifest["runtime_sha256"]}
    if runtime != manifest["runtime_sha256"]:
        raise ValueError("Runtime differs from prepared baseline")
    base_sha = digest(args.base)
    if base_sha != manifest["runtime_sha256"]["bin/params.bin"]:
        raise ValueError("Fixed base differs from prepared baseline")
    state = {"schema": CHECKPOINT_SCHEMA, "base_sha256": base_sha,
             "updates": 0, "tempo_delta_cp": [0.0, 0.0, 0.0]}
    if args.checkpoint:
        state = json.loads(args.checkpoint.read_bytes())
    check_zero_delta(state, base_sha)
    args.output.mkdir(parents=True, exist_ok=False)
    copy = args.output / "params-zero-delta.bin"
    layout = zero_copy(args.base, copy, args.probe)
    if layout != manifest["native_layout"]:
        raise ValueError("Native ABI differs from prepared layout")
    def inspect(path):
        return json.loads(subprocess.check_output(
            [str(args.probe.resolve()), "--inspect-params", str(path.resolve())], text=True, timeout=30))
    base_info = inspect(args.base)
    if base_info != inspect(copy):
        raise ValueError("Tempo changed during zero-delta copy")
    original, copied = Probe(args.probe, args.base), Probe(args.probe, copy)
    try:
        counts = validate_native(parts, original, copied)
    finally:
        original.close(); copied.close()
    if runtime != {name: digest(ROOT / name) for name in runtime}:
        raise ValueError("Runtime changed during validation")
    if digest(copy) != base_sha or digest(args.base) != base_sha:
        raise ValueError("Fixed base/copy changed during validation")
    report = {"schema": "rakuyou-learning-input-validation-v1", "mode": "validate-only",
              "training_ready": False, "updates": 0,
              "preparation_manifest_sha256": digest(args.manifest),
              "tool_sha256": digest(Path(__file__)), "probe_sha256": digest(args.probe),
              "runtime_sha256": runtime, "native_layout": layout, "base_info": base_info,
              "base_sha256": base_sha, "zero_delta_checkpoint": state, "splits": counts,
              "limits": manifest["pending"],
              "teacher_quality_measured": False, "search_performed": False}
    for name, value in (("checkpoint-zero.json", state), ("validation.json", report)):
        with (args.output / name).open("x") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
    print(json.dumps({"training_ready": False, "updates": 0, "splits": counts}, indent=2))


if __name__ == "__main__":
    main()
