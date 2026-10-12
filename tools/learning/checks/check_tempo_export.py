#!/usr/bin/env python3
"""Manual candidate export/reread check; no training or candidate re-search."""

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
from tools.learning.checks.check_tempo_rounding import compare
from tools.learning.core.tempo_export import export_candidate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest",type=Path)
    parser.add_argument("train_leaves",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--probe",type=Path,default=ROOT/"results/learning-tools/learning-data-probe")
    args=parser.parse_args()
    if args.output.resolve().is_relative_to((ROOT/"bin").resolve()):raise ValueError("Runtime output forbidden")
    manifest,parts=load_input(args.manifest)
    q=json.loads(args.train_leaves.read_bytes())
    if (q.get("schema")!="rakuyou-qsearch-leaves-v1" or
            q.get("preparation_manifest_sha256")!=digest(args.manifest) or q.get("updates")!=0):
        raise ValueError("Unexpected frozen-leaf provenance")
    lookup={r["id"]:r for r in parts["train"]}
    frames=[f for f in q["frames"] if f["excluded"] is None]
    if not frames or any(f["id"] not in lookup for f in frames):raise ValueError("Non-train frozen leaves")
    runtime={n:digest(ROOT/n) for n in manifest["runtime_sha256"]}
    if runtime!=manifest["runtime_sha256"]:raise ValueError("Runtime differs from fixed base")
    args.output.mkdir(parents=True,exist_ok=False)
    candidate=args.output/"params-manual-delta.bin"
    metadata=export_candidate(ROOT/"bin/params.bin",candidate,(.25,-.5,.75),
                              runtime["bin/params.bin"],args.probe)
    baseline=Probe(args.probe,ROOT/"bin/params.bin",details=True)
    memory=Probe(args.probe,ROOT/"bin/params.bin",tempo_raw=metadata["raw_increments"])
    reread=Probe(args.probe,candidate,details=True)
    max_error=0.0
    try:
        for f in frames:
            row=lookup[f["id"]];moves=row["moves_before"]+f["qsearch"]["pv"]
            a,b,c=baseline.replay(moves),memory.replay(moves),reread.replay(moves)
            if not all(v.get("ok") for v in (a,b,c)) or b!=c:
                raise ValueError("Candidate reread differs from in-memory perturbation")
            leaf=a["positions"][-1]
            if leaf["sfen"]!=f["qsearch"]["leaf_sfen"] or leaf["eval_on"]!=f["qsearch"]["leaf_eval_full"]:
                raise ValueError("Frozen leaf identity mismatch")
            e,_=compare(leaf,c["positions"][-1],f["qsearch"]["leaf_side"],metadata["raw_increments"])
            max_error=max(max_error,e)
    finally:baseline.close();memory.close();reread.close()
    if runtime!={n:digest(ROOT/n) for n in runtime}:raise ValueError("Runtime changed during export check")
    report=dict(schema="rakuyou-tempo-export-validation-v1",candidate_kind="manual diagnostic; not learned",
                real_data_updates=0,training_ready=False,export=metadata,checked_leaves=len(frames),
                reread_matches_memory=True,max_smooth_delta_error_cp=max_error,
                runtime_sha256=runtime,preparation_manifest_sha256=digest(args.manifest),
                train_leaves_sha256=digest(args.train_leaves),probe_sha256=digest(args.probe),
                tool_sha256=digest(Path(__file__)),exporter_sha256=digest(ROOT/"tools/learning/core/tempo_export.py"))
    with (args.output/"validation.json").open("x") as stream:
        json.dump(report,stream,ensure_ascii=False,sort_keys=True,indent=2);stream.write("\n")
    print(json.dumps({k:report[k] for k in ("candidate_kind","checked_leaves","reread_matches_memory","max_smooth_delta_error_cp","export")},indent=2))


if __name__=="__main__":main()
