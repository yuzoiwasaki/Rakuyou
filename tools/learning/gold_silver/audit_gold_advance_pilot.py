#!/usr/bin/env python3
"""Audit saved twenty-step gold pilot; replay arithmetic only, no engine searches."""
import sys
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import argparse
import json
import math
from tools.learning.gold_silver import gold_advance_pilot as p
from tools.learning.core.king_safety_objective import sigmoid,GAIN


def audit(folder):
    folder=Path(folder).resolve();report_path=folder/'report.json';r=json.loads(report_path.read_bytes())
    prep,records=p.load_prepared();p.verify_backups(prep)
    if (not r['closed'] or r['errors'] or r['updates']!=20 or r['searches'] or r['teacher_searches']
        or r['test_roots'] or r['deployed'] or r['plan']['config']!=prep['plan']['config']
        or r['plan']['selection_rule']!=p.SELECTION or r['plan']['deployment_enabled']
        or [x['update'] for x in r['saved']]!=[0,5,10,20]):raise ValueError('Unexpected run scope')
    extra=json.loads((folder/'additional-backup/manifest.json').read_bytes())
    if p.digest(folder/'additional-backup/manifest.json')!=r['additional_backup_sha256']:
        raise ValueError('Additional backup manifest changed')
    p.verify_backup(folder/'additional-backup/manifest.json')
    for name,sha in r['binding']['required_sha256'].items():
        if p.digest(p.ROOT/name)!=sha:raise ValueError('Protected input changed: '+name)
    marker=json.loads(p.MARKER.read_bytes())
    if marker['output']!=folder.relative_to(p.ROOT).as_posix() or marker['plan_sha256']!=r['binding']['plan_sha256']:
        raise ValueError('Attempt identity changed')
    state=p.initial(p.CONFIG);states={0:state};samples=[x['sample'] for x in records['train']]
    if len(r['trajectory'])!=20:raise ValueError('Missing trajectory')
    for t in r['trajectory']:
        indices,sampled=p.sample_batch(state,len(samples),p.CONFIG)
        loss,g=p.objective([samples[i] for i in indices],state.delta,p.CONFIG.l2)
        state=p.step(sampled,g,p.CONFIG)
        if t!=dict(update=state.updates,indices=indices,gradient=list(g),loss=loss,delta=list(state.delta)):
            raise ValueError('Saved RNG/gradient/trajectory mismatch')
        if state.updates in (5,10,20):states[state.updates]=state
    smooth={}
    for c in r['saved']:
        update=c['update'];state=states[update];delta=state.average()
        if c['delta_cp']!=list(delta[:2]) or c['raw']!=[math.trunc(x*65536) for x in delta[:2]]:
            raise ValueError('Candidate average/raw mismatch')
        cp=folder/f'checkpoint-{update:02d}.json';sidecar=folder/f'gold-average-{update:02d}.json'
        if p.digest(cp)!=c['checkpoint_sha256'] or p.digest(sidecar)!=c['sidecar_sha256']:
            raise ValueError('Saved candidate changed')
        if p.restore(json.loads(cp.read_bytes()),p.CONFIG,r['binding'])!=state:
            raise ValueError('Checkpoint trajectory mismatch')
        side=json.loads(sidecar.read_bytes())
        if side['delta_cp']!=c['delta_cp'] or side['raw']!=c['raw'] or side['operational_loadable']:
            raise ValueError('Sidecar mismatch')
        smooth[str(update)]={}
        for split,rows in records.items():
            observations=c['observations'][split]
            if [x['id'] for x in observations]!=[x['row']['id'] for x in rows]:raise ValueError('Observation scope mismatch')
            for x,record in zip(observations,rows):
                sample=record['sample'];base=sample.base_root_cp
                expected_smooth=sample.predict(tuple(x/65536 for x in c['raw'])+(0.0,)*6)-base
                if (x['base_cp']!=base or x['cp_change']!=x['candidate_cp']-base
                    or x['smooth_cp_change']!=expected_smooth
                    or x['loss_base']!=(sigmoid(GAIN*base)-sigmoid(GAIN*sample.teacher_root_cp))**2
                    or x['loss_candidate']!=(sigmoid(GAIN*x['candidate_cp'])-sigmoid(GAIN*sample.teacher_root_cp))**2):
                    raise ValueError('Saved score/loss arithmetic mismatch')
            if p.summary(observations)!=c['summary'][split]:raise ValueError('Summary mismatch')
            loss,_=p.objective([x['sample'] for x in rows],delta,0)
            base_loss,_=p.objective([x['sample'] for x in rows],(0.0,)*8,0)
            smooth[str(update)][split]=dict(loss=loss,base_loss=base_loss,
                relative_improvement=(base_loss-loss)/base_loss,
                max_abs_cp_change=max(abs(x['sample'].predict(delta)-x['sample'].base_root_cp) for x in rows))
        expected=c['summary']['validation']['all']['mean_loss']+.5*p.CONFIG.l2*math.fsum(x*x for x in delta)
        if c['validation_loss_plus_l2']!=expected:raise ValueError('Selection objective mismatch')
    if p.choose(r['saved'])!=r['selected_update']:raise ValueError('Selection mismatch')
    result=dict(accepted=True,report_sha256=p.digest(report_path),updates=20,selected_update=r['selected_update'],
        trajectory_rng_gradient_and_checkpoints_verified=True,input_and_backups_verified=True,
        searches=0,teacher_searches=0,test_roots=0,deployed=False,
        full_precision_smooth=smooth,auditor_sha256=p.digest(Path(__file__)))
    out=folder/'audit-v1.json'
    if out.exists():raise ValueError('Audit output already exists')
    p.write_report(out,result);print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    args=parser.parse_args();audit(args.folder)
