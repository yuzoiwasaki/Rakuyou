#!/usr/bin/env python3
"""Read-only audit of game-split transfer trajectory and packed evaluations."""
import sys,json,math
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.imitation import imitation_pilot as pilot,sparse_updater as u,transfer_pilot as transfer
from tools.learning.imitation.sparse_objective import objective,factors,root_cp
from tools.learning.checks.check_tempo_rounding import score_from_parts
from tools.learning.data.prepare_learning_data import digest,ROOT
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report


def audit(folder):
    folder=Path(folder).resolve();r=json.loads((folder/'report.json').read_bytes());prep=transfer.load();keys=prep['active_keys']
    if (not r['closed'] or r['errors'] or r['updates']!=20 or r['selected_update']!=20 or r['searches']
        or r['qsearch_calls'] or r['deployed'] or r['plan']['config']!=u.CONFIG
        or [c['update'] for c in r['saved']]!=[0,5,10,20]):raise ValueError('Unexpected run scope')
    if digest(folder/'plan.json')!=r['binding']['plan_sha256']:raise ValueError('Plan changed')
    if digest(folder/'backup/manifest.json')!=r['backup_sha256']:raise ValueError('Backup changed')
    verify_backup(folder/'backup/manifest.json')
    for n,s in r['binding']['required_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Protected input changed: '+n)
    marker=json.loads(transfer.MARKER.read_bytes())
    if marker['output']!=str(folder.relative_to(ROOT)) or marker['plan_sha256']!=r['binding']['plan_sha256']:raise ValueError('Attempt identity mismatch')
    points=json.loads((folder/'baseline-locations.json').read_bytes());samples=[p['sample'] for p in prep['pairs']['train']];all_samples=[p['sample'] for split in ('train','validation') for p in prep['pairs'][split]]
    s=u.initial(keys);states={0:s}
    if len(r['trajectory'])!=20:raise ValueError('Missing trajectory')
    for t in r['trajectory']:
        loss,g=objective(samples,s['delta'],1e-6);s=u.step(s,g)
        if t!=dict(update=s['updates'],loss=loss,gradient=g,state=s):raise ValueError('Trajectory/gradient mismatch')
        if s['updates'] in (5,10,20):states[s['updates']]=s
    smooth_validation={}
    for c in r['saved']:
        update=c['update'];s=states[update];delta=u.average(s)
        cp=folder/f'checkpoint-{update:02d}.json';sidecar=folder/f'average-{update:02d}.txt'
        if digest(cp)!=c['checkpoint_sha256'] or digest(sidecar)!=c['sidecar_sha256']:raise ValueError('Candidate hash changed')
        if u.restore(json.loads(cp.read_bytes()),r['binding'])!=s:raise ValueError('Checkpoint mismatch')
        raw={}
        for line in sidecar.read_text().splitlines():
            t,a,b,lane,value=map(int,line.split());k=f'{t}:{a}:{b}:{lane}'
            if k in raw:raise ValueError('Duplicate raw key')
            raw[k]=value
        if raw!={k:math.trunc(v*65536) for k,v in delta.items()}:raise ValueError('Average/raw mismatch')
        if len(c['observations'])!=len(points):raise ValueError('Observation scope')
        for point,x in zip(points,c['observations']):
            before=point['baseline'];parts={k:list(v) for k,v in before['on_parts'].items()}
            for t,a,b,count in before['features']:
                for lane in ((0,1,2) if t==0 else (0,2)):
                    parts['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
            native_side='black' if before['sfen'].split()[1]=='b' else 'white'
            candidate=score_from_parts(parts,native_side,before['progress'])*(1 if native_side==point['root_side'] else -1)
            smooth=math.fsum(v*delta.get(k,0) for k,v in factors(before,point['root_side']).items())
            if x['id']!=point['id'] or x['candidate_cp']!=candidate or x['base_cp']!=root_cp(before,point['root_side']) or x['smooth_change']!=smooth or abs(x['change'])>10:
                raise ValueError('Packed candidate evaluation mismatch')
            if 'teacher_cp' in point:
                target=pilot.sigmoid(pilot.GAIN*point['teacher_cp'])
                if x['loss_base']!=(pilot.sigmoid(pilot.GAIN*x['base_cp'])-target)**2 or x['loss_candidate']!=(pilot.sigmoid(pilot.GAIN*candidate)-target)**2:
                    raise ValueError('Diagnostic loss mismatch')
        if pilot.summarize(c['observations'])!=c['validation']:raise ValueError('Diagnostic summary mismatch')
        loss,_=objective(all_samples,delta,0)
        native_samples=[]
        for i,(pair,sample) in enumerate(zip(c['pairs'],all_samples)):
            actual,alt=c['observations'][2*i:2*i+2]
            gap=alt['candidate_cp']-actual['candidate_cp']
            smooth_gap=sample['base_gap']+math.fsum(v*delta.get(k,0) for k,v in sample['factors'].items())
            if pair['gap']!=gap or pair['smooth_gap']!=smooth_gap:raise ValueError('Pair gap mismatch')
            native_samples.append(dict(base_gap=gap,factors={}))
        integer_loss,_=objective(native_samples,{})
        if loss!=c['pair_loss_smooth'] or integer_loss!=c['pair_loss_integer']:raise ValueError('Pair loss mismatch')
        for split,source_pairs in prep['pairs'].items():
            recorded=c['transfer'][split]
            base,_=objective([x['sample'] for x in source_pairs],{},0)
            smooth,_=objective([x['sample'] for x in source_pairs],delta,0)
            ids={x['id'] for x in source_pairs}
            pair_rows=[x for x in c['pairs'] if x['id'] in ids]
            integer,_=objective([dict(base_gap=x['gap'],factors={}) for x in pair_rows],{})
            if recorded!=dict(pairs=len(pair_rows),loss_base=base,loss_integer=integer,loss_smooth=smooth,
                relative_integer_improvement=(base-integer)/base,relative_smooth_improvement=(base-smooth)/base,pair_gaps=pair_rows):
                raise ValueError('Transfer held-game summary mismatch')

        rows=[]
        for p,x in zip(points,c['observations']):
            if p['kind']=='validation_leaf':
                target=pilot.sigmoid(pilot.GAIN*p['teacher_cp'])
                rows.append(dict(side=p['root_side'],stratum=p['stratum'],base=(pilot.sigmoid(pilot.GAIN*x['base_cp'])-target)**2,
                    loss=(pilot.sigmoid(pilot.GAIN*(x['base_cp']+x['smooth_change']))-target)**2))
        def stats(rs):
            base=math.fsum(x['base'] for x in rs)/len(rs);loss=math.fsum(x['loss'] for x in rs)/len(rs)
            return dict(positions=len(rs),loss=loss,relative_improvement=(base-loss)/base)
        smooth_validation[str(update)]=dict(all=stats(rows),side={side:stats([x for x in rows if x['side']==side]) for side in ('black','white')},draw=stats([x for x in rows if x['stratum'].endswith(':draw')]))
    result=dict(accepted=True,gradient_uses_train_game_only=True,report_sha256=digest(folder/'report.json'),updates=20,selected_update=20,
        trajectory_gradient_average_and_checkpoints_verified=True,packed_evaluation_checks=4*len(points),
        input_and_backups_unchanged=True,searches=0,qsearch_calls=0,deployed=False,
        smooth_validation=smooth_validation,auditor_sha256=digest(Path(__file__)))
    output=folder/'audit.json'
    if output.exists():raise ValueError('Do not overwrite audit')
    write_report(output,result)
    paths=[Path(__file__),output];required={str(p.relative_to(ROOT)):digest(p) for p in paths}
    create_backup(required,folder/'audit-backup');verify_backup(folder/'audit-backup/manifest.json',required)
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':audit(Path(sys.argv[1]))
