#!/usr/bin/env python3
"""One signed mutual gold/silver-pair residual experiment; frozen leaves, no deployment."""
import argparse
import json
import math
import selectors
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path
from prepare_learning_data import ROOT, Probe, digest
from prepare_refreshed_pilot import load_refreshed
from refreshed_tempo_pilot import cached_records
from king_safety_objective import FrozenLeaf, objective, check_gradient, sigmoid, GAIN
from king_safety_updater import Config, initial, sample_batch, step, checkpoint, restore
from king_safety_pilot import stats, independent_columns
from learning_backup import create_backup, verify_backup
from run_tempo_search import write_report

PROBE=ROOT/'results/gold-silver-pair-tools/gold-silver-pair-probe'
PREP=ROOT/'results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1'
GEN=ROOT/'results/learning-pilot/2026-10-11-teacher-refresh-run-v1'
PRECHECK=ROOT/'results/learning-pilot/2026-10-12-gold-silver-pair-precheck-v1/precheck.json'
CONFIG=Config(l2=1e-6)
FEATURE='unpromoted_gold_silver_mutual_pair_both_nonking_defenders_gt_attackers'

class PairProbe(Probe):
    def __init__(self,raw=(0,0)):
        if len(raw)!=2 or any(type(x) is not int or abs(x)>32768 for x in raw):
            raise ValueError('Two signed bounded raw coefficients required')
        self.errors=tempfile.TemporaryFile(mode='w+t');self.qsearch=False
        self.process=subprocess.Popen([str(PROBE),'--pair-perturb',str(ROOT/'bin/params.bin'),*[str(x) for x in raw]],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.errors,text=True,bufsize=1)
        self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)


def prepare(parts,old):
    independent={x['id']:x['counts'] for x in json.loads(PRECHECK.read_bytes())['records']}
    records={s:[] for s in parts};probe=PairProbe()
    try:
        for split in parts:
            for record in old[split]:
                row,frame=record['row'],record['frame'];r=probe.replay(row['moves_before']+frame['pv'])
                if not r.get('ok'):raise ValueError('Illegal frozen PV')
                leaf=r['positions'][-1]
                if (leaf['sfen'],leaf['eval_on'],leaf['progress'],leaf['on_parts'])!=(frame['leaf_sfen'],frame['leaf_eval_full'],frame['leaf_progress'],frame['leaf_parts']):
                    raise ValueError('Baseline/cache mismatch')
                if leaf['pair_counts']!=independent[row['id']]:raise ValueError('Independent/native feature mismatch')
                net=leaf['pair_counts']['black']-leaf['pair_counts']['white']
                sign=1 if frame['root_side']==frame['leaf_side'] else -1
                sample=FrozenLeaf(sign*leaf['eval_on'],row['teacher_cp'],leaf['progress'],row['side_to_move'],(net,0,0,0))
                records[split].append(dict(row=row,frame=frame,leaf=leaf,root=r['positions'][len(row['moves_before'])],sample=sample))
    finally:probe.close()
    return records


def native_scores(records,raw,quality=False):
    probe=PairProbe(raw);out=[]
    try:
        for r in records:
            row,f=r['row'],r['frame'];replay=probe.replay(row['moves_before']+f['pv'])
            if not replay.get('ok'):raise ValueError('Candidate replay failed')
            leaf=replay['positions'][-1];root=replay['positions'][len(row['moves_before'])]
            for before,after in ((r['leaf'],leaf),(r['root'],root)):
                for key in ('sfen','progress','pair_counts','base_on_parts','base_eval_on'):
                    if after[key]!=before[key]:raise ValueError('Baseline/position changed')
                for mode in ('on_parts','off_parts'):
                    for key in ('kp','tempo'):
                        if before[mode][key]!=after[mode][key]:raise ValueError('Protected component changed')
                    net=before['pair_counts']['black']-before['pair_counts']['white']
                    for lane in range(4):
                        expected=net*raw[lane//2] if lane in (0,2) else 0
                        if after[mode]['others'][lane]-before[mode]['others'][lane]!=expected:raise ValueError('Packed pair residual mismatch')
            sign=1 if f['root_side']==f['leaf_side'] else -1
            score=sign*leaf['eval_on'];base=r['sample'].base_root_cp
            smooth=r['sample'].predict(tuple(x/65536 for x in raw)+(0.0,)*6)
            if abs(score-smooth)>2.000001:raise ValueError('Smooth/native mismatch')
            observation=dict(id=row['id'],side=row['side_to_move'],stratum=row['stratum'],base_cp=base,candidate_cp=score,
                cp_change=score-base,smooth_cp_change=smooth-base,root_base_cp=r['root']['eval_on'],root_candidate_cp=root['eval_on'],
                root_cp_change=root['eval_on']-r['root']['eval_on'])
            if quality:observation.update(loss_base=(sigmoid(GAIN*base)-sigmoid(GAIN*row['teacher_cp']))**2,
                loss_candidate=(sigmoid(GAIN*score)-sigmoid(GAIN*row['teacher_cp']))**2)
            out.append(observation)
    finally:probe.close()
    return out


def run(output,execute=False):
    gen,parts,required,_=load_refreshed(GEN/'report.json',GEN/'audit-v2.json')
    prep=json.loads((PREP/'report.json').read_bytes())
    old={s:cached_records(PREP/f'{s}.leaves.json',s,parts[s],prep['binding']['train_sha256' if s=='train' else 'val_sha256']) for s in parts}
    records=prepare(parts,old);samples=[r['sample'] for r in records['train']]
    if independent_columns(samples)!=[0,1]:raise ValueError('Both stage coefficients must be identifiable')
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(schema='rakuyou-mutual-pair-plan-v1',feature=FEATURE,unit='cp per pair; each gold/silver pair counted once',
        interpolation='(1-progress)*opening + progress*end; signed black-minus-white count; no tempo half factor',
        active_slots=[0,1],unused_slots=[2,3,4,5,6,7],initial_delta=[0,0],sign_constraints=None,config=asdict(CONFIG),
        l2_rationale=dict(train_only_initial_gradient=list(objective(samples,(0.0,)*8,0)[1][:2]),
            regularization_gradient_at_coefficient_cap=CONFIG.l2*CONFIG.delta_limit_cp,
            chosen_before_quality_measurement=True),precheck_sha256=digest(PRECHECK),
        runtime_sha256=gen['runtime_sha256'],probe_sha256=digest(PROBE),training_enabled=execute,
        deployment_enabled=False,outcome_loss_enabled=False,max_position_cp_change=10,save_updates=[0,5,10,20])
    write_report(output/'plan.json',plan)
    dependencies=['gold_silver_pair_pilot.py','gold_silver_pair_probe.cc','learning_data_probe.cc','king_safety_objective.py',
        'king_safety_updater.py','king_safety_pilot.py','king_safety_export.py','king_safety_features.h',
        'prepare_learning_data.py','prepare_refreshed_pilot.py','refreshed_tempo_pilot.py','learning_backup.py','run_tempo_search.py']
    for p in [ROOT/'tools'/n for n in dependencies]+[ROOT/'Makefile',ROOT/'test/test_gold_silver_pair_learning.py',ROOT/'test/test_king_safety_learning.py',PROBE,PRECHECK,PREP/'report.json',PREP/'train.leaves.json',PREP/'validation.leaves.json',output/'plan.json']:
        required[p.relative_to(ROOT).as_posix()]=digest(p)
    existing=verify_backup(PREP/'backup/manifest.json');covered={n:s for n,s in required.items() if n in existing};missing={n:s for n,s in required.items() if n not in existing}
    verify_backup(PREP/'backup/manifest.json',covered);create_backup(missing,output/'additional-backup');verify_backup(output/'additional-backup/manifest.json',missing)
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
        verify_backup(PREP/'backup/manifest.json',covered);verify_backup(output/'additional-backup/manifest.json',missing)
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
