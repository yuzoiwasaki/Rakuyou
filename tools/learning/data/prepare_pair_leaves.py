#!/usr/bin/env python3
"""Audited expanded teachers to frozen leaves and zero checkpoint; no learning."""

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
from tools.learning.data.pair_teacher_generation import load_binding, PREP
from tools.learning.data.prepare_refreshed_pilot import frozen_record
from tools.learning.gold_silver.gold_silver_pair_pilot import PairProbe, CONFIG, FEATURE, PROBE
from tools.learning.core.king_safety_updater import initial, checkpoint, restore
from tools.learning.core.learning_backup import verify_backup, create_backup, safe_path
from tools.learning.tempo.run_tempo_search import write_report


def load_generation(path):
    path=Path(path).resolve();r=json.loads(path.read_bytes());a=json.loads((path.parent/'audit-v1.json').read_bytes())
    if a['generation_report_sha256']!=digest(path) or not a['teacher_provenance_verified']:raise ValueError('Teacher audit mismatch')
    if not r['teacher_generation_complete'] or r['errors'] or r['real_data_updates'] or r['deployed']:raise ValueError('Incomplete generation')
    plan_path=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['plan_sha256'])
    plan,m,pending,entries,_,probe=load_binding(PREP,plan_path,True)
    required=dict(m['required_sha256']);parts={}
    for e in r['input_copies']:
        for p in (ROOT/e['source'],path.parent/e['copy']):
            if digest(p)!=e['sha256']:raise ValueError('Generation input copy changed')
            required[p.relative_to(ROOT).as_posix()]=e['sha256']
    for split,e in r['files'].items():
        p=safe_path(path.parent,e['path'])
        if digest(p)!=e['sha256']:raise ValueError('Teacher JSONL changed')
        rows=[json.loads(line) for line in p.read_text().splitlines()]
        if rows!=[x for x in r['records'] if x['split']==split]:raise ValueError('JSONL/report mismatch')
        parts[split]=[row for row in rows if row['teacher_status']=='accepted']
        required[p.relative_to(ROOT).as_posix()]=e['sha256']
        for row in rows:required[row['source']['path']]=row['source']['sha256']
    for e in entries:required[e['source']]=e['sha256']
    for p in (path,path.parent/'audit-v1.json',PROBE,Path(__file__),ROOT/'tools/learning/data/pair_teacher_generation.py',ROOT/'tools/learning/data/prepare_refreshed_pilot.py',ROOT/'tools/learning/checks/check_qsearch_leaves.py',ROOT/'tools/learning/core/king_safety_updater.py',ROOT/'tools/learning/core/king_safety_objective.py'):
        required[p.relative_to(ROOT).as_posix()]=digest(p)
    for n,sha in required.items():
        if digest(ROOT/n)!=sha:raise ValueError('Bound source changed: '+n)
    return r,parts,required,probe


def run(generation,output):
    generation=Path(generation).resolve();g,parts,required,binary=load_generation(generation)
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    with (generation.parent/'frozen-leaf-preparation-attempt-v1.json').open('x') as f:json.dump(dict(output=output.relative_to(ROOT).as_posix(),generation_sha256=digest(generation)),f)
    report=dict(schema='rakuyou-pair-expanded-leaf-preparation-v1',generation_sha256=digest(generation),
        audit_sha256=digest(generation.parent/'audit-v1.json'),feature=FEATURE,config=asdict(CONFIG),
        frames={},summary={},qsearch_calls=0,errors=[],updates=0,quality_measured=False,selected_update=None,
        deployed=False,training_ready=False,test_roots=0,closed=False)
    report_path=output/'report.json';write_report(report_path,report)
    q=Probe(binary,ROOT/'bin/params.bin',qsearch_progress=ROOT/'bin/progress.bin');static=PairProbe();valid={}
    try:
        for split in ('train','validation'):
            frames=[];valid[split]=[]
            for row in parts[split]:
                frame={};reason=None;counts=None
                try:
                    report['qsearch_calls']+=1
                    frame=q.replay(row['moves_before']);record,reason=frozen_record(row,frame)
                    if record is not None:
                        replay=static.replay(row['moves_before']+frame['pv'])
                        if not replay.get('ok'):raise ValueError('Frozen PV illegal')
                        leaf=replay['positions'][-1]
                        if any(p['occurrences']>1 for p in replay['positions']):reason='repeated_game_history'
                        elif (leaf['sfen'],leaf['eval_on'],leaf['progress'],leaf['on_parts'])!=(frame['leaf_sfen'],frame['leaf_eval_full'],frame['leaf_progress'],frame['leaf_parts']):raise ValueError('Leaf/base mismatch')
                        elif leaf['on_parts']!=leaf['base_on_parts']:raise ValueError('Zero residual mismatch')
                        if reason is None:counts=leaf['pair_counts'];valid[split].append(dict(row=row,frame=frame,pair_counts=counts))
                except Exception as e:
                    reason='preparation_error';report['errors'].append(dict(id=row['id'],type=type(e).__name__,message=str(e)))
                frames.append(dict(id=row['id'],stratum=row['stratum'],qsearch=frame,excluded=reason,pair_counts=counts))
                report['frames'][split]=frames;write_report(report_path,report)
            cache=output/f'{split}.leaves.json'
            write_report(cache,dict(schema='rakuyou-refreshed-leaves-v1',split=split,generation_sha256=digest(generation),frames=frames,quality_measured=False,updates=0))
            required[cache.relative_to(ROOT).as_posix()]=digest(cache)
            report['summary'][split]=dict(requested=sum(r['split']==split for r in g['records']),teacher_accepted=len(parts[split]),
                leaf_accepted=len(valid[split]),excluded=dict(Counter(x['excluded'] for x in frames if x['excluded'])),
                strata=dict(Counter(x['row']['stratum'] for x in valid[split])),
                pair_presence=sum(any(x['pair_counts'].values()) for x in valid[split]),
                net_nonzero=sum(x['pair_counts']['black']!=x['pair_counts']['white'] for x in valid[split]))
    finally:q.close();static.close()
    overlap={key:sorted({x['frame'][key] for x in valid['train']}&{x['frame'][key] for x in valid['validation']}) for key in ('root_sfen','leaf_sfen')}
    report['split_overlap']=overlap
    if any(overlap.values()):report['errors'].append(dict(type='SplitOverlap',message='No replacement; overlapping leaves retained for review'))
    existing=verify_backup(ROOT/'results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1/backup/manifest.json')
    covered={n:s for n,s in required.items() if n in existing};missing={n:s for n,s in required.items() if n not in existing}
    verify_backup(ROOT/'results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1/backup/manifest.json',covered)
    create_backup(missing,output/'additional-backup');verify_backup(output/'additional-backup/manifest.json',missing)
    binding=dict(required_sha256=required,generation_sha256=digest(generation),audit_sha256=report['audit_sha256'])
    state=initial(CONFIG);payload=checkpoint(state,CONFIG,binding);write_report(output/'checkpoint-00.json',payload)
    if restore(json.loads((output/'checkpoint-00.json').read_bytes()),CONFIG,binding)!=state:raise ValueError('Zero checkpoint restore mismatch')
    write_report(output/'pair-zero-delta.json',dict(feature=FEATURE,delta_cp=[0,0],raw=[0,0],scale=65536,
        base_sha256=g['runtime_sha256']['bin/params.bin'],operational_loadable=False))
    for n,s in required.items():
        if digest(ROOT/n)!=s:raise ValueError('Input/runtime changed after preparation: '+n)
    report.update(binding=binding,zero_checkpoint_sha256=digest(output/'checkpoint-00.json'),zero_checkpoint_restored=True,
        backup_sha256=digest(output/'additional-backup/manifest.json'),closed=True)
    write_report(report_path,report)
    print(json.dumps(dict(summary=report['summary'],errors=report['errors'],split_overlap=overlap),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('generation',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.generation,a.output)
