#!/usr/bin/env python3
"""Prepare provisional, audited search teachers. Never runs search or learning.

Outputs remain provisional until historical runtime provenance is reviewed.
The native probe replays moves, validates PVs and round-trips Huffman positions.
"""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))

import argparse
import hashlib
import json
import re
import selectors
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from tools.analysis.paired_selfplay import summarize

ROOT = Path(__file__).resolve().parents[3]
VERSION = "rakuyou-search-teachers-v1"
TOKEN = re.compile(r"(?:[1-9][a-i][1-9][a-i]\+?|[PLNSGBR]\*[1-9][a-i])\Z")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_order(seed, value):
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


class Probe:
    def __init__(self, binary, params=None, *, details=False, tempo_raw=None, qsearch_progress=None):
        if qsearch_progress is not None and (details or tempo_raw is not None):
            raise ValueError("Qsearch cannot run with tempo perturbations or static details")
        if (details or tempo_raw is not None or qsearch_progress is not None) and params is None:
            raise ValueError("Parameter file required for detailed evaluation")
        if tempo_raw is not None and (len(tempo_raw) != 3 or
                any(type(v) is not int or abs(v) > 5*65536 for v in tempo_raw)):
            raise ValueError("Three bounded raw tempo increments required")
        self.errors = tempfile.TemporaryFile(mode="w+t")
        args = [str(Path(binary).resolve()), "--replay"]
        if params is not None:
            mode = "--qsearch" if qsearch_progress is not None else "--perturb-tempo" if tempo_raw is not None else "--evaluate-details" if details else "--evaluate"
            args = [str(Path(binary).resolve()), mode, str(Path(params).resolve())]
            if tempo_raw is not None:
                args.extend(str(v) for v in tempo_raw)
            if qsearch_progress is not None:
                args.append(str(Path(qsearch_progress).resolve()))
        self.qsearch = qsearch_progress is not None
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.errors,
                                        text=True, bufsize=1)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def replay(self, moves):
        if len(moves) > 600 or any(not isinstance(m, str) or not TOKEN.fullmatch(m) for m in moves):
            return {"ok": False, "error": "move_syntax"}
        self.process.stdin.write(" ".join(moves) + "\n")
        self.process.stdin.flush()
        if not self.selector.select(timeout=30):
            raise RuntimeError("Native validation timed out")
        line = self.process.stdout.readline()
        if not line:
            self.errors.seek(0)
            raise RuntimeError("Native validation failed: " + self.errors.read()[-1000:])
        result = json.loads(line)
        if result.get("ok") and not self.qsearch and len(result["positions"]) != len(moves) + 1:
            raise ValueError("Native replay length mismatch")
        return result

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process.stdout.close()
        self.selector.close()
        self.errors.close()


def outcome(game, side):
    """Only verified result types supply outcome targets; max_plies stays unknown."""
    result, reason = game["result"], game["reason"]
    if reason == "max_plies" and result == "draw":
        return {"kind": "truncated", "target": None, "use_outcome_loss": False}
    if reason in ("resign", "declaration") and result in ("black_win", "white_win"):
        return {"kind": "decisive", "target": float(result == side + "_win"),
                "use_outcome_loss": True}
    # Formal draws require a separate adjudication audit, not just a reason string.
    return {"kind": "unverified", "target": None, "use_outcome_loss": False}


def validate_game(game, settings):
    moves, records = game["moves"], game["records"]
    if not isinstance(moves, list) or not records or len(moves) > 600:
        raise ValueError("Empty or oversized game")
    if moves != [r["move"] for r in records if r["move"] not in ("resign", "win")]:
        raise ValueError("Records/moves mismatch")
    if {game["black"], game["white"]} != {"shin_yonenaga", "normal"}:
        raise ValueError("Unexpected players")
    for ply, record in enumerate(records, 1):
        color = "black" if ply % 2 else "white"
        if (record["ply"], record["color"], record["player"]) != (ply, color, game[color]):
            raise ValueError("Ply/color/player mismatch")
        if record["move"] in ("resign", "win") and ply != len(records):
            raise ValueError("Termination inside game")
    last = records[-1]
    reason = game["reason"]
    if reason == "max_plies":
        if len(moves) != settings["max_plies"] or game["result"] != "draw" or game["winner"] is not None:
            raise ValueError("Invalid max_plies outcome")
        if last["move"] in ("resign", "win"):
            raise ValueError("Invalid max_plies terminal token")
    elif reason in ("resign", "declaration"):
        if last["move"] != ("resign" if reason == "resign" else "win"):
            raise ValueError("Invalid terminal token")
        winner_side = last["color"]
        if reason == "resign":
            winner_side = "white" if winner_side == "black" else "black"
        if game["result"] != winner_side + "_win" or game["winner"] != game[winner_side]:
            raise ValueError("Outcome/terminal mismatch")
    else:
        raise ValueError("Unverified termination kind")


def teacher_rejection(record):
    if record["player"] != "shin_yonenaga":
        return "off_player"
    if record["source"] != "search":
        return "non_search"
    if record["move"] in ("resign", "win") or not 24 <= record["ply"] <= 80:
        return "outside_window"
    a = record.get("analysis") or {}
    if a.get("score_type") != "cp" or a.get("depth") != 15:
        return "not_depth15_cp"
    if a.get("stopped_early") or a.get("lowerbound") or a.get("upperbound"):
        return "incomplete_or_bound"
    raw = a.get("raw", "")
    if not isinstance(raw, str) or not raw or re.search(r"\b(?:lowerbound|upperbound)\b", raw):
        return "missing_raw_or_bound"
    try:
        score = int(a["score"])
    except (TypeError, ValueError, KeyError):
        return "invalid_score"
    # Preserve the raw search's condition, not just a parsed field.
    if not re.search(r"\bdepth 15\b", raw) or not re.search(rf"\bscore cp {score}(?:\s|$)", raw):
        return "raw_mismatch"
    pv = a.get("pv")
    if not isinstance(pv, list) or not pv or pv[0] != record["move"]:
        return "pv_mismatch"
    if raw.split(" pv ")[-1].split() != pv:
        return "raw_pv_mismatch"
    if abs(score) > 1000:
        return "cp_outside_limit"
    return None


def collect(paths, probe):
    rows, sources, excluded = [], [], Counter()
    totals = Counter()
    for path in paths:
        path = Path(path).resolve()
        name = path.relative_to(ROOT).as_posix()
        document = json.loads(path.read_bytes())
        if not isinstance(document, dict) or "games" not in document:
            continue
        sha = digest(path)
        source = {"path": name, "sha256": sha, "games": len(document["games"]),
                  "historical_runtime_provenance": "not_verified"}
        sources.append(source)
        settings = document["settings"]
        count = document.get("requested_games", 2 * document.get("requested_pairs", 0))
        if document.get("errors") or count != len(document["games"]):
            source["excluded"] = "incomplete_or_error_run"
            excluded[source["excluded"]] += len(document["games"])
            continue
        expected = summarize(document["games"])
        expected["errors"] = 0
        if settings.get("shin_side", "both") != "both":
            expected["pairs_completed"] = None
        if expected != document.get("summary"):
            raise ValueError(f"Summary mismatch: {name}")
        if settings.get("depth") != 15 or settings.get("players", {}).get("shin_yonenaga", {}).get("ShinYonenagaGyoku") is not True:
            source["excluded"] = "wrong_search_condition"
            excluded[source["excluded"]] += len(document["games"])
            continue
        # Store relevant conditions without machine-specific absolute paths.
        source["conditions"] = {k: settings.get(k) for k in (
            "depth", "threads_per_engine", "hash_mb_per_engine", "ponder",
            "book_max_ply", "shin_side", "max_plies", "players")}
        source["conditions"]["book_names"] = {
            k: Path(settings[k]).name if settings.get(k) else None
            for k in ("book_file", "shin_book_file")}
        for number, game in enumerate(document["games"], 1):
            validate_game(game, settings)
            replay = probe.replay(game["moves"])
            if not replay.get("ok"):
                raise ValueError(f"Game replay failed: {name} game {number}: {replay}")
            totals["games_replayed"] += 1
            totals["moves_replayed"] += len(game["moves"])
            totals["games_" + game["reason"]] += 1
            positions = replay["positions"]
            repeated_history = False
            for record in game["records"]:
                root = positions[min(record["ply"] - 1, len(positions)-1)]
                repeated_history |= root["occurrences"] > 1
                rejection = teacher_rejection(record)
                if rejection:
                    excluded[rejection] += 1
                    continue
                if repeated_history:
                    excluded["repeated_history"] += 1
                    continue
                before = game["moves"][:record["ply"]-1]
                pv = record["analysis"]["pv"]
                pv_check = probe.replay(before + pv)
                if not pv_check.get("ok"):
                    excluded["illegal_pv"] += 1
                    continue
                if any(p["occurrences"] > 1 for p in pv_check["positions"]):
                    excluded["pv_repeated_history"] += 1
                    continue
                side = record["color"]
                rows.append({"schema": VERSION, "id": f"{sha}:{number}:{record['ply']}",
                    "run": sha, "game": number, "ply": record["ply"],
                    "source_path": name, "source_sha256": sha,
                    "sfen": root["sfen"], "huffman_hex": root["huffman_hex"],
                    "moves_before": before, "move": record["move"], "side_to_move": side,
                    "teacher_cp": int(record["analysis"]["score"]), "depth": 15,
                    "pv": pv, "ShinYonenagaGyoku": True, "result": game["result"],
                    "termination": game["reason"], "outcome": outcome(game, side),
                    "stratum": side + ":" + game["result"],
                    "prefix24": " ".join(game["moves"][:24]),
                    "provenance_status": "historical_runtime_not_verified"})
        print(f"Audited {name}: {len(document['games'])} games", flush=True)
    return rows, sources, dict(excluded), dict(totals)


def split_rows(rows, seed=20261011, caps=(1024, 256, 256)):
    """Hold out whole runs, then remove shared root SFENs and 24-move prefixes.

    Leakage checks use all eligible candidates before the per-game/output caps.
    This retains within-run correlation while rejecting cross-split duplicates.
    """
    names = ("train", "validation", "test")
    run_sides = defaultdict(set)
    for row in rows:
        run_sides[row["run"]].add(row["side_to_move"])
    buckets = defaultdict(list)
    for run, sides in run_sides.items():
        buckets[tuple(sorted(sides))].append(run)
    assignments = {}
    for runs in buckets.values():
        runs.sort(key=lambda v: stable_order(seed, v))
        if len(runs) < 3:
            # Such runs can help training, but cannot invent independent held-outs.
            assignments.update((run, "train") for run in runs)
            continue
        held = max(1, len(runs) // 5)
        for i, run in enumerate(runs):
            assignments[run] = "validation" if i < held else "test" if i < 2*held else "train"
    root_splits, prefix_splits = defaultdict(set), defaultdict(set)
    for row in rows:
        part = assignments[row["run"]]
        root_splits[row["sfen"]].add(part)
        prefix_splits[row["prefix24"]].add(part)
    eligible, exclusions = defaultdict(list), Counter()
    for row in rows:
        if len(root_splits[row["sfen"]]) > 1:
            exclusions["shared_sfen"] += 1
        elif len(prefix_splits[row["prefix24"]]) > 1:
            exclusions["shared_prefix24"] += 1
        else:
            eligible[assignments[row["run"]]].append(row)
    output = {}
    for name, cap in zip(names, caps):
        # Fair round-robin across side/result strata; explicit sampling, no win relabeling.
        strata = defaultdict(list)
        for row in eligible[name]:
            strata[row["stratum"]].append(row)
        for group in strata.values():
            group.sort(key=lambda row: stable_order(seed, row["id"]))
        games, seen = Counter(), set()
        chosen = []
        for i in range(max((len(g) for g in strata.values()), default=0)):
            for key in sorted(strata):
                if i >= len(strata[key]):
                    continue
                row = strata[key][i]
                game = (row["run"], row["game"])
                if row["sfen"] in seen:
                    exclusions["duplicate_sfen"] += 1
                elif games[game] >= 8:
                    exclusions["game_cap"] += 1
                elif len(chosen) < cap:
                    seen.add(row["sfen"])
                    games[game] += 1
                    chosen.append({**row, "split": name})
            if len(chosen) >= cap:
                break
        output[name] = chosen
    return output, assignments, dict(exclusions)


def zero_copy(base, output, probe):
    """Strict native-layout check and exclusive, byte-identical zero-delta output."""
    layout = json.loads(subprocess.check_output([str(Path(probe).resolve()), "--layout"], text=True))
    if Path(base).stat().st_size != layout["eval_parameters_bytes"]:
        raise ValueError("Base parameters do not match the native ABI size")
    if Path(base).resolve() == Path(output).resolve():
        raise ValueError("Input and output must differ")
    with Path(base).open("rb") as src, Path(output).open("xb") as dst:
        shutil.copyfileobj(src, dst)
    if digest(base) != digest(output):
        raise ValueError("Zero-delta copy mismatch")
    return layout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path)
    parser.add_argument("--probe", type=Path, default=ROOT / "results/learning-tools/learning-data-probe")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--base", type=Path, default=ROOT / "bin/params.bin")
    args = parser.parse_args()
    paths = sorted(args.inputs or (ROOT / "results").glob("*.json"))
    runtime_names = ("bin/release", "bin/params.bin", "bin/progress.bin", "bin/probability.bin",
                     "bin/book.bin", "books/shin-yonenaga-book-v1.txt")
    runtime_before = {name: digest(ROOT / name) for name in runtime_names}
    # Never reuse an output directory or touch original data.
    args.output.mkdir(parents=True, exist_ok=False)
    probe = Probe(args.probe)
    try:
        rows, sources, exclusions, totals = collect(paths, probe)
    finally:
        probe.close()
    eligible_count = len(rows)
    parts, assignments, split_exclusions = split_rows(rows, args.seed)
    if any(not rows for rows in parts.values()):
        raise ValueError("Insufficient independent train/validation/test candidates")
    zero = args.output / "params-zero-delta.bin"
    layout = zero_copy(args.base, zero, args.probe)
    # Compare static evaluations of selected prefixes, including both colors/draws.
    samples = []
    for rows in parts.values():
        seen_strata = set()
        for row in rows:
            if row["stratum"] not in seen_strata:
                seen_strata.add(row["stratum"])
                samples.append(row["moves_before"] + [row["move"]])
    original, copied = Probe(args.probe, args.base), Probe(args.probe, zero)
    try:
        for moves in samples:
            a, b = original.replay(moves), copied.replay(moves)
            if not a.get("ok") or a != b:
                raise ValueError("Zero-delta evaluation roundtrip mismatch")
    finally:
        original.close()
        copied.close()
    outputs = {}
    for name, rows in parts.items():
        p = args.output / (name + ".provisional.jsonl")
        with p.open("x") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        outputs[name] = {"path": p.name, "sha256": digest(p), "positions": len(rows),
                         "strata": dict(Counter(r["stratum"] for r in rows)),
                         "runs": len({r["run"] for r in rows})}
    runtime = {name: digest(ROOT / name) for name in runtime_names}
    if runtime != runtime_before:
        raise ValueError("Runtime files changed during preparation")
    manifest = {"schema": VERSION, "training_ready": False,
        "pending": ["historical per-run engine/evaluation/data provenance review",
                    "long-prefix correlation beyond the first 24 moves",
                    "formal repetition/perpetual-check adjudication"],
        "seed": args.seed, "sources": sources, "totals": totals,
        "eligible_candidates": eligible_count,
        "selected_positions": sum(len(v) for v in parts.values()),
        "exclusions": exclusions, "split_exclusions": split_exclusions,
        "run_assignments": assignments, "outputs": outputs, "native_layout": layout,
        "probe_sha256": digest(args.probe), "runtime_sha256": runtime,
        "tool_sha256": digest(Path(__file__)),
        "zero_delta": {"sha256": digest(zero), "evaluation_sample_prefixes": len(samples)},
        "sampling": "equal side/result strata, max8/game, max1/root, shared SFEN/prefix24 removed",
        "outcome_policy": "max_plies masked; cp teachers retained; no draws relabeled as wins"}
    with (args.output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"totals": totals, "outputs": outputs, "training_ready": False}, indent=2))


if __name__ == "__main__":
    main()
