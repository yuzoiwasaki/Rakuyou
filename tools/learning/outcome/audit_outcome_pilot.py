#!/usr/bin/env python3
"""Read-only audit of20 winner-label updates and178x4 packed evaluations."""
import sys,json,math
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.outcome import outcome_pilot as p
from tools.learning.outcome.outcome_objective import objective
from tools.learning.imitation import sparse_updater as u
from tools.learning.imitation.sparse_objective import root_cp,factors
from tools.learning.checks.check_tempo_rounding import score_from_parts
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.data.prepare_learning_data import ROOT,digest
from tools.learning.tempo.run_tempo_search import write_report


def audit(folder):
    folder=Path(folder).resolve();r=json.loads((folder/'report.json').read_bytes());prep=p.load()
    if (not r['closed'] or r['errors'] or r['updates']!=20 or r['selected_update']!=20 or r['searches'] or r['qsearch_calls']
        or r['deployed'] or r['plan']['config']!=u.CONFIG or [x['update'] for x in r['saved']]!=[0,5,10,20]):raise ValueError('Unexpected run scope')
    if digest(folder/'plan.json')!=r['binding']['plan_sha256'] or digest(folder/'backup/manifest.json')!=r['backup_sha256']:raise ValueError('Plan/backup changed')
    verify_backup(folder/'backup/manifest.json')
    for n,s in r['binding']['required_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
    marker=json.loads(p.MARKER.read_bytes())
    if marker['output']!=str(folder.relative_to(ROOT)) or marker['plan_sha256']!=r['binding']['plan_sha256']:raise ValueError('Attempt identity mismatch')
    keys=prep['binding']['active_keys'];train=[x['sample'] for x in prep['records']['train']]
    state=u.initial(keys);states={0:state}
    if len(r['trajectory'])!=20:raise ValueError('Missing updates')
    for t in r['trajectory']:
        loss,g=objective(train,state['delta'],1e-6);state=u.step(state,g)
        if t!=dict(update=state['updates'],loss=loss,gradient=g,state=state):raise ValueError('Trajectory/gradient mismatch')
        if state['updates'] in (5,10,20):states[state['updates']]=state
    for c in r['saved']:
        index=c['update'];state=states[index];delta=u.average(state)
        cp=folder/f'checkpoint-{index:02d}.json';sidecar=folder/f'average-{index:02d}.txt'
        if digest(cp)!=c['checkpoint_sha256'] or digest(sidecar)!=c['sidecar_sha256']:raise ValueError('Candidate hash mismatch')
        if u.restore(json.loads(cp.read_bytes()),r['binding'])!=state:raise ValueError('Checkpoint mismatch')
        raw={}
        for line in sidecar.read_text().splitlines():
            t,a,b,lane,value=map(int,line.split());key=f'{t}:{a}:{b}:{lane}'
            if key in raw:raise ValueError('Duplicate key')
            raw[key]=value
        if raw!={k:math.trunc(v*65536) for k,v in delta.items()}:raise ValueError('Average/raw mismatch')
        for split,rows in prep['records'].items():
            obs=c['observations'][split]
            if len(obs)!=len(rows):raise ValueError('Membership count changed')
            for sample,x in zip(rows,obs):
                before=sample['features'];side=sample['row']['side_to_move'];parts={k:list(v) for k,v in before['on_parts'].items()}
                for t,a,b,count in before['features']:
                    for lane in ((0,1,2) if t==0 else (0,2)):parts['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
                score=score_from_parts(parts,side,before['progress']);base=root_cp(before,side)
                smooth=base+math.fsum(v*delta.get(k,0) for k,v in factors(before,side).items())
                if (x['id']!=sample['id'] or x['target']!=sample['target'] or x['use_outcome_loss']!=sample['use_outcome_loss']
                    or x['base_cp']!=base or x['candidate_cp']!=score or x['smooth_cp']!=smooth or abs(score-base)>10):
                    raise ValueError('Packed evaluation/label mismatch')
            if p.summarize(obs)!=c['summary'][split]:raise ValueError('Side/outcome/draw summary mismatch')
    result=dict(accepted=True,report_sha256=digest(folder/'report.json'),updates=20,selected_update=20,
        trajectory_gradient_average_and_checkpoints_verified=True,packed_evaluation_checks=712,
        train_keys_and_gradients_exclude_masked_draws_and_validation=True,
        no_draw_outcome_loss=True,runtime_and_inputs_unchanged=True,searches=0,qsearch_calls=0,deployed=False,
        auditor_sha256=digest(Path(__file__)))
    out=folder/'audit.json'
    if out.exists():raise ValueError('Do not overwrite audit')
    write_report(out,result)
    required={str(x.relative_to(ROOT)):digest(x) for x in [Path(__file__),out]}
    create_backup(required,folder/'audit-backup');verify_backup(folder/'audit-backup/manifest.json',required)
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':audit(Path(sys.argv[1]))
