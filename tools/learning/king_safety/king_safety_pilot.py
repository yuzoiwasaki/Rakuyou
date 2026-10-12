#!/usr/bin/env python3
"""Four king-neighbor residual features, one 20-update run, no search/deployment."""

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
from tools.learning.data.prepare_refreshed_pilot import load_refreshed
from tools.learning.tempo.refreshed_tempo_pilot import cached_records
from tools.learning.core.king_safety_objective import FrozenLeaf, objective, check_gradient, sigmoid, GAIN
from tools.learning.core.king_safety_updater import Config, initial, sample_batch, step, checkpoint, restore
from tools.learning.core.king_safety_export import export
from tools.learning.core.learning_backup import create_backup, verify_backup
from tools.learning.tempo.run_tempo_search import write_report

PROBE=ROOT/'results/king-safety-tools/king-safety-probe'
MAP=ROOT/'results/king-safety-tools/king-safety-map-v1.json'
FEATURES=['supported_gold','supported_silver','isolated_gold_or_silver','adjacent_control_deficit']
PREP=ROOT/'results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1'
GEN=ROOT/'results/learning-pilot/2026-10-11-teacher-refresh-run-v1'


def independent_columns(samples):
    columns=list(zip(*(s.factors() for s in samples)));basis=[];active=[]
    for index,column in enumerate(columns):
        v=list(column)
        for b in basis:
            dot=math.fsum(x*y for x,y in zip(v,b))
            v=[x-dot*y for x,y in zip(v,b)]
        norm=math.sqrt(math.fsum(x*x for x in v))
        if norm>1e-9:
            basis.append([x/norm for x in v]);active.append(index)
    return active


def prepare_records(parts,old_records,probe):
    result={}
    for split in ('train','validation'):
        result[split]=[]
        for old in old_records[split]:
            row,frame=old['row'],old['frame']
            replay=probe.replay(row['moves_before']+frame['pv'])
            if not replay.get('ok'):raise ValueError('Illegal frozen PV')
            leaf=replay['positions'][-1]
            if (leaf['sfen']!=frame['leaf_sfen'] or leaf['eval_on']!=frame['leaf_eval_full'] or
                leaf['progress']!=frame['leaf_progress'] or leaf['on_parts']!=frame['leaf_parts']):
                raise ValueError('New probe/base evaluation mismatch')
            counts=tuple(a-b for a,b in zip(leaf['safety_features']['black'],leaf['safety_features']['white']))
            sign=1 if frame['root_side']==frame['leaf_side'] else -1
            sample=FrozenLeaf(sign*leaf['eval_on'],row['teacher_cp'],leaf['progress'],row['side_to_move'],counts)
            result[split].append(dict(row=row,frame=frame,leaf=leaf,root=replay['positions'][len(row['moves_before'])],sample=sample))
    return result


def native_scores(candidate,records,raw_delta,measure_quality=False):
    native=Probe(PROBE,candidate,details=True);observations=[]
    try:
        for record in records:
            row,frame,base=record['row'],record['frame'],record['leaf']
            r=native.replay(row['moves_before']+frame['pv'])
            if not r.get('ok'):raise ValueError('Candidate replay illegal')
            leaf=r['positions'][-1]
            native_root=r['positions'][len(row['moves_before'])]
            for before,after in ((base,leaf),(record['root'],native_root)):
                if after['sfen']!=before['sfen'] or after['progress']!=before['progress'] or after['safety_features']!=before['safety_features']:
                    raise ValueError('Candidate position/feature identity mismatch')
                for key in ('kp','tempo'):
                    if after['on_parts'][key]!=before['on_parts'][key]:raise ValueError('Protected evaluation component changed')
                for lane in (1,3):
                    if after['on_parts']['others'][lane]!=before['on_parts']['others'][lane]:raise ValueError('Side-dependent component changed')
                counts=[a-b for a,b in zip(before['safety_features']['black'],before['safety_features']['white'])]
                for stage,lane in ((0,0),(1,2)):
                    expected=sum(counts[i]*raw_delta[2*i+stage] for i in range(4))
                    if after['on_parts']['others'][lane]-before['on_parts']['others'][lane]!=expected:
                        raise ValueError('Native feature/map packed-delta mismatch')
            sign=1 if frame['root_side']==frame['leaf_side'] else -1
            score=sign*leaf['eval_on'];baseline=record['sample'].base_root_cp
            predicted=record['sample'].predict([x/65536 for x in raw_delta])
            if abs(score-predicted)>2.000001:raise ValueError('Integer rounding differs from smooth model')
            observation=dict(id=row['id'],side=row['side_to_move'],stratum=row['stratum'],base_cp=baseline,candidate_cp=score,cp_change=score-baseline,
                             root_base_cp=record['root']['eval_on'],root_candidate_cp=native_root['eval_on'],
                             root_cp_change=native_root['eval_on']-record['root']['eval_on'])
            if measure_quality:
                observation.update(loss_base=(sigmoid(GAIN*baseline)-sigmoid(GAIN*row['teacher_cp']))**2,
                                   loss_candidate=(sigmoid(GAIN*score)-sigmoid(GAIN*row['teacher_cp']))**2)
            observations.append(observation)
    finally:native.close()
    return observations


def stats(observations):
    return dict(positions=len(observations),changed=sum(x['cp_change']!=0 for x in observations),
                max_abs_cp_change=max(abs(x['cp_change']) for x in observations),
                max_abs_root_cp_change=max(abs(x['root_cp_change']) for x in observations),
                mean_loss=math.fsum(x['loss_candidate'] for x in observations)/len(observations) if 'loss_candidate' in observations[0] else None)


def run(output,execute):
    gen,parts,required,_=load_refreshed(GEN/'report.json',GEN/'audit-v2.json')
    prep=json.loads((PREP/'report.json').read_bytes());base_sha=gen['runtime_sha256']['bin/params.bin']
    old={s:cached_records(PREP/f'{s}.leaves.json',s,parts[s],prep['binding']['train_sha256' if s=='train' else 'val_sha256']) for s in parts}
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    if execute:
        marker=GEN/'king-safety-learning-attempt-v1.json'
        with marker.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT))),f)
    probe=Probe(PROBE,ROOT/'bin/params.bin',details=True)
    try:records=prepare_records(parts,old,probe)
    finally:probe.close()
    samples=[r['sample'] for r in records['train']];active=independent_columns(samples)
    if not active:raise ValueError('No identifiable training features')
    config=Config();layout=json.loads(MAP.read_bytes())
    coverage={s:[dict(id=r['row']['id'],run=r['row']['run'],features=r['leaf']['safety_features'],factors=list(r['sample'].factors())) for r in records[s]] for s in records}
    for name in ('learning/king_safety/king_safety_pilot.py','learning/native/king_safety_features.h','learning/native/learning_data_probe.cc','learning/core/king_safety_objective.py','learning/core/king_safety_updater.py','learning/core/king_safety_export.py'):
        p=ROOT/'tools'/name;required[p.relative_to(ROOT).as_posix()]=digest(p)
    for p in (PROBE,MAP,PREP/'report.json',PREP/'train.leaves.json',PREP/'validation.leaves.json'):
        required[p.relative_to(ROOT).as_posix()]=digest(p)
    plan=dict(schema='rakuyou-king-safety-plan-v1',features=FEATURES,coefficients='feature-major opening/end',
              base_sha256=base_sha,initial_delta=[0.0]*8,config=asdict(config),active_columns=active,
              generation_sha256=digest(GEN/'report.json'),audit_sha256=digest(GEN/'audit-v2.json'),
              train_sha256=digest(PREP/'train.leaves.json'),val_sha256=digest(PREP/'validation.leaves.json'),
              runtime_sha256=gen['runtime_sha256'],probe_sha256=digest(PROBE),map_sha256=digest(MAP),
              training_enabled=execute,deployment_enabled=False,outcome_loss_enabled=False,
              max_leaf_cp_change=10,max_updates=20,save_updates=[0,5,10,20],coverage=coverage)
    with (output/'plan.json').open('x') as f:json.dump(plan,f,sort_keys=True,indent=2);f.write('\n')
    required[(output/'plan.json').relative_to(ROOT).as_posix()]=digest(output/'plan.json')
    # Keep the old 57-file backup intact; only new inputs/dependencies are copied.
    existing=verify_backup(PREP/'backup/manifest.json');covered={n:sha for n,sha in required.items() if n in existing}
    verify_backup(PREP/'backup/manifest.json',covered)
    missing={n:sha for n,sha in required.items() if n not in existing}
    create_backup(missing,output/'additional-backup');verify_backup(output/'additional-backup/manifest.json',missing)
    binding=dict(plan_sha256=digest(output/'plan.json'),required_sha256=required)
    # Train-only numerical checks; no updates. Validator results are retained.
    gradients=[check_gradient(samples,tuple([0.0]*8)),check_gradient(samples,tuple([.01,-.01]*4))]
    manual=export(ROOT/'bin/params.bin',output/'params-perturbation.bin',[.025,-.025]*4,base_sha,layout)
    rounding=native_scores(output/'params-perturbation.bin',records['train']+records['validation'],manual['raw_delta'])
    report=dict(schema='rakuyou-king-safety-pilot-v1',plan=plan,binding=binding,gradients=gradients,
                numerical_perturbation_max_cp=max(abs(x['cp_change']) for x in rounding),saved=[],updates=0,
                selected_update=None,deployed=False,searches=0,test_roots=0,errors=[],closed=False,
                additional_backup_sha256=digest(output/'additional-backup/manifest.json'))
    path=output/'report.json';write_report(path,report)
    state=initial(config)
    def save(state):
        delta=state.average();n=state.updates
        cand=output/f'params-average-{n:02d}.bin'
        exported=export(ROOT/'bin/params.bin',cand,delta,base_sha,layout)
        obs={s:native_scores(cand,records[s],exported['raw_delta'],execute) for s in records}
        if n==0 and (exported['candidate_sha256']!=base_sha or any(x['cp_change'] for rows in obs.values() for x in rows)):
            raise ValueError('Zero-delta export/evaluation mismatch')
        val=stats(obs['validation'])
        total_limit=max(max(abs(x['cp_change']),abs(x['root_cp_change'])) for rows in obs.values() for x in rows)<=10
        val['loss_plus_l2']=val['mean_loss']+.5*config.l2*math.fsum(x*x for x in delta) if execute else None
        payload=checkpoint(state,config,binding)
        cp=output/f'checkpoint-{n:02d}.json'
        with cp.open('x') as f:json.dump(payload,f,sort_keys=True,indent=2);f.write('\n')
        if restore(json.loads(cp.read_bytes()),config,binding)!=state:raise ValueError('State restore mismatch')
        report['saved'].append(dict(update=n,delta=list(delta),export=exported,observations=obs,
                                   within_total_limit=total_limit,validation=val,checkpoint_sha256=digest(cp)))
        write_report(path,report)
    try:
        save(state)
        if execute:
            while state.updates<20:
                indices,sampled=sample_batch(state,len(samples),config)
                _,g=objective([samples[i] for i in indices],state.delta,config.l2)
                state=step(sampled,tuple(x if i in active else 0.0 for i,x in enumerate(g)),config)
                report['updates']=state.updates;write_report(path,report)
                if state.updates in (5,10,20):save(state)
            baseline=report['saved'][0]['validation']['loss_plus_l2']
            choices=[s for s in report['saved'][1:] if s['within_total_limit'] and s['validation']['changed'] and s['validation']['loss_plus_l2']<baseline-1e-12]
            report['selected_update']=min(choices,key=lambda s:(s['validation']['loss_plus_l2'],s['update']))['update'] if choices else 0
        verify_backup(PREP/'backup/manifest.json',covered);verify_backup(output/'additional-backup/manifest.json',missing)
        for n,sha in gen['runtime_sha256'].items():
            if digest(ROOT/n)!=sha:raise ValueError('Operational runtime changed')
        report['closed']=True
    except Exception as e:
        report['errors'].append(dict(type=type(e).__name__,message=str(e)));report['closed']=True
        raise
    finally:write_report(path,report)
    print(json.dumps(dict(updates=report['updates'],active=active,selected=report['selected_update'],
                          validation=[s['validation'] for s in report['saved']]),indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--run',action='store_true')
    a=p.parse_args();run(a.output,a.run)
