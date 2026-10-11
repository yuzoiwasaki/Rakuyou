#!/usr/bin/env python3
"""Check tempo derivatives using synthetic leaves and train roots; no updates."""
import argparse
import json
from collections import Counter
from pathlib import Path

from prepare_learning_data import ROOT, Probe, digest
from validate_learning_input import load_input
from tempo_objective import FrozenLeaf, check_gradient


def synthetic_checks():
    checks = []
    for p in (0, .25, .5-1/65536, .5, .5+1/65536, .75, 1):
        for root in ("black", "white"):
            for leaf in ("black", "white"):
                for cp in (-1200, 0, 1200):
                    samples = [FrozenLeaf(cp, 200, p, root, leaf)]
                    for delta in ((0, 0, 0), (.25, -.5, .75)):
                        for l2 in (0, 1e-4):
                            checks.append(check_gradient(samples, delta, l2))
    return {"cases": len(checks), "coefficient_checks": 3*len(checks),
            "max_absolute_error": max(c["max_absolute_error"] for c in checks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--probe", type=Path, default=ROOT / "results/learning-tools/learning-data-probe")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest, parts = load_input(args.manifest)
    runtime = {name: digest(ROOT/name) for name in manifest["runtime_sha256"]}
    if runtime != manifest["runtime_sha256"]:
        raise ValueError("Runtime differs from prepared baseline")
    synthetic = synthetic_checks()
    samples = []
    probe = Probe(args.probe, ROOT / "bin/params.bin")
    try:
        for row in parts["train"]:
            result = probe.replay(row["moves_before"])
            if not result.get("ok"):
                raise ValueError("Train root replay failed")
            root = result["positions"][-1]
            if root["sfen"] != row["sfen"] or root["huffman_hex"] != row["huffman_hex"]:
                raise ValueError("Train root identity mismatch")
            samples.append(FrozenLeaf(root["eval_on"], row["teacher_cp"], root["progress"],
                                      row["side_to_move"], row["side_to_move"]))
    finally:
        probe.close()
    checks = [check_gradient(samples, d) for d in ((0, 0, 0), (.25, -.5, .75))]
    if runtime != {name: digest(ROOT/name) for name in runtime}:
        raise ValueError("Runtime changed during numerical check")
    report = {"schema": "rakuyou-tempo-gradient-check-v1", "updates": 0,
              "training_ready": False, "search_performed": False,
              "parameter_files_written": False, "synthetic": synthetic,
              "train_positions": len(samples),
              "train_sides": dict(Counter(s.root_side for s in samples)),
              "progress_min": min(s.progress for s in samples),
              "progress_max": max(s.progress for s in samples), "train_checks": checks,
              "held_out_quality_measured": False,
              "limits": ["smooth surrogate excludes integer score rounding",
                         "real samples use static train roots, not qsearch leaves",
                         "root/leaf parity checks beyond zero ply are synthetic",
                         "historical provenance and split independence remain provisional"],
              "preparation_manifest_sha256": digest(args.manifest),
              "tool_sha256": digest(Path(__file__)),
              "objective_sha256": digest(ROOT / "tools/tempo_objective.py"),
              "probe_sha256": digest(args.probe), "runtime_sha256": runtime}
    with args.output.open("x") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"synthetic": synthetic, "train_positions": len(samples),
                      "train_checks": checks, "updates": 0}, indent=2))


if __name__ == "__main__":
    main()
