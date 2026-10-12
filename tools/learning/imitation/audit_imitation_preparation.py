#!/usr/bin/env python3
"""Audit saved six-pair preparation plus static root/cap checks; no qsearch or updates."""
import sys,json,math
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.imitation import prepare_imitation as p
from tools.learning.imitation.sparse_objective import native,factors,root_cp,write_delta,objective,transformed
from tools.learning.data.prepare_learning_data import Probe,digest,ROOT
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report
REPORT_SHA='c119a11de5a9b53655c0396ade1deb3da5d0491516710675b2f822da9f22cc96'


def audit(folder):
    folder=Path(folder).resolve()
    if digest(folder/'report.json')!=REPORT_SHA:raise ValueError('Preparation changed')
    r=json.loads((folder/'report.json').read_bytes());a=json.loads((folder/'audit.json').read_bytes())
    if (not a['accepted'] or a['report_sha256']!=REPORT_SHA or r['updates'] or r['errors']
        or not r['closed'] or r['qsearch_calls']!=12 or len(r['pairs'])!=6 or r['excluded']):
        raise ValueError('Expected audited6pairs/update0')
    covered=verify_backup(p.OLD/'backup/manifest.json');covered.update(verify_backup(folder/'backup/manifest.json'))
    for name,sha in r['required_sha256'].items():
        if covered.get(name)!=sha or digest(ROOT/name)!=sha:raise ValueError('Protected source/backup mismatch')
    state=json.loads((folder/'checkpoint-00.json').read_bytes())
    if digest(folder/'checkpoint-00.json')!=r['checkpoint_sha256'] or state['updates'] or any(state['delta_cp'].values()) or any(state['average_cp'].values()):
        raise ValueError('Checkpoint not zero')
    samples=[x['sample'] for x in r['pairs']]
    loss,g=objective(samples,{})
    if loss!=r['l2']['initial_loss'] or g!=r['initial_gradient']:raise ValueError('Gradient/loss mismatch')
    old=json.loads((p.OLD/'report.json').read_bytes());roots=[];probe=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',details=True)
    try:
        for pair in r['pairs']:
            replay=probe.replay(pair['row']['moves_before'])
            if not replay.get('ok'):raise ValueError('Root history illegal')
            roots.append(replay['positions'][-1])
        for row in old['records']['validation']:
            roots.append(row['root'])
    finally:probe.close()
    root_frames=native([x['sfen'] for x in roots])
    for before,after in zip(roots,root_frames):
        if any(before[k]!=after[k] for k in ('sfen','progress','eval_on','eval_off','on_parts','off_parts')):
            raise ValueError('Static root zero mismatch')
    frames=[b['features'] for pair in r['pairs'] for b in pair['branches'].values()]+[v['features'] for v in r['validation']]+root_frames
    keys=state['active_keys'];active=set(keys)
    max_l1=max(math.fsum(abs(v) for k,v in factors(f).items() if k in active) for f in frames)
    # Fixed pre-training proposal: 0.01cp per canonical key; all 38 nonking pieces
    # contribute <=76 KP references and 38*39/2=741 PP references at any phase.
    theoretical_l1=2*38+38*39//2
    checks={}
    for direction in (1,-1):
        raw={k:direction*(-1 if g[k]>0 else 1)*655 for k in keys}
        path=folder/f'cap-direction-{direction}.txt';write_delta(path,raw)
        candidates=native([f['sfen'] for f in frames],path)
        observations=[]
        for before,after in zip(frames,candidates):
            for mode in ('on_parts','off_parts'):
                expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
                for t,first,second,count in before['features']:
                    for lane in ((0,1,2) if t==0 else (0,2)):
                        expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{first}:{second}:{lane}',0)
                if after[mode]['tempo']!=before[mode]['tempo']:raise ValueError('Tempo changed')
                for part in ('kp','others'):
                    if [after[mode][part][l]-before[mode][part][l] for l in range(4)]!=expected[part]:
                        raise ValueError('Protected lanes or canonical table change mismatch')
            smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in factors(before).items())
            change=root_cp(after)-root_cp(before)
            if abs(change-smooth)>2.000001 or abs(change)>10:raise ValueError('Position bound exceeded')
            observations.append(dict(sfen=before['sfen'],change=change,smooth=smooth))
        checks[str(direction)]=dict(max_integer_change=max(abs(x['change']) for x in observations),
            max_smooth_change=max(abs(x['smooth']) for x in observations),observations=observations)
    if max_l1>theoretical_l1+1e-9:raise ValueError('Reference-count bound inconsistent')
    result=dict(accepted=True,report_sha256=REPORT_SHA,updates=0,searches=0,qsearch_calls=0,
        effective_pairs=6,zero_leaf_positions=47,additional_zero_roots=41,
        root_side='white',validation_roots_and_leaves=35,active_parameters=len(keys),
        proposed_per_key_cap_cp=.01,proposed_l2=1e-6,cap_change_not_applied_to_training=True,
        max_observed_active_l1=max_l1,global_l1_bound=theoretical_l1,
        global_smooth_bound_cp=theoretical_l1*.01,global_integer_bound_cp=math.ceil(theoretical_l1*.01),
        cap_direction_checks=checks,baseline_backups_verified=True,checkpoint_zero_verified=True,
        auditor_sha256=digest(Path(__file__)))
    out=folder/'saved-results-audit.json'
    if out.exists():raise ValueError('Do not overwrite audit')
    write_report(out,result)
    paths=[Path(__file__),out]+list(folder.glob('cap-direction-*.txt'))
    required={str(x.relative_to(ROOT)):digest(x) for x in paths};create_backup(required,folder/'audit-backup');verify_backup(folder/'audit-backup/manifest.json',required)
    print(json.dumps({k:v for k,v in result.items() if k!='cap_direction_checks'},indent=2))
    print({k:(v['max_integer_change'],v['max_smooth_change']) for k,v in checks.items()})
    return result

if __name__=='__main__':audit(Path(sys.argv[1]))
