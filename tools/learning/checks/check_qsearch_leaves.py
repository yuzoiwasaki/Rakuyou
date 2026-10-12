#!/usr/bin/env python3
"""Bounded ON quiescence diagnostics and frozen-leaf checks, without updates."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.validate_learning_input import load_input
from tools.learning.core.tempo_objective import FrozenLeaf, check_gradient, leaf_sign
from tools.learning.checks.check_tempo_rounding import compare, score_from_parts


def select_roots(rows, limit=64):
    strata=defaultdict(list)
    for row in rows:
        strata[row["stratum"]].append(row)
    selected=[]
    for i in range(max(map(len,strata.values()),default=0)):
        for key in sorted(strata):
            if i<len(strata[key]):
                selected.append(strata[key][i])
                if len(selected)==limit:
                    return selected
    return selected


def eligibility(frame):
    if not frame.get("ok"):
        return "qsearch_failed"
    if abs(frame["qscore"])>=31000:
        return "known_win_or_mate"
    if frame["leaf_repetition"]:
        return "repetition_or_shek"
    if frame["leaf_in_check"]:
        return "nonstatic_terminal"
    if frame["leaf_eval_cached"]!=frame["leaf_eval_full"]:
        raise ValueError("Incremental/full leaf evaluation mismatch")
    expected=frame["root_side"] if len(frame["pv"])%2==0 else (
        "white" if frame["root_side"]=="black" else "black")
    if expected!=frame["leaf_side"]:
        raise ValueError("PV length/leaf turn mismatch")
    if frame["qscore"]!=leaf_sign(frame["root_side"],frame["leaf_side"])*frame["leaf_eval_full"]:
        return "qscore_not_static_leaf"
    return None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--probe",type=Path,default=ROOT/"results/learning-tools/learning-data-probe")
    parser.add_argument("--split",choices=("train","validation"),default="train")
    parser.add_argument("--prepare-only",action="store_true",help="save baseline leaves without teacher losses or perturbations")
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest,parts=load_input(args.manifest)
    runtime={name:digest(ROOT/name) for name in manifest["runtime_sha256"]}
    if runtime!=manifest["runtime_sha256"]:
        raise ValueError("Runtime differs from prepared baseline")
    prepare_only=args.prepare_only or args.split=="validation"
    rows=select_roots(parts[args.split])
    frames,accepted,rejected=[],[],Counter()
    q=Probe(args.probe,ROOT/"bin/params.bin",qsearch_progress=ROOT/"bin/progress.bin")
    static=Probe(args.probe,ROOT/"bin/params.bin",details=True)
    try:
        for row in rows:
            f=q.replay(row["moves_before"])
            if f.get("ok") and (f["root_sfen"]!=row["sfen"] or f["root_side"]!=row["side_to_move"]):
                raise ValueError("Qsearch root identity mismatch")
            reason=eligibility(f)
            record={"id":row["id"],"qsearch":f,"excluded":reason}
            frames.append(record)
            if reason:
                rejected[reason]+=1
                continue
            replay=static.replay(row["moves_before"]+f["pv"])
            if not replay.get("ok"):
                raise ValueError("Qsearch PV independent replay failed")
            if any(p["occurrences"]>1 for p in replay["positions"]):
                record["excluded"]="repeated_game_history"
                rejected[record["excluded"]]+=1
                continue
            leaf=replay["positions"][-1]
            if (leaf["sfen"]!=f["leaf_sfen"] or leaf["eval_on"]!=f["leaf_eval_full"] or
                    leaf["progress"]!=f["leaf_progress"] or leaf["on_parts"]!=f["leaf_parts"]):
                raise ValueError("Qsearch leaf independent evaluation mismatch")
            if score_from_parts(f["leaf_parts"],f["leaf_side"],f["leaf_progress"])!=f["leaf_eval_full"]:
                raise ValueError("Leaf integer reconstruction mismatch")
            sample=FrozenLeaf(f["leaf_eval_full"],row["teacher_cp"],f["leaf_progress"],
                              f["root_side"],f["leaf_side"])
            if not prepare_only:
                check_gradient([sample],(0,0,0))
                check_gradient([sample],(.25,-.5,.75))
            accepted.append((row,f,leaf,sample))
    finally:
        q.close();static.close()
    if not accepted:
        raise ValueError("No usable static qsearch leaves")
    samples=[a[3] for a in accepted]
    gradients=[] if prepare_only else [check_gradient(samples,d) for d in ((0,0,0),(.25,-.5,.75))]
    # Re-evaluate only the frozen PV leaf; do NOT search under changed tempo.
    perturbations=[]
    for increments in (() if prepare_only else ((16384,-32768,49152),(-16384,32768,-49152))):
        native=Probe(args.probe,ROOT/"bin/params.bin",tempo_raw=increments)
        max_error=0.0
        try:
            for row,f,base,sample in accepted:
                result=native.replay(row["moves_before"]+f["pv"])
                if not result.get("ok"):
                    raise ValueError("Frozen-leaf perturbed replay failed")
                changed=result["positions"][-1]
                error,_=compare(base,changed,f["leaf_side"],increments)
                max_error=max(max_error,error)
                root_after=leaf_sign(f["root_side"],f["leaf_side"])*changed["eval_on"]
                predicted=sample.predict(tuple(v/65536 for v in increments))
                if abs(root_after-predicted)>=2.000001:
                    raise ValueError("Root-perspective frozen-leaf delta mismatch")
        finally:
            native.close()
        perturbations.append(dict(raw_increments=list(increments),leaves=len(accepted),
                                  max_smooth_delta_error_cp=max_error))
    if runtime!={name:digest(ROOT/name) for name in runtime}:
        raise ValueError("Runtime changed during check")
    report={"schema":"rakuyou-qsearch-leaves-v1","updates":0,"training_ready":False,
            "parameter_files_written":False,"qsearch_calls":len(rows),"split":args.split,
            "prepare_only":prepare_only,
            "search_mode":"depth0/PV/ON/learning_mode_true/fresh1MBTT",
            "root_history":"Huffman boundary; pre-root Node history omitted like RootStrap",
            "probability_weights_used":False,"accepted_leaves":len(accepted),
            "excluded":dict(rejected),"leaf_pv_lengths":dict(Counter(str(len(a[1]["pv"])) for a in accepted)),
            "leaf_parity":dict(Counter("odd" if len(a[1]["pv"])%2 else "even" for a in accepted)),
            "root_sides":dict(Counter(a[1]["root_side"] for a in accepted)),
            "strata":dict(Counter(a[0]["stratum"] for a in accepted)),
            "gradients":gradients,"perturbations":perturbations,"frames":frames,
            "held_out_quality_measured":False,"changed_tempo_qsearch_calls":0,
            "runtime_sha256":runtime,"preparation_manifest_sha256":digest(args.manifest),
            "probe_sha256":digest(args.probe),"tool_sha256":digest(Path(__file__)),
            "limits":["bounded split diagnostic, not full dataset or strength validation",
                      "PV switching under perturbation untested","historical provenance remains provisional"]}
    with args.output.open("x") as stream:
        json.dump(report,stream,ensure_ascii=False,sort_keys=True,indent=2)
        stream.write("\n")
    print(json.dumps({k:report[k] for k in ("qsearch_calls","accepted_leaves","excluded",
        "leaf_parity","root_sides","leaf_pv_lengths","perturbations","gradients")},indent=2))


if __name__=="__main__":
    main()
