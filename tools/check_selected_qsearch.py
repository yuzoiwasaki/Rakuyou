#!/usr/bin/env python3
"""Locked selected-candidate Qsearch comparison: 32 validation + 32 test roots.

No training, tuning, alternative-candidate selection, deployment or game play.
"""
import argparse
import json
import math
from collections import Counter
from pathlib import Path

from prepare_learning_data import ROOT,Probe,digest
from validate_learning_input import load_input
from check_qsearch_leaves import eligibility,select_roots
from tempo_objective import GAIN,sigmoid


def compare_frames(row,base,candidate):
    for f in (base,candidate):
        if not f.get("ok") or f["root_sfen"]!=row["sfen"] or f["root_side"]!=row["side_to_move"]:
            raise ValueError("Re-search root mismatch")
    a,b=eligibility(base),eligibility(candidate)
    result=dict(id=row["id"],run=row["run"],stratum=row["stratum"],
                base=base,candidate=candidate,base_excluded=a,candidate_excluded=b,
                pv_changed=base["pv"]!=candidate["pv"],leaf_changed=base["leaf_sfen"]!=candidate["leaf_sfen"])
    if a is None and b is None:
        t=row["teacher_cp"];x=base["qscore"];y=candidate["qscore"]
        result.update(cp_change=y-x,cp_error_base=t-x,cp_error_candidate=t-y,
            sigmoid_loss_base=(sigmoid(GAIN*x)-sigmoid(GAIN*t))**2,
            sigmoid_loss_candidate=(sigmoid(GAIN*y)-sigmoid(GAIN*t))**2)
    return result


def summarize(records):
    valid=[r for r in records if "cp_change" in r]
    values=[r["cp_change"] for r in valid]
    return dict(roots=len(records),comparable=len(valid),pv_changed=sum(r["pv_changed"] for r in records),
        leaf_changed=sum(r["leaf_changed"] for r in records),
        score_changed=sum(v!=0 for v in values),cp_change_min=min(values,default=None),cp_change_max=max(values,default=None),
        raw_sigmoid_loss_base=math.fsum(r["sigmoid_loss_base"] for r in valid)/len(valid) if valid else None,
        raw_sigmoid_loss_candidate=math.fsum(r["sigmoid_loss_candidate"] for r in valid)/len(valid) if valid else None,
        cp_rmse_base=math.sqrt(math.fsum(r["cp_error_base"]**2 for r in valid)/len(valid)) if valid else None,
        cp_rmse_candidate=math.sqrt(math.fsum(r["cp_error_candidate"]**2 for r in valid)/len(valid)) if valid else None,
        strata=dict(Counter(r["stratum"] for r in records)))


def locked_candidate(report_path):
    r=json.loads(Path(report_path).read_bytes())
    if r.get("schema")!="rakuyou-tempo-pilot-run-v1" or r.get("mode")!="run" or r.get("real_data_updates")!=20 or r.get("deployed") is not False:
        raise ValueError("Expected completed, undeployed bounded pilot")
    selected=r.get("selected_update")
    if selected not in (5,10,20):raise ValueError("No learned candidate selected")
    entry=next(s for s in r["saved"] if s["update"]==selected)
    candidate=Path(report_path).resolve().parent/f"params-average-{selected:02d}.bin"
    if digest(candidate)!=entry["export"]["candidate_sha256"]:raise ValueError("Selected candidate SHA mismatch")
    return r,candidate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest",type=Path)
    parser.add_argument("pilot_report",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--probe",type=Path,default=ROOT/"results/learning-tools/learning-data-probe")
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    pilot,candidate=locked_candidate(args.pilot_report)
    manifest,parts=load_input(args.manifest)
    if digest(args.manifest)!=pilot["binding"]["manifest_sha256"]:raise ValueError("Pilot input mismatch")
    runtime={name:digest(ROOT/name) for name in manifest["runtime_sha256"]}
    if runtime!=pilot["runtime_sha256"]:raise ValueError("Runtime no longer matches baseline")
    batches={name:select_roots(parts[name],32) for name in ("validation","test")}
    if any(len(v)!=32 for v in batches.values()):raise ValueError("Need 32 roots per split")
    if {r["run"] for r in batches["validation"]}&{r["run"] for r in batches["test"]}:
        raise ValueError("Split runs overlap")
    base=Probe(args.probe,ROOT/"bin/params.bin",qsearch_progress=ROOT/"bin/progress.bin")
    trial=Probe(args.probe,candidate,qsearch_progress=ROOT/"bin/progress.bin")
    records={}
    try:
        for split,rows in batches.items():
            records[split]=[compare_frames(row,base.replay(row["moves_before"]),trial.replay(row["moves_before"])) for row in rows]
            print(json.dumps({"split":split,**summarize(records[split])},indent=2),flush=True)
    finally:base.close();trial.close()
    if runtime!={n:digest(ROOT/n) for n in runtime}:raise ValueError("Runtime changed during re-search")
    report=dict(schema="rakuyou-selected-qsearch-check-v1",selected_update=pilot["selected_update"],
        candidate_sha256=digest(candidate),pilot_report_sha256=digest(args.pilot_report),
        manifest_sha256=digest(args.manifest),qsearch_calls=128,real_data_updates=0,
        candidate_reselected=False,deployed=False,records=records,
        summaries={s:summarize(rows) for s,rows in records.items()},runtime_sha256=runtime,
        probe_sha256=digest(args.probe),tool_sha256=digest(Path(__file__)),
        limits=["depth0 quiescence only, not full-depth search or games",
                "32 test roots now used for final selected-candidate diagnostic; 224 remain quality-unseen",
                "historical teacher provenance/correlation caveats remain"])
    with args.output.open("x") as stream:
        json.dump(report,stream,ensure_ascii=False,sort_keys=True,indent=2);stream.write("\n")


if __name__=="__main__":main()
