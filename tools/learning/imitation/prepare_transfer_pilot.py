#!/usr/bin/env python3
"""Fixed12/12 game-split baseline comparisons and leaves; update zero only."""
import sys,json,math,argparse
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,Probe,digest
from tools.learning.data.refresh_teachers import RecordedEngine,classify,RUNTIME_MANIFEST
from tools.learning.tempo.run_tempo_search import PREPARATION_SHA,write_report
from tools.learning.data.prepare_refreshed_pilot import frozen_record
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.imitation import sparse_updater as updater
from tools.learning.imitation.sparse_objective import native,objective,pair_record,factors,root_cp,write_delta,PROBE

PREP=ROOT/'results/learning-pilot/2026-10-12-game-split-imitation-roots-v1'
PREP_SHA='95eb72a4849025fcf7498c7b751b3c3d387c86cc3bfb0ef82ace7730dd67bc67'
PREP_AUDIT_SHA='c16cd92136a6047244a5e0bbf2a0de629265c49e76b2a000161e959fdcaac817'
PRIOR=ROOT/'results/learning-pilot/2026-10-12-historical-move-comparison-v1/report.json'
PRIOR_SHA='d7825b838e41f8f544107874ef6571e6c1e65cfae250274b0c19d013dcd9dacd'
OLD=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
OLD_SHA='060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4'
MARKER=PREP/'transfer-preparation-attempt-v1.json'


def load():
    for path,sha in [(PREP/'manifest.json',PREP_SHA),(PREP/'audit.json',PREP_AUDIT_SHA),(PRIOR,PRIOR_SHA),(OLD/'report.json',OLD_SHA)]:
        if digest(path)!=sha:raise ValueError('Bound preparation input changed')
    m=json.loads((PREP/'manifest.json').read_bytes());audit=json.loads((PREP/'audit.json').read_bytes())
    if not audit['accepted'] or audit['manifest_sha256']!=PREP_SHA or m['excluded'] or m['updates']:raise ValueError('Expected audited12/12 roots')
    for n,s in m['required_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Root preparation binding changed: '+n)
    verify_backup(PREP/'backup/manifest.json');verify_backup(OLD/'backup/manifest.json')
    if digest(RUNTIME_MANIFEST)!=PREPARATION_SHA:raise ValueError('Isolated baseline manifest changed')
    rm=json.loads(RUNTIME_MANIFEST.read_bytes())
    for e in rm['files']:
        if e['variant']=='baseline' and digest(RUNTIME_MANIFEST.parent/e['path'])!=e['sha256']:raise ValueError('Baseline copy changed')
    previous=json.loads(PRIOR.read_bytes())
    reuse={}
    probe=Probe(ROOT/'results/learning-tools/learning-data-probe')
    try:
        for split in ('train','validation'):
            if len(m['accepted'][split])!=12:raise ValueError('Fixed roots changed')
            for row in m['accepted'][split]:
                if row['id'] not in m['reusable_baseline_comparison_ids']:continue
                entries=[x for x in previous['records'] if x['row']['id']==row['id']]
                if len(entries)!=2:raise ValueError('Reuse incomplete; no automatic replacement')
                for x in entries:
                    if x['row']['moves_before']!=row['moves_before'] or x['row']['actual_move']!=row['actual_move']:raise ValueError('Reuse history changed')
                    cp,reason=classify(x['result'],row,probe)
                    if cp!=x['cp'] or reason!=x['excluded'] or reason is not None:raise ValueError('Reuse provenance changed')
                reuse[row['id']]=entries
    finally:probe.close()
    return m,reuse


def prepare(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Transfer preparation already started/closed')
    m,reuse=load();output.mkdir(parents=True,exist_ok=False)
    plan=dict(preparation_sha256=PREP_SHA,train_ids=[x['id'] for x in m['accepted']['train']],
        validation_ids=[x['id'] for x in m['accepted']['validation']],depth=15,threads=1,hash_mb=64,
        shin=True,own_book=False,timeout_seconds=30,max_new_searches=42,max_qsearch_calls=48,
        max_updates=20,per_key_cap_cp=.01,max_position_cp_change=10,outcome_loss_enabled=False,
        training_enabled=False,deployment_enabled=False,retries=0,refill=False,
        runtime_sha256=m['plan']['runtime_sha256'],prospect='decide adoption/deeper investigation from final evidence, not automatic hold or expansion')
    write_report(output/'plan.json',plan)
    with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json')),f)
    r=dict(plan=plan,comparisons=[],pairs={'train':[],'validation':[]},excluded=[],same_moves=[],
        new_searches=0,reused_searches=0,qsearch_calls=0,updates=0,errors=[],closed=False)
    path=output/'report.json';write_report(path,r)
    legal=Probe(ROOT/'results/learning-tools/learning-data-probe')
    q=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',qsearch_progress=ROOT/'bin/progress.bin')
    static=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',details=True)
    try:
        for split in ('train','validation'):
            for row in m['accepted'][split]:
                entries=[]
                for variant in ('unrestricted','forced-actual'):
                    if row['id'] in reuse:
                        old=next(x for x in reuse[row['id']] if x['variant']==variant)
                        entry={**old,'row':row,'reused':True,'reuse_report_sha256':PRIOR_SHA};r['reused_searches']+=1
                    else:
                        print(row['id'],variant,flush=True)
                        e=RecordedEngine(RUNTIME_MANIFEST.parent/'baseline/bin/release')
                        try:
                            if any('error' in l.lower() or 'failed' in l.lower() for l in e.transcript):raise ValueError('Engine load error')
                            if r['new_searches']>=42:raise ValueError('Search cap')
                            r['new_searches']+=1;write_report(path,r)
                            result=e.analyze(row['moves_before'],15,30,searchmoves=[row['actual_move']] if variant=='forced-actual' else None)
                            cp,reason=classify(result,row,legal)
                            if variant=='forced-actual' and reason is None and result['bestmove']!=row['actual_move']:raise ValueError('Forced move mismatch')
                        finally:e.close()
                        entry=dict(row=row,variant=variant,result=result,cp=cp,excluded=reason,commands=e.commands,transcript=e.transcript,reused=False)
                    entries.append(entry);r['comparisons'].append(entry);write_report(path,r)
                reasons=[dict(variant=x['variant'],reason=x['excluded']) for x in entries if x['excluded']]
                if reasons:r['excluded'].append(dict(id=row['id'],split=split,stage='comparison',reasons=reasons));continue
                if entries[0]['result']['bestmove']==row['actual_move']:
                    r['same_moves'].append(dict(id=row['id'],split=split));continue
                pair=dict(id=row['id'],row=row,branches={});reasons=[]
                for label,entry in (('actual',entries[1]),('alternative',entries[0])):
                    moves=row['moves_before']+entry['result']['candidates'][0]['pv']
                    if r['qsearch_calls']>=48:raise ValueError('Qsearch cap')
                    frame=q.replay(moves);r['qsearch_calls']+=1
                    replay=static.replay(moves)
                    if not replay.get('ok'):raise ValueError('Saved comparison PV illegal')
                    terminal=replay['positions'][-1]
                    dummy=dict(sfen=terminal['sfen'],side_to_move='black' if len(moves)%2==0 else 'white',teacher_cp=0)
                    _,reason=frozen_record(dummy,frame)
                    full=moves+(frame.get('pv') or []);replay=static.replay(full)
                    if not replay.get('ok'):raise ValueError('Leaf PV illegal')
                    if any(x['occurrences']>1 for x in replay['positions']):reason=reason or 'repeated_history'
                    if reason:reasons.append(dict(branch=label,reason=reason))
                    pair['branches'][label]=dict(moves=full,qsearch=frame,baseline=replay['positions'][-1],excluded=reason)
                if reasons:r['excluded'].append(dict(id=row['id'],split=split,stage='leaf',reasons=reasons))
                else:r['pairs'][split].append(pair)
                write_report(path,r)
        if not r['pairs']['train'] or not r['pairs']['validation']:raise ValueError('No usable train/validation pairs; do not refill')
        old=json.loads((OLD/'report.json').read_bytes())
        diagnostic=[dict(row=x['row'],features=x['leaf']) for x in old['records']['validation']]
        points=[]
        for split,rows in r['pairs'].items():
            for pair in rows:
                for label,b in pair['branches'].items():points.append(dict(id=pair['id']+':'+label,kind=split+'_leaf',root_side='white',baseline=b['baseline']))
        for split in ('train','validation'):
            for check in m['native_checks']:
                if check['id'] in plan[split+'_ids']:points.append(dict(id=check['id']+':root',kind=split+'_root',root_side='white',baseline=check['root']))
        for x in old['records']['validation']:
            for location in ('root','leaf'):points.append(dict(id=x['row']['id']+':'+location,kind='diagnostic_'+location,
                root_side=x['row']['side_to_move'],stratum=x['row']['stratum'],teacher_cp=x['row']['teacher_cp'],baseline=x[location]))
        frames=native([x['baseline']['sfen'] for x in points])
        lookup={}
        for point,f in zip(points,frames):
            before=point['baseline']
            if any(before[k]!=f[k] for k in ('sfen','eval_on','eval_off','progress','on_parts','off_parts')):raise ValueError('Zero baseline mismatch')
            point['features']=f;lookup[point['id']]=f
        for split,rows in r['pairs'].items():
            for pair in rows:
                for label,b in pair['branches'].items():b['features']=lookup[pair['id']+':'+label]
                pair['sample']=pair_record(pair['branches']['actual']['features'],pair['branches']['alternative']['features'])
        train_samples=[p['sample'] for p in r['pairs']['train']]
        keys=sorted({k for p in train_samples for k in p['factors']})
        loss,g=objective(train_samples,{})
        ratios=sorted(1e-8/abs(g[k]) for k in keys if g.get(k))
        scale=dict(l2=1e-6,cap_cp=.01,train_only=True,active_parameters=len(keys),initial_train_loss=loss,
            nonzero_gradients=sum(bool(g.get(k)) for k in keys),zero_gradients=sum(not g.get(k) for k in keys),
            cap_gradient_ratio_median=ratios[(len(ratios)-1)//2],cap_gradient_ratio_p90=ratios[int((len(ratios)-1)*.9)],
            cap_gradient_ratio_max=max(ratios),above_25percent=sum(x>.25 for x in ratios))
        checked=[]
        for k in sorted(keys,key=lambda k:-abs(g.get(k,0)))[:10]:
            h=.001;a,_=objective(train_samples,{k:h},1e-6);b,_=objective(train_samples,{k:-h},1e-6)
            error=abs((a-b)/(2*h)-g.get(k,0))
            if error>1e-9:raise ValueError('Gradient mismatch')
            checked.append(dict(key=k,error=error))
        # Cross-game leaf overlap is a blocker to discuss, never refill.
        train_leafs={' '.join(b['features']['sfen'].split()[:3]) for p in r['pairs']['train'] for b in p['branches'].values()}
        val_leafs={' '.join(b['features']['sfen'].split()[:3]) for p in r['pairs']['validation'] for b in p['branches'].values()}
        overlap=len(train_leafs&val_leafs)
        raw={k:(1 if g.get(k,0)<0 else -1)*655 for k in keys}
        write_delta(output/'cap-audit.txt',raw)
        after=native([f['sfen'] for f in frames],output/'cap-audit.txt');cap_obs=[]
        for before,changed,point in zip(frames,after,points):
            if before['features']!=changed['features'] or before['progress']!=changed['progress']:raise ValueError('Key/progress changed')
            expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
            for t,a,b,count in before['features']:
                for lane in ((0,1,2) if t==0 else (0,2)):
                    expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
            for mode in ('on_parts','off_parts'):
                if before[mode]['tempo']!=changed[mode]['tempo']:raise ValueError('Tempo changed')
                for part in ('kp','others'):
                    if [changed[mode][part][l]-before[mode][part][l] for l in range(4)]!=expected[part]:raise ValueError('Native canonical packed mismatch')
            side=point['root_side'];delta=root_cp(changed,side)-root_cp(before,side)
            smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in factors(before,side).items())
            if abs(delta)>10 or abs(delta-smooth)>2.000001:raise ValueError('Position bound')
            cap_obs.append(dict(id=point['id'],change=delta,smooth=smooth))
        r.update(locations=points,active_keys=keys,initial_gradient=g,scale=scale,gradient_checks=checked,
            cross_game_leaf_overlap=overlap,cap_observations=cap_obs,
            validation_quality_measured=False,ready_for_training=overlap==0 and scale['cap_gradient_ratio_p90']<=.25)
        required=dict(m['required_sha256'])
        for path_ in [PREP/'manifest.json',PREP/'audit.json',PRIOR,OLD/'report.json',Path(__file__),
            ROOT/'tools/learning/imitation/sparse_objective.py',ROOT/'tools/learning/imitation/sparse_updater.py',
            ROOT/'test/learning/imitation/test_prepare_transfer_pilot.py',PROBE,PROBE.parent/'build-report.json',output/'plan.json',output/'cap-audit.txt']:
            required[str(path_.relative_to(ROOT))]=digest(path_)
        covered=verify_backup(OLD/'backup/manifest.json');covered.update(verify_backup(PREP/'backup/manifest.json'))
        extras={n:s for n,s in required.items() if covered.get(n)!=s}
        create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras)
        r['required_sha256']=required;r['backup_sha256']=digest(output/'backup/manifest.json')
        write_report(output/'checkpoint-00.json',updater.checkpoint(updater.initial(keys),dict(preparation_sha256=PREP_SHA,active_keys=keys)))
        r['checkpoint_sha256']=digest(output/'checkpoint-00.json')
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        r['closed']=True
    except Exception as e:r['errors'].append(str(e));r['closed']=True;raise
    finally:
        legal.close();q.close();static.close();write_report(path,r)
    write_report(output/'audit.json',dict(accepted=True,report_sha256=digest(path),new_searches=r['new_searches'],reused_searches=r['reused_searches'],
        qsearch_calls=r['qsearch_calls'],pairs={s:len(p) for s,p in r['pairs'].items()},excluded=r['excluded'],same_moves=r['same_moves'],
        cross_game_leaf_overlap=r['cross_game_leaf_overlap'],zero_positions=len(r['locations']),updates=0,runtime_unchanged=True))
    print(json.dumps(dict(pairs={s:len(p) for s,p in r['pairs'].items()},excluded=r['excluded'],same_moves=r['same_moves'],scale=r['scale']),indent=2));return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
