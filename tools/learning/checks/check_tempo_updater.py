#!/usr/bin/env python3
"""Synthetic-only 20-step updater/save/resume check. Never loads game teachers."""

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

from tools.learning.data.prepare_learning_data import ROOT, digest
from tools.learning.core.tempo_updater import Config, initial, sample_batch, step, checkpoint, restore, fingerprint


def population():
    return [(1.5+(i%7-3)*.02,-1.0+(i%5-2)*.02,.75+(i%3-1)*.02) for i in range(256)]


def loss(state,targets,config):
    return math.fsum(.5*math.fsum((d-t)**2 for d,t in zip(state.delta,target)) for target in targets)/len(targets) + .5*config.l2*math.fsum(d*d for d in state.delta)


def advance(state,targets,config):
    ids,sampled=sample_batch(state,len(targets),config)
    gradient=tuple(math.fsum(state.delta[j]-targets[i][j] for i in ids)/len(ids)+config.l2*state.delta[j] for j in range(3))
    return step(sampled,gradient,config)


def synthetic_check():
    config=Config();targets=population()
    binding=dict(input_kind="synthetic-quadratic",base_sha256=fingerprint("synthetic-zero-base"),
                 input_sha256=fingerprint(targets),objective="mean-half-squared-distance-plus-delta-L2-v1")
    state=initial(config);start=loss(state,targets,config)
    checkpoints={"0":checkpoint(state,config,binding)}
    max_move=0.0
    for i in range(1,21):
        prior=state;state=advance(state,targets,config)
        max_move=max(max_move,max(abs(a-b) for a,b in zip(state.delta,prior.delta)))
        if i in (5,10,20):checkpoints[str(i)]=checkpoint(state,config,binding)
    # Serialize through JSON, then reconstruct all float and RNG state.
    resumed=restore(json.loads(json.dumps(checkpoints["10"])),config,binding)
    for _ in range(10):resumed=advance(resumed,targets,config)
    if checkpoint(resumed,config,binding)!=checkpoints["20"]:
        raise ValueError("Resumed optimizer/sampler diverged")
    final=loss(state,targets,config)
    if not final<start or max_move>config.max_step_cp:
        raise ValueError("Synthetic convergence/bound check failed")
    try:
        advance(state,targets,config)
    except ValueError:
        limited=True
    else:
        raise ValueError("Update cap not enforced")
    return dict(synthetic_updates=state.updates,real_data_updates=0,config=asdict(config),
        initial_synthetic_loss=start,final_synthetic_loss=final,final_delta_cp=list(state.delta),
        averaged_delta_cp=list(state.average()),max_update_cp=max_move,
        resume_identical=True,update_cap_enforced=limited,checkpoints=checkpoints,
        training_ready=False,parameter_files_written=False,search_performed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    names=("bin/release","bin/params.bin","bin/progress.bin","bin/probability.bin",
           "bin/book.bin","books/shin-yonenaga-book-v1.txt")
    before={n:digest(ROOT/n) for n in names}
    result=synthetic_check()
    if before!={n:digest(ROOT/n) for n in names}:raise ValueError("Runtime changed")
    result.update(schema="rakuyou-synthetic-updater-check-v1",runtime_sha256=before,
                  tool_sha256=digest(Path(__file__)),updater_sha256=digest(ROOT/"tools/learning/core/tempo_updater.py"))
    with args.output.open("x") as stream:
        json.dump(result,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        stream.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("checkpoints","runtime_sha256")},indent=2))


if __name__=="__main__":main()
