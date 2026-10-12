#!/usr/bin/env python3
"""One 20-update run on audited143/35 leaves; existing pair objective unchanged."""
import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path
from prepare_learning_data import ROOT,digest
from gold_silver_pair_pilot import PairProbe,CONFIG,FEATURE,PROBE,native_scores
from king_safety_objective import FrozenLeaf,objective,check_gradient
from king_safety_updater import initial,sample_batch,step,checkpoint,restore
from king_safety_pilot import stats,independent_columns
from prepare_pair_leaves import load_generation
from learning_backup import verify_backup,create_backup
from run_tempo_search import write_report

PREP=ROOT/'results/learning-pilot/2026-10-12-pair-leaves-v1'
GEN=ROOT/'results/learning-pilot/2026-10-12-pair-teacher-run-v1'
BACKUPS=[ROOT/'results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1/backup/manifest.json',PREP/'additional-backup/manifest.json']
LEAF_SHA='6e5216775697f1bbeaa6bd5c3e37e105378148f34fb04239aa6e313aa484dfed'
AUDIT_SHA='747229695ece4961f079dc1bbab30cda86cb52fb6b9ddd5dc4875dc5d7029a73'


def existing_backups(required):
    known={}
    for path in BACKUPS:
        files=verify_backup(path)
        verify_backup(path,{n:s for n,s in required.items() if n in files})
        known.update(files)
    return known


def load_records():
    if digest(PREP/'report.json')!=LEAF_SHA or digest(PREP/'audit-v1.json')!=AUDIT_SHA:raise ValueError('Leaf preparation/audit SHA mismatch')
    prep=json.loads((PREP/'report.json').read_bytes());audit=json.loads((PREP/'audit-v1.json').read_bytes())
    if not audit['accepted'] or audit['report_sha256']!=LEAF_SHA or prep['errors'] or not prep['closed'] or prep['updates']:raise ValueError('Expected closed untrained audited leaves')
    gen,parts,required,_=load_generation(GEN/'report.json')
    if prep['feature']!=FEATURE or prep['config']!=asdict(CONFIG):raise ValueError('Feature/config changed')
    for n,s in prep['binding']['required_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Bound preparation input changed')
        required[n]=s
    records={};probe=PairProbe()
    try:
        for split,rows in parts.items():
            path=PREP/f'{split}.leaves.json';cache=json.loads(path.read_bytes())
            if cache['frames']!=prep['frames'][split]:raise ValueError('Saved frame/report mismatch')
            frames={f['id']:f for f in cache['frames']}
            if len(frames)!=len(rows) or set(frames)!={r['id'] for r in rows}:raise ValueError('Teacher/leaf membership mismatch')
            records[split]=[]
            for row in rows:
                entry=frames[row['id']];frame=entry['qsearch']
                if entry['excluded'] is not None:raise ValueError('Unexpected excluded leaf')
                r=probe.replay(row['moves_before']+frame['pv'])
                if not r.get('ok'):raise ValueError('Illegal frozen PV')
                leaf=r['positions'][-1]
                if (leaf['sfen'],leaf['eval_on'],leaf['progress'],leaf['on_parts'])!=(frame['leaf_sfen'],frame['leaf_eval_full'],frame['leaf_progress'],frame['leaf_parts']):raise ValueError('Baseline/cache mismatch')
                if leaf['pair_counts']!=entry['pair_counts']:raise ValueError('Pair count mismatch')
                net=leaf['pair_counts']['black']-leaf['pair_counts']['white']
                sign=1 if frame['root_side']==frame['leaf_side'] else -1
                sample=FrozenLeaf(sign*leaf['eval_on'],row['teacher_cp'],leaf['progress'],row['side_to_move'],(net,0,0,0))
                records[split].append(dict(row=row,frame=frame,leaf=leaf,root=r['positions'][len(row['moves_before'])],sample=sample))
        if len(records['train'])!=143 or len(records['validation'])!=35:raise ValueError('Expected143/35, no refill')
    finally:probe.close()
    for path in (PREP/'report.json',PREP/'audit-v1.json'):
        required[path.relative_to(ROOT).as_posix()]=digest(path)
    return gen,records,required

def run(output,execute=False):
    gen,records,required=load_records();samples=[r['sample'] for r in records['train']]
    if independent_columns(samples)!=[0,1]:raise ValueError('Both stage coefficients must be identifiable')
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(schema='rakuyou-mutual-pair-plan-v1',feature=FEATURE,unit='cp per pair; each gold/silver pair counted once',
        interpolation='(1-progress)*opening + progress*end; signed black-minus-white count; no tempo half factor',
        active_slots=[0,1],unused_slots=[2,3,4,5,6,7],initial_delta=[0,0],sign_constraints=None,config=asdict(CONFIG),
        l2_rationale=dict(train_only_initial_gradient=list(objective(samples,(0.0,)*8,0)[1][:2]),
            regularization_gradient_at_coefficient_cap=CONFIG.l2*CONFIG.delta_limit_cp,
            chosen_before_quality_measurement=True),preparation_sha256=LEAF_SHA,preparation_audit_sha256=AUDIT_SHA,
        runtime_sha256=gen['runtime_sha256'],probe_sha256=digest(PROBE),training_enabled=execute,
        deployment_enabled=False,outcome_loss_enabled=False,max_position_cp_change=10,save_updates=[0,5,10,20])
    write_report(output/'plan.json',plan)
    dependencies=['expanded_pair_pilot.py','prepare_pair_leaves.py','pair_teacher_generation.py','gold_silver_pair_pilot.py','gold_silver_pair_probe.cc','learning_data_probe.cc','king_safety_objective.py',
        'king_safety_updater.py','king_safety_pilot.py','king_safety_export.py','king_safety_features.h',
        'prepare_learning_data.py','prepare_refreshed_pilot.py','refreshed_tempo_pilot.py','learning_backup.py','run_tempo_search.py']
    for p in [ROOT/'tools'/n for n in dependencies]+[ROOT/'Makefile',ROOT/'test/test_gold_silver_pair_learning.py',ROOT/'test/test_king_safety_learning.py',PROBE,PREP/'audit-v1.json',PREP/'report.json',PREP/'train.leaves.json',PREP/'validation.leaves.json',output/'plan.json']:
        required[p.relative_to(ROOT).as_posix()]=digest(p)
    existing=existing_backups(required);missing={n:s for n,s in required.items() if n not in existing}
    create_backup(missing,output/'additional-backup');verify_backup(output/'additional-backup/manifest.json',missing)
    binding=dict(plan_sha256=digest(output/'plan.json'),required_sha256=required)
    checks=[check_gradient(samples,(0.0,)*8,CONFIG.l2),check_gradient(samples,(.01,-.01)+(0.0,)*6,CONFIG.l2)]
    rounding={str(raw):native_scores(records['train']+records['validation'],raw) for raw in ((16384,-16384),(-16384,16384))}
    report=dict(schema='rakuyou-mutual-pair-pilot-v1',plan=plan,binding=binding,gradients=checks,numerical_perturbations=rounding,
        saved=[],updates=0,selected_update=None,deployed=False,searches=0,test_roots=0,errors=[],closed=False,
        additional_backup_sha256=digest(output/'additional-backup/manifest.json'))
    path=output/'report.json';write_report(path,report)
    state=initial(CONFIG)
    def save():
        delta=state.average()
        if any(delta[2:]) or any(state.delta[2:]):raise ValueError('Unused updater coordinates changed')
        raw=[math.trunc(x*65536) for x in delta[:2]]
        candidate=dict(schema='rakuyou-mutual-pair-sidecar-v1',feature=FEATURE,base_sha256=gen['runtime_sha256']['bin/params.bin'],
            probe_sha256=digest(PROBE),delta_cp=list(delta[:2]),raw=raw,scale=65536,update=state.updates,operational_loadable=False)
        sidecar=output/f'pair-average-{state.updates:02d}.json';write_report(sidecar,candidate)
        observations={s:native_scores(records[s],raw,execute) for s in records}
        if state.updates==0 and any(x['cp_change'] or x['root_cp_change'] for rows in observations.values() for x in rows):raise ValueError('Zero-delta mismatch')
        val=stats(observations['validation']);val['loss_plus_l2']=val['mean_loss']+.5*CONFIG.l2*math.fsum(x*x for x in delta) if execute else None
        limit=all(max(abs(x['cp_change']),abs(x['root_cp_change']))<=10 for rows in observations.values() for x in rows)
        payload=checkpoint(state,CONFIG,binding);cp=output/f'checkpoint-{state.updates:02d}.json';write_report(cp,payload)
        if restore(json.loads(cp.read_bytes()),CONFIG,binding)!=state:raise ValueError('Checkpoint roundtrip mismatch')
        report['saved'].append(dict(update=state.updates,delta=list(delta[:2]),raw=raw,observations=observations,validation=val,
            within_total_limit=limit,sidecar_sha256=digest(sidecar),checkpoint_sha256=digest(cp)))
        write_report(path,report)
    try:
        save()
        if execute:
            with (GEN/'mutual-pair-learning-attempt-v1.json').open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=binding['plan_sha256']),f)
            while state.updates<20:
                indices,sampled=sample_batch(state,len(samples),CONFIG)
                loss,g=objective([samples[i] for i in indices],state.delta,CONFIG.l2)
                state=step(sampled,g,CONFIG);report['updates']=state.updates
                report.setdefault('trajectory',[]).append(dict(update=state.updates,delta=list(state.delta[:2]),gradient=list(g[:2]),loss=loss))
                if state.updates in (5,10,20):save()
            baseline=report['saved'][0]['validation']['loss_plus_l2']
            choices=[s for s in report['saved'][1:] if s['within_total_limit'] and s['validation']['changed'] and s['validation']['loss_plus_l2']<baseline-1e-12]
            report['selected_update']=min(choices,key=lambda s:(s['validation']['loss_plus_l2'],s['update']))['update'] if choices else 0
        existing_backups(required);verify_backup(output/'additional-backup/manifest.json',missing)
        for n,sha in required.items():
            if digest(ROOT/n)!=sha:raise ValueError('Bound input changed: '+n)
        report['closed']=True
    except Exception as e:
        report['errors'].append(dict(type=type(e).__name__,message=str(e)));report['closed']=True;raise
    finally:write_report(path,report)
    print(json.dumps(dict(updates=report['updates'],selected=report['selected_update'],saved=[dict(update=s['update'],delta=s['delta'],validation=s['validation']) for s in report['saved']]),indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--run',action='store_true')
    a=p.parse_args();run(a.output,a.run)
