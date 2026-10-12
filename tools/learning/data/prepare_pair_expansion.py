#!/usr/bin/env python3
"""Select 144/36 pending roots; static replay only, no teachers, search or updates."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.prepare_teacher_refresh import select_rows, pending_record
from tools.learning.data.validate_learning_input import load_input
from tools.learning.gold_silver.gold_silver_pair_pilot import PairProbe, CONFIG, FEATURE, PROBE
from tools.learning.tempo.run_tempo_search import write_report

BASE=ROOT/'results/learning-pilot/2026-10-11-preparation-v2/manifest.json'
REFERENCE=ROOT/'docs/experiments/configs/teacher-refresh-v1.json'
HISTORY=[ROOT/'results/learning-pilot/2026-10-11-input-validation-v1/validation-leaves-v1.json',
         ROOT/'results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json']
PRIOR=ROOT/'results/learning-pilot/2026-10-12-gold-silver-pair-run-v1/report.json'


def used_validation_games(rows,history):
    lookup={r['id']:r for r in rows};used=set()
    for data in history:
        entries=data['frames'] if 'frames' in data else [r for r in data['records'] if r['split']=='validation']
        for entry in entries:
            if entry['id'] not in lookup:raise ValueError('Prior validation root outside audited pool')
            row=lookup[entry['id']];used.add((row['run'],row['game']))
    return used


def choose(parts,history):
    used=used_validation_games(parts['validation'],history)
    pool=[r for r in parts['validation'] if (r['run'],r['game']) not in used]
    selected=dict(train=select_rows(parts['train'],24,20261011,max_per_run=8),
                  validation=select_rows(pool,6,20261011,max_per_run=12))
    for key in ('run','sfen','prefix24'):
        if {r[key] for r in selected['train']}&{r[key] for r in selected['validation']}:
            raise ValueError('Split overlap: '+key)
    if any((r['run'],r['game']) in used for r in selected['validation']):raise ValueError('Reused validation game')
    return selected,used


def prepare(output):
    reference=json.loads(REFERENCE.read_bytes())
    if digest(BASE)!=reference['preparation_manifest_sha256']:raise ValueError('Original manifest changed')
    manifest,parts=load_input(BASE)
    prior=json.loads(PRIOR.read_bytes())
    if not prior['closed'] or prior['updates']!=20 or prior['errors']:raise ValueError('Prior experiment not closed')
    if prior['plan']['feature']!=FEATURE or prior['plan']['config']!=asdict(CONFIG):raise ValueError('Feature/training config changed')
    runtime={n:digest(ROOT/n) for n in reference['runtime_sha256']}
    if runtime!=reference['runtime_sha256'] or runtime!=manifest['runtime_sha256']:raise ValueError('Operational runtime changed')
    original_probe=ROOT/'results/learning-tools/learning-data-probe'
    if digest(original_probe)!=reference['probe_sha256'] or digest(PROBE)!=prior['plan']['probe_sha256']:raise ValueError('Probe changed')
    for p in HISTORY:
        if str(p.relative_to(ROOT)) in prior['binding']['required_sha256'] and digest(p)!=prior['binding']['required_sha256'][str(p.relative_to(ROOT))]:raise ValueError('History changed')
    # The old validation cache is also bound by its original preparation report.
    validation=json.loads(HISTORY[0].read_bytes())
    if validation['preparation_manifest_sha256']!=digest(BASE) or len(validation['frames'])!=64:raise ValueError('Old validation cache mismatch')
    selected,used=choose(parts,[json.loads(p.read_bytes()) for p in HISTORY])
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('Output must be new directory in results')
    rows={};coverage={};probe=Probe(original_probe,ROOT/'bin/params.bin',details=True);pairs=PairProbe()
    try:
        for split,chosen in selected.items():
            rows[split]=[];coverage[split]=[]
            for row in chosen:
                r=probe.replay(row['moves_before']);p=pairs.replay(row['moves_before'])
                if not r.get('ok') or not p.get('ok'):raise ValueError('Illegal selected root')
                root=r['positions'][-1];pair=p['positions'][-1]
                if root['sfen']!=row['sfen'] or root['huffman_hex']!=row['huffman_hex']:raise ValueError('Root identity mismatch')
                if any(x['occurrences']>1 for x in r['positions']):raise ValueError('Repeated root history')
                for key in ('sfen','eval_on','eval_off','progress','on_parts','off_parts'):
                    if root[key]!=pair[key]:raise ValueError('Zero residual/base mismatch: '+key)
                rows[split].append(pending_record(row))
                coverage[split].append(dict(id=row['id'],stratum=row['stratum'],pair_counts=pair['pair_counts'],progress=pair['progress']))
    finally:probe.close();pairs.close()
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(schema='rakuyou-pair-expansion-plan-v1',status='preparation-only',feature=FEATURE,training_config=asdict(CONFIG),
        initial_delta=[0,0],sign_constraints=None,selection=dict(seed=20261011,per_stratum=dict(train=24,validation=6),
            max_roots_per_game=1,max_roots_per_run=dict(train=8,validation=12),test_roots=0,
            ordering=reference['selection']['ordering'],validation_freshness='unused games within existing held-out runs'),
        search={**reference['search'],'max_searches':180},teacher=reference['teacher'],acceptance=reference['acceptance'],
        teacher_search_enabled=False,real_data_training_enabled=False,deployment_enabled=False,
        runtime_sha256=runtime,original_probe_sha256=digest(original_probe),pair_probe_sha256=digest(PROBE),
        max_position_cp_change=10,save_updates=[0,5,10,20],outcome_loss_enabled=False,
        note='Native root checks only; frozen leaves and current teachers not generated; old 36/18 runner unchanged')
    write_report(output/'plan.json',plan)
    files={};summary={}
    for split,chosen in rows.items():
        path=output/(split+'.pending.jsonl')
        with path.open('x') as f:
            for row in chosen:f.write(json.dumps(row,sort_keys=True)+'\n')
        files[split]=dict(path=path.name,sha256=digest(path),roots=len(chosen))
        original=selected[split];counts=Counter(r['run'] for r in original)
        summary[split]=dict(roots=len(chosen),games=len({(r['run'],r['game']) for r in original}),runs=len(counts),
            max_roots_per_run=max(counts.values()),strata=dict(Counter(r['stratum'] for r in original)),
            root_pair_presence=sum(any(x['pair_counts'].values()) for x in coverage[split]),
            root_net_nonzero=sum(x['pair_counts']['black']!=x['pair_counts']['white'] for x in coverage[split]))
    required={str(p.relative_to(ROOT)):digest(p) for p in [BASE,REFERENCE,PRIOR,*HISTORY,original_probe,PROBE,
        ROOT/'tools/learning/data/prepare_pair_expansion.py',ROOT/'tools/learning/data/prepare_teacher_refresh.py',ROOT/'tools/learning/data/validate_learning_input.py',
        ROOT/'tools/learning/gold_silver/gold_silver_pair_pilot.py',ROOT/'tools/learning/native/gold_silver_pair_probe.cc',output/'plan.json']}
    required.update(runtime)
    for split,entry in files.items():required[str((output/entry['path']).relative_to(ROOT))]=entry['sha256']
    if runtime!={n:digest(ROOT/n) for n in runtime}:raise ValueError('Runtime changed during preparation')
    report=dict(schema='rakuyou-pair-expansion-preparation-v1',plan_sha256=digest(output/'plan.json'),files=files,
        summary=summary,required_sha256=required,excluded_prior_validation_games=[list(x) for x in sorted(used)],
        root_coverage=coverage,searches_executed=0,real_data_updates=0,test_roots_selected=0,deployed=False,
        training_ready=False,teacher_generation_ready=False,old_runner_supports_expanded_counts=False,
        validation_new_games=True,validation_new_runs=False)
    write_report(output/'manifest.json',report)
    print(json.dumps(summary,indent=2));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    prepare(parser.parse_args().output)
