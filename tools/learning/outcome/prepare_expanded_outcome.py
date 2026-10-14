#!/usr/bin/env python3
"""Connect accepted383/80 roots and six old White draws; audit update zero only."""
import sys,json,argparse,math
from pathlib import Path
from collections import Counter
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,digest,validate_game,outcome
from tools.learning.imitation.sparse_objective import native,factors,root_cp,write_delta,PROBE
from tools.learning.imitation import sparse_updater as updater
from tools.learning.outcome.outcome_objective import objective
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report

PARENT=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
PARENT_SHA='060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4'
BASE=ROOT/'results/learning-pilot/2026-10-11-preparation-v2/manifest.json'
BASE_SHA='44704fc910fc3217a55399951d6a60ab233a49b80b0a017695e7672627954792'


SELECTION=ROOT/'results/learning-pilot/2026-10-13-outcome-expansion-selection-v1'
SELECTION_SHA='68a62bb9ba5a4abaad369ab230c9c0ee63ff93d69afa6c3c330d5c1f28fd067b'
OLD_OUTCOME=ROOT/'results/learning-pilot/2026-10-13-outcome-preparation-v1/report.json'
OLD_OUTCOME_SHA='ac1edd4bbe2d15552bd980aebc05a3179174f9929b57af615ea1c3f131295d9e'


def load():
    if digest(SELECTION/'manifest.json')!=SELECTION_SHA or digest(OLD_OUTCOME)!=OLD_OUTCOME_SHA:
        raise ValueError('Expanded selection/old diagnostic changed')
    if digest(BASE)!=BASE_SHA or digest(PARENT/'report.json')!=PARENT_SHA:
        raise ValueError('Original baseline changed')
    selection=json.loads((SELECTION/'manifest.json').read_bytes())
    audit=json.loads((SELECTION/'audit.json').read_bytes())
    if (not audit['accepted'] or audit['manifest_sha256']!=SELECTION_SHA or selection['updates']
        or selection['searches'] or selection['selection_complete']
        or {s:(v['roots'],v['supervised']) for s,v in selection['summary'].items()}!={'train':(383,256),'validation':(80,64)}):
        raise ValueError('Expected accepted partial383/80 selection')
    base_parent=json.loads((PARENT/'report.json').read_bytes());m=json.loads(BASE.read_bytes())
    required=dict(base_parent['binding']['required_sha256']);required.update(selection['required_sha256'])
    required[str((SELECTION/'manifest.json').relative_to(ROOT))]=SELECTION_SHA
    required[str((SELECTION/'audit.json').relative_to(ROOT))]=digest(SELECTION/'audit.json')
    required[str(OLD_OUTCOME.relative_to(ROOT))]=OLD_OUTCOME_SHA
    verify_backup(PARENT/'backup/manifest.json');verify_backup(SELECTION/'backup/manifest.json')
    for n,sha in required.items():
        if digest(ROOT/n)!=sha:raise ValueError('Bound selection input changed: '+n)
    native_by_id={x['id']:x['root'] for x in selection['native_checks']}
    records={}
    for split in ('train','validation'):
        path=SELECTION/(split+'.roots.json')
        rows=json.loads(path.read_bytes())['records']
        if len(rows)!=selection['summary'][split]['roots']:raise ValueError('Expanded membership changed')
        records[split]=[dict(row=r,root=native_by_id[r['id']]) for r in rows]
    old=json.loads(OLD_OUTCOME.read_bytes())
    diagnostic=[x for x in old['records']['validation'] if x['row']['side_to_move']=='white' and not x['use_outcome_loss']]
    if len(diagnostic)!=6:raise ValueError('Expected six old White draws')
    records['diagnostic']=[dict(row={**x['row'],'split':'diagnostic'},root=x['baseline']) for x in diagnostic]
    new_games={(x['row']['source']['run'],x['row']['source']['game']) for rows in records.values() for x in rows if x['row']['split']!='diagnostic'}
    if any((x['row']['source']['run'],x['row']['source']['game']) in new_games for x in records['diagnostic']):
        raise ValueError('Old diagnostic mixed into new dataset')
    return dict(records=records,binding={'required_sha256':required}),m


def prepare(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    parent,manifest=load();cache={};records={};source_sha={}
    for split,old_rows in parent['records'].items():
        records[split]=[]
        for old in old_rows:
            row=old['row'];src=row['source'];name=src['path']
            if manifest['run_assignments'][src['run']]!=('validation' if split=='diagnostic' else split):raise ValueError('Existing split changed')
            if name not in cache:
                if digest(ROOT/name)!=src['sha256']:raise ValueError('Raw game changed')
                cache[name]=json.loads((ROOT/name).read_bytes());source_sha[name]=src['sha256']
            doc=cache[name];game=doc['games'][src['game']-1];validate_game(game,doc['settings'])
            if game['moves'][:src['ply']-1]!=row['moves_before'] or game[row['side_to_move']]!='shin_yonenaga':raise ValueError('Game identity/Shin side changed')
            label=outcome(game,row['side_to_move'])
            records[split].append(dict(id=row['id'],row=row,baseline=old['root'],kind=label['kind'],target=label['target'],
                use_outcome_loss=label['use_outcome_loss'],termination=game['reason'],result=game['result']))
        if len({(r['row']['source']['run'],r['row']['source']['game']) for r in records[split]})!=len(records[split]):raise ValueError('More than one root per game')
    if {r['row']['source']['run'] for r in records['train']}&{r['row']['source']['run'] for r in records['validation']}:raise ValueError('Run overlap')
    frames=native([r['baseline']['sfen'] for rows in records.values() for r in rows]);cursor=0
    for rows in records.values():
        for r in rows:
            frame=frames[cursor];cursor+=1
            if any(r['baseline'][k]!=frame[k] for k in ('sfen','eval_on','eval_off','progress','on_parts','off_parts')):raise ValueError('Zero baseline mismatch')
            r['features']=frame
            r['sample']=dict(target=r['target'],use_outcome_loss=r['use_outcome_loss'],
                base_cp=root_cp(frame,r['row']['side_to_move']),factors=factors(frame,r['row']['side_to_move']))
    train=[r['sample'] for r in records['train']]
    keys=sorted({k for r in train if r['use_outcome_loss'] for k in r['factors']})
    loss,g=objective(train,{},1e-6)
    ratios=sorted(1e-8/abs(g.get(k,0)) for k in keys if g.get(k))
    scale=dict(train_only=True,l2=1e-6,cap_cp=.01,active_parameters=len(keys),initial_train_loss=loss,
        nonzero_gradients=len(ratios),zero_gradients=len(keys)-len(ratios),ratio_median=ratios[(len(ratios)-1)//2],
        ratio_p90=ratios[int((len(ratios)-1)*.9)],ratio_above_25percent=sum(x>.25 for x in ratios))
    checks=[]
    for k in sorted(keys,key=lambda k:-abs(g.get(k,0)))[:10]:
        h=.001;a,_=objective(train,{k:h},1e-6);b,_=objective(train,{k:-h},1e-6);error=abs((a-b)/(2*h)-g.get(k,0))
        if error>1e-9:raise ValueError('Outcome gradient mismatch')
        checks.append(dict(key=k,error=error))
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(schema='rakuyou-outcome-pilot-plan-v1',source='accepted383/80 roots; separate old White draw6 diagnostic',loss='mean decisive-game logistic cross entropy; sigmoid(cp/600)',
        sample_weight='one root per game, equal selected-game weight; not population win-rate calibration',
        draw_policy='max_plies unknown; no outcome gradient or train keys; keep side/draw impact diagnostics',
        config=updater.CONFIG,training_enabled=False,deployment_enabled=False,searches_enabled=False,
        max_position_cp_change=10,initial='operational baseline plus zero KP/PP delta',selected_update=20,
        historical_game_runtime_provenance='not verified',validation='reused diagnostic split, not unseen strength test')
    write_report(output/'plan.json',plan)
    raw={k:(1 if g.get(k,0)<0 else -1)*655 for k in keys};write_delta(output/'cap-audit.txt',raw)
    after=native([f['sfen'] for f in frames],output/'cap-audit.txt');observations=[]
    all_records=[r for rows in records.values() for r in rows]
    for before,candidate,r in zip(frames,after,all_records):
        if before['features']!=candidate['features'] or before['progress']!=candidate['progress']:raise ValueError('Features/progress changed')
        expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
        for t,a,b,count in before['features']:
            for lane in ((0,1,2) if t==0 else (0,2)):expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
        for mode in ('on_parts','off_parts'):
            if before[mode]['tempo']!=candidate[mode]['tempo']:raise ValueError('Tempo changed')
            for part in ('kp','others'):
                if [candidate[mode][part][l]-before[mode][part][l] for l in range(4)]!=expected[part]:raise ValueError('Protected/canonical table mismatch')
        side=r['row']['side_to_move'];change=root_cp(candidate,side)-root_cp(before,side)
        smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in factors(before,side).items())
        if abs(change)>10 or abs(change-smooth)>2.000001:raise ValueError('Position difference bound')
        observations.append(dict(id=r['id'],split=r['row']['split'],side=side,kind=r['kind'],change=change,smooth=smooth))
    binding=dict(parent_sha256=PARENT_SHA,split_manifest_sha256=BASE_SHA,active_keys=keys,plan_sha256=digest(output/'plan.json'))
    state=updater.initial(keys);write_report(output/'checkpoint-00.json',updater.checkpoint(state,binding))
    if updater.restore(json.loads((output/'checkpoint-00.json').read_bytes()),binding)!=state:raise ValueError('Zero checkpoint mismatch')
    required=dict(parent['binding']['required_sha256']);required.update(source_sha)
    for path in [PARENT/'report.json',BASE,Path(__file__),ROOT/'tools/learning/outcome/outcome_objective.py',
        ROOT/'tools/learning/imitation/sparse_objective.py',ROOT/'tools/learning/imitation/sparse_updater.py',PROBE,
        ROOT/'test/learning/outcome/test_outcome_objective.py',ROOT/'test/learning/outcome/test_prepare_expanded_outcome.py',output/'plan.json',output/'cap-audit.txt']:
        required[str(path.relative_to(ROOT))]=digest(path)
    covered=verify_backup(PARENT/'backup/manifest.json');covered.update(verify_backup(SELECTION/'backup/manifest.json'));extras={n:s for n,s in required.items() if covered.get(n)!=s}
    create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras)
    summary={s:dict(roots=len(rows),supervised=sum(r['use_outcome_loss'] for r in rows),masked=sum(not r['use_outcome_loss'] for r in rows),
        strata=dict(Counter(r['row']['stratum'] for r in rows)),labels=dict(Counter('win' if r['target']==1 else 'loss' if r['target']==0 else 'masked' for r in rows))) for s,rows in records.items()}
    report=dict(plan=plan,records=records,summary=summary,scale=scale,gradient_checks=checks,cap_observations=observations,
        binding=binding,required_sha256=required,checkpoint_sha256=digest(output/'checkpoint-00.json'),backup_sha256=digest(output/'backup/manifest.json'),
        updates=0,searches=0,qsearch_calls=0,deployed=False,validation_quality_measured=False,errors=[],closed=True)
    for n,s in required.items():
        if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
    write_report(output/'report.json',report);write_report(output/'audit.json',dict(accepted=True,report_sha256=digest(output/'report.json'),
        outcome_records_verified=469,zero_positions=469,gradient_checks=10,updates=0,searches=0,no_test_games_read=True,runtime_unchanged=True))
    print(json.dumps(dict(summary=summary,scale=scale,max_cap_change=max(abs(x['change']) for x in observations)),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.output)
