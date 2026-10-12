#!/usr/bin/env python3
"""One fixed20-update central supported-pawn pilot; no searches or deployment."""
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0,str(_RepoPath(__file__).resolve().parents[3]))

import argparse
import json
import math
import subprocess
from pathlib import Path
from tools.learning.gold_silver.supported_pawn_preparation import (
    CONFIG, FEATURE, PROBE, ROOT, FrozenLeaf, native_scores)
from tools.learning.core.king_safety_objective import objective
from tools.learning.core.king_safety_updater import initial, sample_batch, step, checkpoint, restore
from tools.learning.core.learning_backup import create_backup, verify_backup
from tools.learning.data.prepare_learning_data import digest
from tools.learning.tempo.run_tempo_search import write_report

PREPARATION = ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
MARKER = PREPARATION/'learning-attempt-v1.json'
REPORT_SHA = '060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4'
AUDIT_SHA = '1738668b3580e41db2436736667ab158c661d9301fb418983c6d71da2b92b0ed'
SELECTION = 'min validation integer-loss plus L2 among changed bounded improvements; tie earliest; else0'


def load_prepared():
    if digest(PREPARATION/'report.json')!=REPORT_SHA or digest(PREPARATION/'audit-v1.json')!=AUDIT_SHA:
        raise ValueError('Preparation/audit SHA mismatch')
    p=json.loads((PREPARATION/'report.json').read_bytes())
    a=json.loads((PREPARATION/'audit-v1.json').read_bytes())
    from dataclasses import asdict
    if (not a['accepted'] or a['report_sha256']!=REPORT_SHA or p['errors'] or not p['closed']
            or p['updates'] or p['searches'] or p['test_roots'] or p['deployed']
            or p['plan']['feature']!=FEATURE or p['plan']['config']!=asdict(CONFIG)
            or p['plan']['training_enabled'] or p['plan']['deployment_enabled']
            or p['validation_quality_measured']):
        raise ValueError('Expected fixed, audited, untrained preparation')
    for name,sha in (('plan.json',p['binding']['plan_sha256']),
                     ('checkpoint-00.json',p['checkpoint_sha256']),
                     ('pawn-average-00.json',p['sidecar_sha256']),
                     ('backup/manifest.json',p['backup_sha256'])):
        if digest(PREPARATION/name)!=sha:raise ValueError('Prepared output changed: '+name)
    verify_backup(PREPARATION/'backup/manifest.json',p['binding']['required_sha256'])
    state=restore(json.loads((PREPARATION/'checkpoint-00.json').read_bytes()),CONFIG,p['binding'])
    if state!=initial(CONFIG):raise ValueError('Prepared state is not zero')
    if digest(PROBE)!=p['plan']['probe_sha256']:raise ValueError('Feature probe changed')
    records={}
    for split,size in (('train',143),('validation',35)):
        records[split]=[]
        for saved in p['records'][split]:
            r=dict(saved);row,f,leaf=r['row'],r['frame'],r['leaf']
            counts=leaf['supported_pawn_counts'];net=counts['black']-counts['white']
            sign=1 if f['root_side']==f['leaf_side'] else -1
            r['sample']=FrozenLeaf(sign*leaf['eval_on'],row['teacher_cp'],leaf['progress'],row['side_to_move'],(net,0,0,0))
            records[split].append(r)
        if len(records[split])!=size or len({r['row']['id'] for r in records[split]})!=size:
            raise ValueError('Fixed143/35 membership changed')
    return p,records


def summary(rows):
    def group(selected):
        if not selected:return dict(positions=0)
        base=math.fsum(x['loss_base'] for x in selected)/len(selected)
        candidate=math.fsum(x['loss_candidate'] for x in selected)/len(selected)
        return dict(positions=len(selected),changed=sum(x['cp_change']!=0 for x in selected),
                    max_abs_cp_change=max(abs(x['cp_change']) for x in selected),
                    max_abs_root_cp_change=max(abs(x['root_cp_change']) for x in selected),
                    max_abs_smooth_cp_change=max(abs(x['smooth_cp_change']) for x in selected),
                    mean_loss_base=base,mean_loss=candidate,
                    relative_loss_improvement=(base-candidate)/base if base else None)
    return dict(all=group(rows),side={s:group([x for x in rows if x['side']==s]) for s in ('black','white')},
                draw=group([x for x in rows if x['stratum'].endswith(':draw')]),
                strata={s:group([x for x in rows if x['stratum']==s]) for s in sorted({x['stratum'] for x in rows})})


def choose(saved):
    baseline=saved[0]['validation_loss_plus_l2']
    candidates=[x for x in saved[1:] if x['within_total_limit'] and x['summary']['validation']['all']['changed']
                and x['validation_loss_plus_l2']<baseline-1e-12]
    return min(candidates,key=lambda x:(x['validation_loss_plus_l2'],x['update']))['update'] if candidates else 0


def run(output,execute=False):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():
        raise ValueError('A new results directory is required')
    if MARKER.exists():raise ValueError('This supported-pawn learning attempt is already closed/started')
    prep,records=load_prepared()
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(prep['plan']);plan.update(schema='rakuyou-supported-pawn-execution-plan-v1',
        training_enabled=execute,selection_rule=SELECTION,preparation_report_sha256=REPORT_SHA,
        preparation_audit_sha256=AUDIT_SHA)
    write_report(output/'plan.json',plan)
    if execute:
        with MARKER.open('x') as stream:
            json.dump(dict(output=output.relative_to(ROOT).as_posix(),plan_sha256=digest(output/'plan.json'),
                           max_updates=20),stream,sort_keys=True);stream.write('\n')
    required=dict(prep['binding']['required_sha256'])
    extras=[PREPARATION/'report.json',PREPARATION/'audit-v1.json',PREPARATION/'plan.json',
            PREPARATION/'checkpoint-00.json',PREPARATION/'pawn-average-00.json',
            PREPARATION/'backup/manifest.json',Path(__file__),
            ROOT/'test/learning/gold_silver/test_supported_pawn_pilot.py',output/'plan.json']
    if execute:extras.append(MARKER)
    extra_sha={p.relative_to(ROOT).as_posix():digest(p) for p in extras}
    create_backup(extra_sha,output/'additional-backup')
    verify_backup(output/'additional-backup/manifest.json',extra_sha)
    required.update(extra_sha)
    binding=dict(feature=FEATURE,plan_sha256=digest(output/'plan.json'),required_sha256=required)
    report=dict(schema='rakuyou-supported-pawn-pilot-v1',plan=plan,binding=binding,
        preparation_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        harness_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        updates=0,saved=[],trajectory=[],selected_update=None,deployed=False,searches=0,teacher_searches=0,
        test_roots=0,errors=[],closed=False,
        additional_backup_sha256=digest(output/'additional-backup/manifest.json'))
    path=output/'report.json';write_report(path,report)
    state=initial(CONFIG)
    samples=[r['sample'] for r in records['train']]
    def save():
        delta=state.average()
        if any(delta[2:]) or any(state.delta[2:]):raise ValueError('Unused slots changed')
        raw=[math.trunc(x*65536) for x in delta[:2]]
        sidecar=output/f'pawn-average-{state.updates:02d}.json'
        write_report(sidecar,dict(schema='rakuyou-supported-pawn-sidecar-v1',feature=FEATURE,
                    base_sha256=plan['runtime_sha256']['bin/params.bin'],probe_sha256=digest(PROBE),
                    delta_cp=list(delta[:2]),raw=raw,scale=65536,update=state.updates,operational_loadable=False))
        observations={s:native_scores(rows,raw,quality=True) for s,rows in records.items()}
        if state.updates==0 and any(x['cp_change'] or x['root_cp_change'] for rows in observations.values() for x in rows):
            raise ValueError('Zero baseline changed')
        summaries={s:summary(rows) for s,rows in observations.items()}
        within=all(max(abs(x['cp_change']),abs(x['root_cp_change']))<=plan['max_position_cp_change']
                   for rows in observations.values() for x in rows)
        cp=output/f'checkpoint-{state.updates:02d}.json'
        write_report(cp,checkpoint(state,CONFIG,binding))
        if restore(json.loads(cp.read_bytes()),CONFIG,binding)!=state:raise ValueError('Checkpoint roundtrip mismatch')
        report['saved'].append(dict(update=state.updates,delta_cp=list(delta[:2]),raw=raw,
            summary=summaries,observations=observations,within_total_limit=within,
            validation_loss_plus_l2=summaries['validation']['all']['mean_loss']+.5*CONFIG.l2*math.fsum(x*x for x in delta),
            sidecar_sha256=digest(sidecar),checkpoint_sha256=digest(cp)))
        write_report(path,report)
    try:
        save()
        if execute:
            while state.updates<20:
                indices,sampled=sample_batch(state,len(samples),CONFIG)
                loss,g=objective([samples[i] for i in indices],state.delta,CONFIG.l2)
                state=step(sampled,g,CONFIG)
                report['updates']=state.updates
                report['trajectory'].append(dict(update=state.updates,indices=indices,
                    gradient=list(g),loss=loss,delta=list(state.delta)))
                if state.updates in (5,10,20):save()
            report['selected_update']=choose(report['saved'])
        verify_backup(PREPARATION/'backup/manifest.json',prep['binding']['required_sha256'])
        verify_backup(output/'additional-backup/manifest.json',extra_sha)
        for name,sha in required.items():
            if digest(ROOT/name)!=sha:raise ValueError('Protected input changed: '+name)
        report['closed']=True
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error)))
        report['closed']=True
        raise
    finally:write_report(path,report)
    print(json.dumps(dict(updates=report['updates'],selected=report['selected_update'],
                         checkpoints=[dict(update=x['update'],delta=x['delta_cp'],summary=x['summary']) for x in report['saved']]),indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    run(args.output,args.run)
