#!/usr/bin/env python3
"""Bind refreshed teachers, prepare baseline leaves, dry-run at update zero only."""

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
from tools.learning.core.learning_backup import safe_path, create_backup, verify_backup
from tools.learning.data.refresh_teachers import load_binding
from tools.learning.checks.check_qsearch_leaves import eligibility
from tools.learning.checks.check_tempo_rounding import score_from_parts
from tools.learning.core.tempo_objective import FrozenLeaf
from tools.learning.core.tempo_updater import Config, initial, checkpoint, restore
from tools.learning.core.tempo_export import export_candidate
from tools.learning.tempo.tempo_pilot import assert_disjoint, verify_candidate

GENERATION_SHA='5b35823223c099a4233c4d4e9c99b11876fd291d14a92b9caa945c3941eb97cf'
AUDIT_SHA='de27d343a78ef62a0571b12410c14567b39e461a18191f38cc546be539d4cdd4'


def validate_teacher(row,split):
    if (row.get('schema')!='rakuyou-refreshed-teacher-v1' or row.get('split')!=split or
        row.get('teacher_status')!='accepted' or type(row.get('teacher_cp')) is not int or
        abs(row['teacher_cp'])>=31000 or row.get('outcome_loss_enabled') is not False or
        row.get('perspective')!='root-side-to-move' or row.get('excluded') is not None):
        raise ValueError('Expected accepted, root-perspective cp teacher')
    if row['teacher_cp']!=int(row['analysis']['candidates'][0]['score']):
        raise ValueError('Fresh teacher/analysis cp mismatch')
    # Existing pilot helpers expect run at top level; preserve original record otherwise.
    return {**row,'run':row['source']['run']}


def load_refreshed(report_path,audit_path):
    report_path=Path(report_path).resolve();audit_path=Path(audit_path).resolve()
    if digest(report_path)!=GENERATION_SHA or digest(audit_path)!=AUDIT_SHA:
        raise ValueError('Generation/audit SHA mismatch')
    r=json.loads(report_path.read_bytes());a=json.loads(audit_path.read_bytes())
    if (a['generation_report_sha256']!=GENERATION_SHA or not a['teacher_provenance_verified'] or
        a['accepted']!=54 or r['generated_teachers']!=54 or r['errors'] or r['real_data_updates']!=0):
        raise ValueError('Expected fully audited, untrained generation')
    prep=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['preparation_sha256'])
    plan=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['plan_sha256'])
    _,_,_,_,_,probe_path=load_binding(prep,plan,True)
    required={n:sha for n,sha in r['runtime_sha256'].items()}
    for e in r['input_copies']:
        required[e['source']]=e['sha256']
        copy=report_path.parent/e['copy']
        if digest(copy)!=e['sha256']:raise ValueError('Generation input copy changed')
    for e in r['runtime_files']:
        required[e['source']]=e['sha256']
    parts={}
    for split,e in r['files'].items():
        path=safe_path(report_path.parent,e['path'])
        if digest(path)!=e['sha256']:raise ValueError('Teacher JSONL changed')
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if rows!=[x for x in r['records'] if x['split']==split]:raise ValueError('JSONL/report mismatch')
        parts[split]=[validate_teacher(row,split) for row in rows]
        required[path.relative_to(ROOT).as_posix()]=e['sha256']
        for row in rows:required[row['source']['path']]=row['source']['sha256']
    if set(parts)!= {'train','validation'} or len(parts['train'])!=36 or len(parts['validation'])!=18:
        raise ValueError('Teacher split scope mismatch')
    for split,rows in parts.items():
        if len({x['id'] for x in rows})!=len(rows):raise ValueError('Duplicate teacher ID')
    if {x['run'] for x in parts['train']}&{x['run'] for x in parts['validation']}:raise ValueError('Split run overlap')
    for path in (report_path,audit_path,probe_path):required[path.relative_to(ROOT).as_posix()]=digest(path)
    for name in ('learning/data/prepare_refreshed_pilot.py','learning/data/prepare_learning_data.py','learning/core/tempo_objective.py','learning/core/tempo_updater.py',
                 'learning/core/tempo_export.py','learning/tempo/tempo_pilot.py','learning/checks/check_qsearch_leaves.py','learning/checks/check_tempo_rounding.py','learning/core/learning_backup.py'):
        p=ROOT/'tools'/name;required[p.relative_to(ROOT).as_posix()]=digest(p)
    for n,sha in required.items():
        if digest(safe_path(ROOT,n))!=sha:raise ValueError('Required source changed: '+n)
    return r,parts,required,probe_path


def frozen_record(row,frame):
    reason=eligibility(frame)
    if frame.get('ok') and (frame['root_sfen']!=row['sfen'] or frame['root_side']!=row['side_to_move']):
        raise ValueError('Qsearch root identity mismatch')
    if reason is not None:return None,reason
    if score_from_parts(frame['leaf_parts'],frame['leaf_side'],frame['leaf_progress'])!=frame['leaf_eval_full']:
        raise ValueError('Integer leaf reconstruction mismatch')
    sample=FrozenLeaf(frame['leaf_eval_full'],row['teacher_cp'],frame['leaf_progress'],frame['root_side'],frame['leaf_side'])
    sample.factors()  # Validate finite progress, parity and numeric fields; no loss/gradient.
    return dict(row=row,frame=frame,sample=sample),None


def run(report_path,audit_path,output):
    generation,parts,required,probe_path=load_refreshed(report_path,audit_path)
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in ignored results')
    output.mkdir(parents=True,exist_ok=False)
    # One leaf-preparation attempt; no automatic replacement or rerun under another output.
    with (Path(report_path).resolve().parent/'frozen-leaf-preparation-attempt-v1.json').open('x') as f:
        json.dump(dict(output=str(output.relative_to(ROOT)),generation_sha256=GENERATION_SHA),f)
    frames={};records={}
    q=Probe(probe_path,ROOT/'bin/params.bin',qsearch_progress=ROOT/'bin/progress.bin')
    static=Probe(probe_path,ROOT/'bin/params.bin',details=True)
    try:
        for split in ('train','validation'):
            frames[split]=[];records[split]=[]
            for row in parts[split]:
                frame=q.replay(row['moves_before']);record,reason=frozen_record(row,frame)
                if record is not None:
                    replay=static.replay(row['moves_before']+frame['pv'])
                    if not replay.get('ok'):raise ValueError('Frozen leaf PV illegal')
                    leaf=replay['positions'][-1]
                    if any(p['occurrences']>1 for p in replay['positions']):
                        record=None;reason='repeated_game_history'
                    elif (leaf['sfen']!=frame['leaf_sfen'] or leaf['eval_on']!=frame['leaf_eval_full'] or
                          leaf['progress']!=frame['leaf_progress'] or leaf['on_parts']!=frame['leaf_parts']):
                        raise ValueError('Frozen leaf independent static mismatch')
                if record is not None:records[split].append(record)
                frames[split].append(dict(id=row['id'],qsearch=frame,excluded=reason))
            path=output/f'{split}.leaves.json'
            with path.open('x') as f:
                json.dump(dict(schema='rakuyou-refreshed-leaves-v1',split=split,generation_sha256=GENERATION_SHA,
                               frames=frames[split],quality_measured=False,updates=0),f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
    finally:q.close();static.close()
    if not records['train'] or not records['validation']:raise ValueError('No usable frozen samples')
    assert_disjoint(records['train'],records['validation'])
    for split in frames:
        path=output/f'{split}.leaves.json';required[path.relative_to(ROOT).as_posix()]=digest(path)
    create_backup(required,output/'backup');verify_backup(output/'backup/manifest.json',required)
    config=Config();state=initial(config)
    binding=dict(input_kind='audited-refreshed-search-cp',generation_sha256=GENERATION_SHA,audit_sha256=AUDIT_SHA,
                 base_sha256=generation['runtime_sha256']['bin/params.bin'],
                 train_sha256=digest(output/'train.leaves.json'),val_sha256=digest(output/'validation.leaves.json'),
                 objective_sha256=digest(ROOT/'tools/learning/core/tempo_objective.py'),updater_sha256=digest(ROOT/'tools/learning/core/tempo_updater.py'))
    payload=checkpoint(state,config,binding)
    with (output/'checkpoint-00.json').open('x') as f:json.dump(payload,f,sort_keys=True,indent=2);f.write('\n')
    restored=restore(json.loads((output/'checkpoint-00.json').read_bytes()),config,binding)
    if restored!=state:raise ValueError('Initial checkpoint reread mismatch')
    exported=export_candidate(ROOT/'bin/params.bin',output/'params-zero-delta.bin',state.average(),binding['base_sha256'],probe_path)
    checked=verify_candidate(output/'params-zero-delta.bin',records['train']+records['validation'],probe_path)
    if checked['changed_integer_scores'] or checked['loss'] is not None or exported['candidate_sha256']!=binding['base_sha256']:
        raise ValueError('Zero-update candidate/evaluation mismatch')
    load_refreshed(report_path,audit_path);verify_backup(output/'backup/manifest.json',required)
    summary={s:dict(requested=len(parts[s]),accepted=len(records[s]),
                   excluded=dict(Counter(x['excluded'] for x in frames[s] if x['excluded'] is not None)),
                   strata=dict(Counter(x['row']['stratum'] for x in records[s])),
                   parity=dict(Counter('even' if len(x['frame']['pv'])%2==0 else 'odd' for x in records[s]))) for s in frames}
    result=dict(schema='rakuyou-refreshed-pilot-preparation-v1',generation_sha256=GENERATION_SHA,audit_sha256=AUDIT_SHA,
                qsearch_calls=54,summary=summary,config=asdict(config),binding=binding,
                dry_run=dict(searches=0,updates=0,quality_measured=False,selected_update=None,
                             checkpoint_restored=True,candidate_export=exported,candidate_verification=checked),
                backup_manifest_sha256=digest(output/'backup/manifest.json'),runtime_sha256=generation['runtime_sha256'],
                training_enabled=False,deployment_enabled=False,training_ready=False,test_roots_selected=0,
                tool_sha256=digest(Path(__file__)),probe_sha256=digest(probe_path))
    with (output/'report.json').open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(result['summary'],indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('generation',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.generation,a.audit,a.output)
