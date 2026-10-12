#!/usr/bin/env python3
"""Prepare frozen six-pair sparse imitation, audit zero and scale; no optimizer."""
import sys
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json,math,argparse
from collections import Counter
from tools.learning.data.prepare_learning_data import ROOT,Probe,digest
from tools.learning.data.prepare_refreshed_pilot import frozen_record
from tools.learning.core.learning_backup import create_backup,verify_backup
from tools.learning.tempo.run_tempo_search import write_report
from tools.learning.imitation.sparse_objective import native,factors,root_cp,pair_record,objective,write_delta,transformed,PROBE,TEMPERATURE_CP

SOURCE=ROOT/'results/learning-pilot/2026-10-12-historical-move-comparison-v1'
SOURCE_SHA='d7825b838e41f8f544107874ef6571e6c1e65cfae250274b0c19d013dcd9dacd'
OLD=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
OLD_SHA='060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4'


def prepare(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if digest(SOURCE/'report.json')!=SOURCE_SHA or digest(OLD/'report.json')!=OLD_SHA:raise ValueError('Bound data changed')
    report=json.loads((SOURCE/'report.json').read_bytes());audit=json.loads((SOURCE/'audit.json').read_bytes())
    source_plan=json.loads((SOURCE/'plan.json').read_bytes())
    if not audit['accepted'] or audit['report_sha256']!=SOURCE_SHA or report['errors'] or report['completed']!=16:raise ValueError('Expected audited comparison')
    for n,s in source_plan['runtime_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Runtime changed')
    build=json.loads((PROBE.parent/'build-report.json').read_bytes())
    if digest(PROBE)!=build['probe_sha256']:raise ValueError('Probe changed')
    for n,s in build['inputs'].items():
        if digest(ROOT/n)!=s:raise ValueError('Build input changed')
    selected=[]
    for i in range(0,16,2):
        alternative,actual=report['records'][i:i+2]
        if actual['row']!=alternative['row'] or actual['excluded'] or alternative['excluded']:raise ValueError('Incomplete comparison pair')
        if actual['result']['bestmove']!=alternative['result']['bestmove']:
            selected.append(dict(id=actual['row']['id'],row=actual['row'],branches={'actual':actual,'alternative':alternative}))
    if len(selected)!=6:raise ValueError('Expected fixed six distinct pairs')
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(source_sha256=SOURCE_SHA,ids=[r['id'] for r in selected],max_qsearch_calls=12,updates=0,
        training_enabled=False,outcome_loss_enabled=False,temperature_cp=TEMPERATURE_CP,probe_sha256=digest(PROBE),
        runtime_sha256=source_plan['runtime_sha256'],max_position_cp_change=10,per_key_cap_cp=.5)
    write_report(output/'plan.json',plan)
    with (SOURCE/'imitation-leaf-preparation-attempt-v1.json').open('x') as stream:
        json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json')),stream)
    result=dict(pairs=[],excluded=[],qsearch_calls=0,updates=0,closed=False,errors=[],plan=plan)
    write_report(output/'report.json',result)
    q=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',qsearch_progress=ROOT/'bin/progress.bin')
    static=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',details=True)
    try:
        for item in selected:
            pair=dict(id=item['id'],row=item['row'],branches={});excluded=[]
            for label,record in item['branches'].items():
                moves=item['row']['moves_before']+record['result']['candidates'][0]['pv']
                print(item['id'],label,flush=True)
                frame=q.replay(moves);result['qsearch_calls']+=1
                terminal=static.replay(moves)
                if not terminal.get('ok'):raise ValueError('Saved PV became illegal')
                row=dict(sfen=terminal['positions'][-1]['sfen'],side_to_move='black' if len(moves)%2==0 else 'white',teacher_cp=0)
                _,reason=frozen_record(row,frame)
                all_moves=moves+(frame.get('pv') or [])
                replay=static.replay(all_moves)
                if not replay.get('ok'):raise ValueError('Qsearch PV illegal')
                if any(p['occurrences']>1 for p in replay['positions']):reason=reason or 'repeated_history'
                if reason:excluded.append(dict(branch=label,reason=reason))
                leaf=replay['positions'][-1]
                pair['branches'][label]=dict(moves=all_moves,qsearch=frame,baseline=leaf,excluded=reason)
                write_report(output/'report.json',result)
            if excluded:result['excluded'].append(dict(id=item['id'],reasons=excluded))
            else:result['pairs'].append(pair)
            write_report(output/'report.json',result)
    finally:q.close();static.close()
    if not result['pairs']:raise ValueError('No usable frozen pairs; do not refill')
    old=json.loads((OLD/'report.json').read_bytes())
    validation=[dict(row=r['row'],sfen=r['leaf']['sfen'],baseline=r['leaf']) for r in old['records']['validation']]
    if len(validation)!=35:raise ValueError('Expected unchanged diagnostic35')
    frames=native([b['baseline']['sfen'] for p in result['pairs'] for b in p['branches'].values()]+[v['sfen'] for v in validation])
    cursor=0
    for pair in result['pairs']:
        for branch in pair['branches'].values():branch['features']=frames[cursor];cursor+=1
        pair['sample']=pair_record(pair['branches']['actual']['features'],pair['branches']['alternative']['features'])
    for v in validation:v['features']=frames[cursor];cursor+=1
    identities=[(b['baseline'],b['features']) for p in result['pairs'] for b in p['branches'].values()]+[(v['baseline'],v['features']) for v in validation]
    for before,after in identities:
        if any(before[k]!=after[k] for k in ('sfen','progress','eval_on','eval_off','on_parts','off_parts')):raise ValueError('Zero native baseline mismatch')
    samples=[p['sample'] for p in result['pairs']];loss,gradient=objective(samples,{})
    keys=sorted({k for p in samples for k in p['factors']})
    # Training-only scale diagnostics; no validation losses or parameter updates.
    nonzero=[abs(gradient[k]) for k in keys if gradient.get(k)]
    ratios=sorted(5e-7/g for g in nonzero)
    def quantile(values,q):return values[int((len(values)-1)*q)] if values else None
    l2=dict(proposed=1e-6,per_key_cap_gradient=5e-7,active_parameters=len(keys),
        initial_loss=loss,gradient_nonzero=len(nonzero),gradient_zero=len(keys)-len(nonzero),
        ratio_median=quantile(ratios,.5),ratio_p90=quantile(ratios,.9),
        ratio_above_25percent=sum(x>.25 for x in ratios),validation_quality_measured=False)
    checked=[]
    for k in sorted(keys,key=lambda k:-abs(gradient.get(k,0)))[:5]+keys[:5]:
        h=.001;a,_=objective(samples,{k:h},1e-6);b,_=objective(samples,{k:-h},1e-6)
        error=abs((a-b)/(2*h)-gradient.get(k,0))
        if error>1e-9:raise ValueError('Pair gradient mismatch')
        checked.append(dict(key=k,error=error))
    active=set(keys);sfens=[f['sfen'] for f in frames]
    subsets=[{k:v for k,v in factors(f).items() if k in active} for f in frames]
    worst=max(math.fsum(abs(x) for x in fs.values())*.5 for fs in subsets)
    # A fixed small numerical perturbation, unrelated to gradient signs or quality.
    raw={k:(1 if i%2 else -1)*64 for i,k in enumerate(keys)}
    write_delta(output/'numerical-perturbation.txt',raw)
    changed=native(sfens,output/'numerical-perturbation.txt');observations=[]
    for before,after,fs in zip(frames,changed,subsets):
        if before['features']!=after['features'] or before['progress']!=after['progress']:raise ValueError('Features/progress changed')
        expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
        for t,a,b,count in before['features']:
            for lane in ((0,1,2) if t==0 else (0,2)):
                expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
        for mode in ('on_parts','off_parts'):
            if before[mode]['tempo']!=after[mode]['tempo']:raise ValueError('Tempo changed')
            for component in ('kp','others'):
                if [after[mode][component][l]-before[mode][component][l] for l in range(4)]!=expected[component]:raise ValueError('Sparse table/canonical feature mismatch')
        smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in fs.items())
        change=root_cp(after)-root_cp(before)
        if abs(change-smooth)>2.000001:raise ValueError('Integer/smooth mismatch')
        observations.append(dict(sfen=before['sfen'],change=change,smooth=smooth))
    # Mirror equality and 180-degree color antisymmetry of extracted keys.
    transforms=native([transformed(s) for s in sfens]+[transformed(s,True) for s in sfens])
    for i,frame in enumerate(frames):
        if transforms[i]['features']!=frame['features']:raise ValueError('Mirror feature mismatch')
        if {tuple(x[:3]):x[3] for x in frame['features']}!={tuple(x[:3]):-x[3] for x in transforms[i+len(frames)]['features']}:raise ValueError('Color feature mismatch')
    result.update(validation=validation,initial_gradient=gradient,l2=l2,gradient_checks=checked,
        safety=dict(simultaneous_cap_l1_bound_cp=worst,all_keys_at_cap_not_guaranteed_safe=worst>10,
        numerical_perturbation_raw_abs=64,max_integer_change=max(abs(x['change']) for x in observations),observations=observations),
        symmetry_checked_positions=len(frames),zero_baselines=len(frames),zero_restored=True,closed=True)
    required=dict(plan['runtime_sha256'])
    for path in (SOURCE/'report.json',SOURCE/'audit.json',OLD/'report.json',PROBE,PROBE.parent/'build-report.json',
        Path(__file__),ROOT/'tools/learning/imitation/sparse_objective.py',ROOT/'tools/learning/native/imitation_probe.cc',
        ROOT/'tools/learning/native/learning_data_probe.cc',ROOT/'tools/learning/data/prepare_learning_data.py',
        ROOT/'tools/learning/data/prepare_refreshed_pilot.py',ROOT/'tools/learning/core/learning_backup.py',
        ROOT/'src/evaluation.cc',ROOT/'src/evaluation.h',ROOT/'src/psq.cc',ROOT/'src/psq.h',ROOT/'Makefile',
        output/'plan.json',output/'numerical-perturbation.txt'):
        required[str(path.relative_to(ROOT))]=digest(path)
    # Existing verified baseline copies cover large runtime inputs.
    covered=verify_backup(OLD/'backup/manifest.json')
    extras={k:v for k,v in required.items() if covered.get(k)!=v}
    create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras)
    result['required_sha256']=required
    write_report(output/'checkpoint-00.json',dict(updates=0,delta_cp={k:0 for k in keys},average_cp={k:0 for k in keys},
        active_keys=keys,input_sha256=SOURCE_SHA,training_enabled=False,outcome_loss_enabled=False))
    result['checkpoint_sha256']=digest(output/'checkpoint-00.json')
    result['backup_sha256']=digest(output/'backup/manifest.json')
    for name,sha in required.items():
        if digest(ROOT/name)!=sha:raise ValueError('Protected input changed')
    write_report(output/'report.json',result)
    write_report(output/'audit.json',dict(accepted=True,report_sha256=digest(output/'report.json'),updates=0,qsearch_calls=result['qsearch_calls'],
        pairs=len(result['pairs']),excluded=result['excluded'],zero_baselines=len(frames),symmetry_positions=len(frames),
        gradient_checks=len(checked),sparse_native_table_perturbation_verified=True,runtime_unchanged=True))
    print(json.dumps(dict(pairs=len(result['pairs']),excluded=result['excluded'],l2=l2,safety=result['safety']['simultaneous_cap_l1_bound_cp']),indent=2))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.output)
