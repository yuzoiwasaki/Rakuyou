#!/usr/bin/env python3
"""Isolated fixed-leaf pilot. Default dry-run never computes quality or updates.

--run requires a plan explicitly enabling real-data training. No deployment,
new search or modification of runtime bin files is implemented.
"""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.validate_learning_input import load_input
from tools.learning.checks.check_qsearch_leaves import eligibility
from tools.learning.core.tempo_objective import FrozenLeaf, objective, leaf_sign, sigmoid, GAIN
from tools.learning.core.tempo_updater import Config, initial, sample_batch, step, checkpoint, restore
from tools.learning.core.tempo_export import export_candidate
from tools.learning.core.learning_backup import create_backup, verify_backup


def load_plan(path,run=False):
    plan=json.loads(Path(path).read_bytes())
    if plan.get("schema")!="rakuyou-tempo-pilot-plan-v1" or plan.get("deployment_enabled") is not False:
        raise ValueError("Invalid non-deploying pilot plan")
    if plan.get("optimizer")!=asdict(Config()) or plan.get("save_updates")!=[0,5,10,20]:
        raise ValueError("Settings differ from tested fixed pilot")
    if plan.get("train_roots")!=64 or plan.get("validation_roots_max")!=64 or plan.get("outcome_loss_enabled") is not False:
        raise ValueError("Unexpected dataset/outcome scope")
    if type(plan.get("real_data_training_enabled")) is not bool:
        raise ValueError("Explicit training flag required")
    if run and not plan["real_data_training_enabled"]:
        raise ValueError("Real-data training remains disabled by the plan")
    return plan


def load_leaves(path,part,plan,manifest_sha,rows):
    key="train_qsearch_diagnostic_sha256" if part=="train" else "validation_qsearch_diagnostic_sha256"
    if digest(path)!=plan[key]:raise ValueError("Frozen leaf cache SHA mismatch")
    data=json.loads(Path(path).read_bytes())
    if (data.get("schema")!="rakuyou-qsearch-leaves-v1" or data.get("updates")!=0 or
            data.get("preparation_manifest_sha256")!=manifest_sha or
            data.get("split","train")!=part or data.get("training_ready") is not False):
        raise ValueError("Frozen cache metadata mismatch")
    lookup={r["id"]:r for r in rows};records=[]
    for item in data["frames"]:
        if item["excluded"] is not None:continue
        if item["id"] not in lookup:raise ValueError("Frozen leaf outside split")
        row=lookup[item["id"]];f=item["qsearch"]
        if eligibility(f) is not None or f["root_sfen"]!=row["sfen"] or f["root_side"]!=row["side_to_move"]:
            raise ValueError("Invalid frozen root/leaf")
        records.append(dict(row=row,frame=f,sample=FrozenLeaf(f["leaf_eval_full"],row["teacher_cp"],
                         f["leaf_progress"],f["root_side"],f["leaf_side"])))
    if len(records)!=64 or len({r["row"]["id"] for r in records})!=64:
        raise ValueError("Exactly 64 unique frozen roots required")
    return records


def assert_disjoint(train,val):
    for field in ("run","sfen"):
        if {r["row"][field] for r in train}&{r["row"][field] for r in val}:
            raise ValueError("Train/validation overlap: "+field)
    if {r["frame"]["leaf_sfen"] for r in train}&{r["frame"]["leaf_sfen"] for r in val}:
        raise ValueError("Train/validation frozen leaf overlap")


def advance(state,samples,config):
    ids,sampled=sample_batch(state,len(samples),config)
    loss,gradient=objective([samples[i] for i in ids],state.delta,config.l2)
    if not math.isfinite(loss):raise ValueError("Nonfinite training loss")
    return step(sampled,gradient,config)


def verify_candidate(path,records,probe,measure_quality=False,delta=(0,0,0),l2=1e-6):
    native=Probe(probe,path,details=True);terms=[];changes=0
    try:
        for record in records:
            row,f=record["row"],record["frame"]
            result=native.replay(row["moves_before"]+f["pv"])
            if not result.get("ok"):raise ValueError("Candidate leaf replay failed")
            leaf=result["positions"][-1]
            if leaf["sfen"]!=f["leaf_sfen"] or leaf["progress"]!=f["leaf_progress"]:
                raise ValueError("Candidate leaf identity/progress changed")
            for field in ("kp","others"):
                if leaf["on_parts"][field]!=f["leaf_parts"][field]:raise ValueError("Non-tempo parts changed")
            if leaf["on_parts"]["tempo"][3]!=f["leaf_parts"]["tempo"][3]:raise ValueError("Tempo fourth entry changed")
            changes+=leaf["eval_on"]!=f["leaf_eval_full"]
            if measure_quality:
                score=leaf_sign(f["root_side"],f["leaf_side"])*leaf["eval_on"]
                terms.append((sigmoid(GAIN*score)-sigmoid(GAIN*row["teacher_cp"]))**2)
    finally:native.close()
    return dict(positions=len(records),changed_integer_scores=changes,
                loss=(math.fsum(terms)/len(terms)+.5*l2*math.fsum(v*v for v in delta)) if terms else None)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest",type=Path)
    parser.add_argument("train_leaves",type=Path)
    parser.add_argument("validation_leaves",type=Path)
    parser.add_argument("--plan",type=Path,default=ROOT/"docs/experiments/configs/tempo-pilot-v1.json")
    parser.add_argument("--backup",type=Path,required=True)
    parser.add_argument("--create-backup",action="store_true")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--resume",type=Path)
    parser.add_argument("--probe",type=Path,default=ROOT/"results/learning-tools/learning-data-probe")
    args=parser.parse_args()
    plan=load_plan(args.plan,args.run)
    manifest,parts=load_input(args.manifest);manifest_sha=digest(args.manifest)
    if manifest_sha!=plan["preparation_manifest_sha256"]:raise ValueError("Preparation plan SHA mismatch")
    train=load_leaves(args.train_leaves,"train",plan,manifest_sha,parts["train"])
    val=load_leaves(args.validation_leaves,"validation",plan,manifest_sha,parts["validation"])
    assert_disjoint(train,val)
    runtime={n:digest(ROOT/n) for n in manifest["runtime_sha256"]}
    if runtime!=manifest["runtime_sha256"] or runtime["bin/params.bin"]!=plan["base_params_sha256"]:
        raise ValueError("Fixed runtime mismatch")
    required=dict(runtime)
    for path in (args.manifest,args.train_leaves,args.validation_leaves,args.plan,args.probe):
        required[path.resolve().relative_to(ROOT).as_posix()]=digest(path)
    for record in manifest["outputs"].values():
        path=args.manifest.resolve().parent/record["path"]
        required[path.relative_to(ROOT).as_posix()]=record["sha256"]
    for source in manifest["sources"]:
        if not source.get("excluded"):required[source["path"]]=source["sha256"]
    if args.create_backup:create_backup(required.keys(),args.backup.parent)
    verify_backup(args.backup,required)
    if args.output.resolve().is_relative_to((ROOT/"bin").resolve()):raise ValueError("Runtime output forbidden")
    args.output.mkdir(parents=True,exist_ok=False)
    config=Config()
    binding=dict(base_sha256=plan["base_params_sha256"],manifest_sha256=manifest_sha,
        plan_sha256=digest(args.plan),train_sha256=digest(args.train_leaves),val_sha256=digest(args.validation_leaves),
        objective_sha256=digest(ROOT/"tools/learning/core/tempo_objective.py"),updater_sha256=digest(ROOT/"tools/learning/core/tempo_updater.py"),
        teacher_origin=plan["teacher_origin"],input_kind="historical-search-cp")
    state=initial(config)
    if args.resume:state=restore(json.loads(args.resume.read_bytes()),config,binding)
    if not args.run and state.updates!=0:raise ValueError("Dry-run accepts initial state only")
    saved=[]
    def save(saved_state):
        label=f"{saved_state.updates:02d}";delta=saved_state.average()
        candidate=args.output/f"params-average-{label}.bin"
        exported=export_candidate(ROOT/"bin/params.bin",candidate,delta,plan["base_params_sha256"],args.probe)
        checked=verify_candidate(candidate,train+val,args.probe)
        checked_val=verify_candidate(candidate,val,args.probe,True,delta,config.l2) if args.run else None
        payload=checkpoint(saved_state,config,binding)
        with (args.output/f"checkpoint-{label}.json").open("x") as stream:
            json.dump(payload,stream,sort_keys=True,indent=2,allow_nan=False);stream.write("\n")
        saved.append(dict(update=saved_state.updates,export=exported,verification=checked,validation=checked_val))
    started_at=state.updates
    if args.resume and args.run:
        if state.updates not in plan["save_updates"]:raise ValueError("Resume must use a scheduled checkpoint")
        for n in plan["save_updates"]:
            if n>state.updates:break
            old=restore(json.loads((args.resume.parent/f"checkpoint-{n:02d}.json").read_bytes()),config,binding)
            if old.updates!=n or (n==state.updates and old!=state):raise ValueError("Resume history mismatch")
            save(old)
    else:save(state)
    if args.run:
        samples=[r["sample"] for r in train]
        while state.updates<config.max_updates:
            state=advance(state,samples,config)
            if state.updates in plan["save_updates"]:save(state)
    selected=None
    if args.run:
        baseline=saved[0]["validation"]["loss"]
        choices=[s for s in saved[1:] if s["validation"]["changed_integer_scores"] and s["validation"]["loss"]<baseline-1e-12]
        selected=min(choices,key=lambda s:s["validation"]["loss"])["update"] if choices else saved[0]["update"]
    if runtime!={n:digest(ROOT/n) for n in runtime}:raise ValueError("Runtime changed during pilot")
    report=dict(schema="rakuyou-tempo-pilot-run-v1",mode="run" if args.run else "dry-run",real_data_updates=state.updates,
        updates_performed_this_invocation=state.updates-started_at,
        quality_measured=args.run,selected_update=selected,deployed=False,provisional_input=True,
        backup_manifest_sha256=digest(args.backup),backup_kind="local same-volume copies",runtime_sha256=runtime,
        binding=binding,config=asdict(config),saved=saved,search_performed=False,
        tool_sha256=digest(Path(__file__)),probe_sha256=digest(args.probe))
    with (args.output/"report.json").open("x") as stream:
        json.dump(report,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({k:report[k] for k in ("mode","real_data_updates","quality_measured","selected_update","deployed")},indent=2))


if __name__=="__main__":main()
