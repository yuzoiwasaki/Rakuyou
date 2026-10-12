#!/usr/bin/env python3
"""Fixed 36/18 teacher pilot; default update0, no search or deployment."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from dataclasses import asdict
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, digest
from tools.learning.data.prepare_refreshed_pilot import load_refreshed, frozen_record
from tools.learning.tempo.tempo_pilot import assert_disjoint, advance, verify_candidate
from tools.learning.core.tempo_updater import Config, initial, checkpoint, restore
from tools.learning.core.tempo_export import export_candidate
from tools.learning.core.learning_backup import create_backup, verify_backup
from tools.learning.tempo.run_tempo_search import write_report

DEFAULT_PLAN=ROOT/'docs/experiments/configs/refreshed-tempo-pilot-v1.json'
PREPARATION_SHA='da5310a8b195632f39c36101d853b0992f9ad447d1a7ca07e5752251de8e04a3'


def validate_plan(plan,reference,execute):
    expected={**reference,'real_data_training_enabled':execute}
    if (plan!=expected or plan['optimizer']!=asdict(Config()) or
        plan['deployment_enabled'] is not False or plan['outcome_loss_enabled'] is not False or
        plan['train_roots']!=36 or plan['validation_roots']!=18 or plan['test_roots']!=0):
        raise ValueError('Expected fixed 36/18 plan with training flag matching requested mode')


def cached_records(path,split,rows,expected_sha):
    if digest(path)!=expected_sha:raise ValueError('Frozen cache SHA mismatch')
    data=json.loads(Path(path).read_bytes())
    if (data['schema']!='rakuyou-refreshed-leaves-v1' or data['split']!=split or
        data['updates']!=0 or data['quality_measured'] is not False):raise ValueError('Cache metadata mismatch')
    lookup={r['id']:r for r in rows};records=[]
    if len(data['frames'])!=len(rows) or {x['id'] for x in data['frames']}!=set(lookup):raise ValueError('Cache membership mismatch')
    for x in data['frames']:
        if x['excluded'] is not None:raise ValueError('Fixed pilot requires every prepared root')
        r,reason=frozen_record(lookup[x['id']],x['qsearch'])
        if reason is not None:raise ValueError('Invalid cached leaf')
        records.append(r)
    return records


def choose(saved):
    baseline=saved[0]['validation']['loss']
    eligible=[x for x in saved[1:] if x['validation']['changed_integer_scores'] and x['validation']['loss']<baseline-1e-12]
    return min(eligible,key=lambda x:(x['validation']['loss'],x['update']))['update'] if eligible else 0


def learn(samples,config,save,on_update=None):
    state=initial(config);save(state)
    while state.updates<config.max_updates:
        state=advance(state,samples,config)
        if on_update is not None:on_update(state)
        if state.updates in (5,10,20):save(state)
    return state


def run(preparation,generation,audit,plan_path,output,*,execute=False):
    preparation=Path(preparation).resolve();root=preparation.parent
    if digest(preparation)!=PREPARATION_SHA:raise ValueError('Preparation report changed')
    reference=json.loads(DEFAULT_PLAN.read_bytes());plan=json.loads(Path(plan_path).read_bytes())
    validate_plan(plan,reference,execute)
    if plan['preparation_report_sha256']!=PREPARATION_SHA:raise ValueError('Plan preparation binding mismatch')
    prep=json.loads(preparation.read_bytes())
    if (plan['train_sha256']!=prep['binding']['train_sha256'] or
        plan['val_sha256']!=prep['binding']['val_sha256'] or plan['optimizer']!=prep['config'] or
        plan['generation_sha256']!=prep['generation_sha256'] or plan['audit_sha256']!=prep['audit_sha256']):
        raise ValueError('Plan differs from fixed preparation bindings')
    gen,parts,required,probe=load_refreshed(generation,audit)
    if (digest(generation)!=plan['generation_sha256'] or digest(audit)!=plan['audit_sha256'] or
        gen['runtime_sha256']['bin/params.bin']!=plan['base_params_sha256']):raise ValueError('Teacher/base plan binding mismatch')
    train=cached_records(root/'train.leaves.json','train',parts['train'],plan['train_sha256'])
    val=cached_records(root/'validation.leaves.json','validation',parts['validation'],plan['val_sha256'])
    assert_disjoint(train,val)
    backup=root/'backup/manifest.json'
    if digest(backup)!=plan['base_backup_manifest_sha256']:raise ValueError('Base backup changed')
    existing=verify_backup(backup)
    for path in (preparation,root/'train.leaves.json',root/'validation.leaves.json',Path(plan_path).resolve(),DEFAULT_PLAN,Path(__file__)):
        required[path.relative_to(ROOT).as_posix()]=digest(path)
    # Include generation/loading dependencies as well as learning helpers.
    for name in ('learning/data/refresh_teachers.py','learning/tempo/prepare_tempo_search.py','analysis/analyze_positions.py','learning/tempo/run_tempo_search.py'):
        p=ROOT/'tools'/name;required[p.relative_to(ROOT).as_posix()]=digest(p)
    covered={n:sha for n,sha in required.items() if n in existing}
    verify_backup(backup,covered)
    missing={n:sha for n,sha in required.items() if n not in existing}
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    if execute:
        with (root/'learning-attempt-v1.json').open('x') as f:
            json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(plan_path)),f)
    create_backup(missing,output/'additional-backup')
    verify_backup(output/'additional-backup/manifest.json',missing)
    config=Config()
    binding=dict(input_kind='audited-refreshed-search-cp',preparation_sha256=PREPARATION_SHA,
                 generation_sha256=plan['generation_sha256'],audit_sha256=plan['audit_sha256'],
                 plan_sha256=digest(plan_path),base_sha256=plan['base_params_sha256'],
                 train_sha256=plan['train_sha256'],val_sha256=plan['val_sha256'],
                 tool_sha256={n:sha for n,sha in required.items() if n.startswith('tools/')})
    report=dict(schema='rakuyou-refreshed-tempo-pilot-run-v1',mode='run' if execute else 'dry-run',
                binding=binding,config=asdict(config),runtime_sha256=gen['runtime_sha256'],
                real_data_updates=0,quality_measured=execute,selected_update=None,deployed=False,searches=0,
                saved=[],errors=[],closed=False,base_backup_sha256=digest(backup),
                additional_backup_sha256=digest(output/'additional-backup/manifest.json'))
    report_path=output/'report.json';write_report(report_path,report)
    def save(state):
        report['real_data_updates']=state.updates
        label=f'{state.updates:02d}';candidate=output/f'params-average-{label}.bin'
        exported=export_candidate(ROOT/'bin/params.bin',candidate,state.average(),plan['base_params_sha256'],probe)
        checked=verify_candidate(candidate,train+val,probe)
        validation=verify_candidate(candidate,val,probe,True,state.average(),config.l2) if execute else None
        payload=checkpoint(state,config,binding)
        path=output/f'checkpoint-{label}.json'
        with path.open('x') as f:json.dump(payload,f,sort_keys=True,indent=2);f.write('\n')
        if restore(json.loads(path.read_bytes()),config,binding)!=state:raise ValueError('Checkpoint reread mismatch')
        report['saved'].append(dict(update=state.updates,delta=list(state.average()),export=exported,
                                   verification=checked,validation=validation,checkpoint_sha256=digest(path)))
        write_report(report_path,report)
    def progress(state):
        report['real_data_updates']=state.updates;write_report(report_path,report)
    try:
        if execute:
            learn([r['sample'] for r in train],config,save,progress)
            report['selected_update']=choose(report['saved'])
        else:
            save(initial(config))
            if report['saved'][0]['export']['candidate_sha256']!=plan['base_params_sha256'] or report['saved'][0]['verification']['changed_integer_scores']:
                raise ValueError('Dry-run zero-delta mismatch')
        load_refreshed(generation,audit);verify_backup(backup,covered)
        verify_backup(output/'additional-backup/manifest.json',missing)
        if digest(preparation)!=PREPARATION_SHA or digest(plan_path)!=binding['plan_sha256']:raise ValueError('Input changed during execution')
        report['closed']=True
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error)));report['closed']=True
        raise
    finally:write_report(report_path,report)
    print(json.dumps({k:report[k] for k in ('mode','real_data_updates','quality_measured','selected_update','deployed')},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('preparation',type=Path);p.add_argument('generation',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--plan',type=Path,default=DEFAULT_PLAN);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--run',action='store_true');a=p.parse_args()
    run(a.preparation,a.generation,a.audit,a.plan,a.output,execute=a.run)
