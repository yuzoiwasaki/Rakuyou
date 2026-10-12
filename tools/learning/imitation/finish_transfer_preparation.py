#!/usr/bin/env python3
"""Finish static audit from saved4/4 pairs after terminal response guard; no search."""
import sys,json,math
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.imitation import prepare_transfer_pilot as p,sparse_updater as u
from tools.learning.imitation.sparse_objective import native,objective,factors,pair_record,root_cp,write_delta
from tools.learning.data.prepare_learning_data import ROOT,digest,Probe
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.data.refresh_teachers import classify
from tools.learning.data.prepare_refreshed_pilot import frozen_record
from tools.learning.tempo.run_tempo_search import write_report

SOURCE=ROOT/'results/learning-pilot/2026-10-13-imitation-transfer-preparation-v1'


def finish(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    m,reuse=p.load();source=json.loads((SOURCE/'report.json').read_bytes())
    if source['new_searches']!=42 or source['reused_searches']!=6 or source['qsearch_calls']!=16 or source['errors']!=['Forced move mismatch'] or len(source['comparisons'])!=47:
        raise ValueError('Unexpected source failure; no generic retry/recovery')
    if {s:len(x) for s,x in source['pairs'].items()}!={'train':4,'validation':4}:raise ValueError('Saved membership changed')
    output.mkdir(parents=True,exist_ok=False)
    legal=Probe(ROOT/'results/learning-tools/learning-data-probe')
    try:
        for x in source['comparisons']:
            cp,reason=classify(x['result'],x['row'],legal)
            if (cp,reason)!=(x['cp'],x['excluded']):raise ValueError('Saved comparison audit mismatch')
        for split,rows in source['pairs'].items():
            for pair in rows:
                for branch in pair['branches'].values():
                    q=branch['qsearch']
                    dummy=dict(sfen=q['root_sfen'],side_to_move=q['root_side'],teacher_cp=0)
                    _,reason=frozen_record(dummy,q)
                    replay=legal.replay(branch['moves'])
                    if reason or branch['excluded'] or not replay.get('ok') or any(x['occurrences']>1 for x in replay['positions']):raise ValueError('Saved leaf fails eligibility')
                    if replay['positions'][-1]['sfen']!=branch['baseline']['sfen']:raise ValueError('Leaf identity mismatch')
    finally:legal.close()
    old=json.loads((p.OLD/'report.json').read_bytes());r=dict(pairs=source['pairs'],same_moves=source['same_moves'],
        excluded=source['excluded']+[dict(id='historical:2:112',split='validation',stage='comparison',reasons=[dict(reason='special_terminal_unrestricted_and_missing_forced_record')])],
        source_errors=source['errors'],source_report_sha256=digest(SOURCE/'report.json'),incomplete_response_records=1,
        new_searches=0,qsearch_calls=0,source_new_searches=42,source_reused_searches=6,source_qsearch_calls=16,
        plan=source['plan'],updates=0,errors=[],closed=False)
    points=[]
    for split,rows in r['pairs'].items():
        for pair in rows:
            for label,b in pair['branches'].items():points.append(dict(id=pair['id']+':'+label,kind=split+'_leaf',root_side='white',baseline=b['baseline']))
    for split in ('train','validation'):
        for check in m['native_checks']:
            if check['id'] in source['plan'][split+'_ids']:points.append(dict(id=check['id']+':root',kind=split+'_root',root_side='white',baseline=check['root']))
    for x in old['records']['validation']:
        for loc in ('root','leaf'):points.append(dict(id=x['row']['id']+':'+loc,kind='diagnostic_'+loc,root_side=x['row']['side_to_move'],
            stratum=x['row']['stratum'],teacher_cp=x['row']['teacher_cp'],baseline=x[loc]))
    frames=native([x['baseline']['sfen'] for x in points]);lookup={}
    for point,f in zip(points,frames):
        if any(point['baseline'][k]!=f[k] for k in ('sfen','eval_on','eval_off','progress','on_parts','off_parts')):raise ValueError('Zero baseline mismatch')
        point['features']=f;lookup[point['id']]=f
    for split,rows in r['pairs'].items():
        for pair in rows:
            for label,b in pair['branches'].items():b['features']=lookup[pair['id']+':'+label]
            pair['sample']=pair_record(pair['branches']['actual']['features'],pair['branches']['alternative']['features'])
    train=[x['sample'] for x in r['pairs']['train']];keys=sorted({k for x in train for k in x['factors']});loss,g=objective(train,{})
    ratios=sorted(1e-8/abs(g[k]) for k in keys if g.get(k));scale=dict(l2=1e-6,cap_cp=.01,train_only=True,active_parameters=len(keys),
        initial_train_loss=loss,nonzero_gradients=len(ratios),zero_gradients=len(keys)-len(ratios),ratio_median=ratios[(len(ratios)-1)//2],
        ratio_p90=ratios[int((len(ratios)-1)*.9)],ratio_max=max(ratios),above_25percent=sum(x>.25 for x in ratios))
    checks=[]
    for k in sorted(keys,key=lambda k:-abs(g.get(k,0)))[:10]:
        h=.001;a,_=objective(train,{k:h},1e-6);b,_=objective(train,{k:-h},1e-6);error=abs((a-b)/(2*h)-g.get(k,0))
        if error>1e-9:raise ValueError('Gradient mismatch')
        checks.append(dict(key=k,error=error))
    leafkeys=lambda rows:{' '.join(b['features']['sfen'].split()[:3]) for pair in rows for b in pair['branches'].values()}
    overlap=len(leafkeys(r['pairs']['train'])&leafkeys(r['pairs']['validation']))
    raw={k:(1 if g.get(k,0)<0 else -1)*655 for k in keys};write_delta(output/'cap-audit.txt',raw)
    after=native([f['sfen'] for f in frames],output/'cap-audit.txt');obs=[]
    for before,changed,point in zip(frames,after,points):
        if before['features']!=changed['features'] or before['progress']!=changed['progress']:raise ValueError('Key/progress changed')
        expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
        for t,a,b,count in before['features']:
            for lane in ((0,1,2) if t==0 else (0,2)):expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
        for mode in ('on_parts','off_parts'):
            if before[mode]['tempo']!=changed[mode]['tempo']:raise ValueError('Tempo changed')
            for part in ('kp','others'):
                if [changed[mode][part][l]-before[mode][part][l] for l in range(4)]!=expected[part]:raise ValueError('Protected/canonical table mismatch')
        side=point['root_side'];change=root_cp(changed,side)-root_cp(before,side)
        smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in factors(before,side).items())
        if abs(change)>10 or abs(change-smooth)>2.000001:raise ValueError('Position bound')
        obs.append(dict(id=point['id'],change=change,smooth=smooth))
    required=dict(m['required_sha256'])
    for path in [SOURCE/'report.json',SOURCE/'source-failed.py',p.OLD/'report.json',Path(__file__),ROOT/'tools/learning/imitation/prepare_transfer_pilot.py',
        ROOT/'tools/learning/imitation/sparse_objective.py',ROOT/'tools/learning/imitation/sparse_updater.py',p.PROBE,output/'cap-audit.txt']:
        required[str(path.relative_to(ROOT))]=digest(path)
    covered=verify_backup(p.OLD/'backup/manifest.json');covered.update(verify_backup(p.PREP/'backup/manifest.json'))
    extras={n:s for n,s in required.items() if covered.get(n)!=s};create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras)
    binding=dict(preparation_sha256=p.PREP_SHA,active_keys=keys)
    state=u.initial(keys);write_report(output/'checkpoint-00.json',u.checkpoint(state,binding))
    if u.restore(json.loads((output/'checkpoint-00.json').read_bytes()),binding)!=state:raise ValueError('Zero checkpoint mismatch')
    r.update(locations=points,active_keys=keys,initial_gradient=g,scale=scale,gradient_checks=checks,cross_game_leaf_overlap=overlap,cap_observations=obs,
        required_sha256=required,checkpoint_sha256=digest(output/'checkpoint-00.json'),backup_sha256=digest(output/'backup/manifest.json'),
        validation_quality_measured=False,ready_for_training=False,closed=True)
    for n,s in required.items():
        if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
    write_report(output/'report.json',r)
    write_report(output/'audit.json',dict(accepted=True,report_sha256=digest(output/'report.json'),pairs={s:len(x) for s,x in r['pairs'].items()},
        comparison_records_verified=47,usable_branches=16,zero_positions=len(points),cross_game_leaf_overlap=overlap,
        incomplete_source_response_records=1,no_retry_or_refill=True,updates=0,additional_searches=0,additional_qsearch=0))
    print(json.dumps(dict(pairs={s:len(x) for s,x in r['pairs'].items()},scale=scale,overlap=overlap,max_cap_change=max(abs(x['change']) for x in obs)),indent=2));return r

if __name__=='__main__':finish(Path(sys.argv[1]))
