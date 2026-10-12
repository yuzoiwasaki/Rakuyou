#!/usr/bin/env python3
"""Independent integer-score reconstruction and in-memory tempo perturbations.

Only train roots are used. No search, optimizer or parameter file writes.
"""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.validate_learning_input import load_input
from tools.learning.core.tempo_objective import tempo_factors

SCALE = 65536
VARIANTS = [(0,0,0), (SCALE,0,0), (-SCALE,0,0), (0,SCALE,0), (0,-SCALE,0),
            (0,0,SCALE), (0,0,-SCALE), (16384,-32768,49152), (-16384,32768,-49152), (1,0,0)]


def trunc_div(numerator, denominator):
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError("Integer numerator and positive denominator required")
    return (1 if numerator >= 0 else -1) * (abs(numerator) // denominator)


def score_from_parts(parts, side, progress):
    if side not in ("black", "white") or not 0 <= progress <= 1:
        raise ValueError("Invalid side/progress")
    kp, others, tempo = (parts[k] for k in ("kp", "others", "tempo"))
    if any(len(v) != 4 or any(type(x) is not int for x in v) for v in (kp, others, tempo)):
        raise ValueError("Packed integer vectors required")
    p = int(progress*SCALE)
    if p < SCALE//2:
        w = (SCALE-2*p, 2*p, 0)
    else:
        w = (0, 2*SCALE-2*p, 2*p-SCALE)
    total = sum(a*b for a,b in zip(w,kp))
    t = sum(a*b for a,b in zip(w,tempo))
    sign = 1 if side == "black" else -1
    total += (SCALE-p)*(others[0]+sign*trunc_div(others[1],10))
    total += p*(others[2]+sign*trunc_div(others[3],10))
    total += sign*trunc_div(t,2)
    return sign*trunc_div(total,SCALE*SCALE)


def compare(base, changed, side, increments):
    for field in ("sfen", "huffman_hex", "occurrences", "progress"):
        if base[field] != changed[field]:
            raise ValueError("Position/progress changed under tempo perturbation")
    errors, changed_scores = [], 0
    for mode in ("on", "off"):
        a, b = base[mode+"_parts"], changed[mode+"_parts"]
        if a["kp"] != b["kp"] or a["others"] != b["others"]:
            raise ValueError("Non-tempo evaluation component changed")
        expected_tempo = [a["tempo"][i]+increments[i] for i in range(3)] + [a["tempo"][3]]
        if b["tempo"] != expected_tempo:
            raise ValueError("Tempo mutation does not match request")
        before, after = base["eval_"+mode], changed["eval_"+mode]
        if score_from_parts(a, side, base["progress"]) != before or score_from_parts(b, side, changed["progress"]) != after:
            raise ValueError("Independent integer reconstruction mismatch")
        smooth_change = sum(a*(b/SCALE) for a,b in zip(
            tempo_factors(base["progress"],side,side),increments))
        error = abs((after-before)-smooth_change)
        # Both integer scores are rounded toward zero; crossing zero can approach 2cp.
        if error >= 2.000001:
            raise ValueError("Smooth delta differs beyond integer-rounding bound")
        errors.append(error)
        changed_scores += before != after
    return max(errors), changed_scores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--probe", type=Path, default=ROOT / "results/learning-tools/learning-data-probe")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest, parts = load_input(args.manifest)
    runtime = {name:digest(ROOT/name) for name in manifest["runtime_sha256"]}
    if runtime != manifest["runtime_sha256"]:
        raise ValueError("Runtime differs from prepared baseline")
    rows, baseline = parts["train"], []
    native = Probe(args.probe, ROOT/"bin/params.bin", details=True)
    try:
        for row in rows:
            result = native.replay(row["moves_before"])
            if not result.get("ok"):
                raise ValueError("Baseline replay failed")
            root = result["positions"][-1]
            if root["sfen"] != row["sfen"] or root["huffman_hex"] != row["huffman_hex"]:
                raise ValueError("Root identity mismatch")
            baseline.append(root)
    finally:
        native.close()
    checks = []
    for increments in VARIANTS:
        native = Probe(args.probe, ROOT/"bin/params.bin", tempo_raw=increments)
        max_error, changes = 0, 0
        try:
            for row, base in zip(rows,baseline):
                result = native.replay(row["moves_before"])
                if not result.get("ok"):
                    raise ValueError("Perturbed replay failed")
                error, changed = compare(base,result["positions"][-1],row["side_to_move"],increments)
                max_error = max(max_error,error)
                changes += changed
        finally:
            native.close()
        checks.append(dict(raw_increments=list(increments),positions=len(rows),
                           changed_on_off_scores=changes,max_smooth_delta_error_cp=max_error))
        print(f"Checked raw tempo {increments}: {len(rows)} roots, max error {max_error:.6g}cp",flush=True)
    if runtime != {name:digest(ROOT/name) for name in runtime}:
        raise ValueError("Runtime changed during check")
    report = {"schema":"rakuyou-tempo-rounding-v1", "updates":0,
              "training_ready":False,"search_performed":False,"parameter_files_written":False,
              "integer_reconstruction_exact":True,"train_roots":len(rows),"variants":checks,
              "held_out_quality_measured":False,"runtime_sha256":runtime,
              "preparation_manifest_sha256":digest(args.manifest),"probe_sha256":digest(args.probe),
              "tool_sha256":digest(Path(__file__)),
              "limits":["perturbations applied only in isolated probe memory",
                        "static roots only; qsearch leaves and leaf switching not checked",
                        "historical teacher provenance and split limitations unchanged"]}
    with args.output.open("x") as stream:
        json.dump(report,stream,ensure_ascii=False,sort_keys=True,indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
