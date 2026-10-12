#!/usr/bin/env python3
"""One20 full-batch transfer run:prematch4 train,Denousen4 validation; no searches."""
import sys,json,argparse,math
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.imitation import sparse_updater as u,imitation_pilot as shared
from tools.learning.imitation.sparse_objective import objective
from tools.learning.data.prepare_learning_data import ROOT,digest
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report

PREP=ROOT/'results/learning-pilot/2026-10-13-imitation-transfer-static-audit-v1'
SHA='392ea00497689cbe0ecc917f0ff9cbdb7a6558f459129311fc72de61353bbcce'
AUDIT_SHA='d9a530d959b8b4d755a81cec8b753412d61f2333c869ce22c679efb1952e2df4'
MARKER=PREP/'learning-attempt-v1.json'


def load():
    if digest(PREP/'report.json')!=SHA or digest(PREP/'audit.json')!=AUDIT_SHA:raise ValueError('Transfer preparation changed')
    r=json.loads((PREP/'report.json').read_bytes());a=json.loads((PREP/'audit.json').read_bytes())
    if not a['accepted'] or a['report_sha256']!=SHA or r['updates'] or r['errors'] or r['cross_game_leaf_overlap'] or {s:len(x) for s,x in r['pairs'].items()}!={'train':4,'validation':4}:
        raise ValueError('Expected audited4/4')
    if r['source_errors']!=['Forced move mismatch'] or r['incomplete_response_records']!=1:
        raise ValueError('Unexpected source provenance')
    if any(p['id']=='historical:2:112' for rows in r['pairs'].values() for p in rows):raise ValueError('Incomplete terminal used')
    for n,s in r['required_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Bound source changed: '+n)
    verify_backup(PREP/'backup/manifest.json')
    if sorted({k for p in r['pairs']['train'] for k in p['sample']['factors']})!=r['active_keys']:raise ValueError('Validation contributed keys')
    return r


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Transfer learning already started/closed')
    prep=load();keys=prep['active_keys'];flat=prep['pairs']['train']+prep['pairs']['validation']
    synthetic=dict(pairs=flat)
    points=[]
    for p in prep['locations']:
        point={k:v for k,v in p.items() if k not in ('baseline','features')};point['baseline']=p['features']
        if point['kind'] in ('train_leaf','validation_leaf'):point['kind']='pair_leaf'
        elif point['kind']=='diagnostic_leaf':point['kind']='validation_leaf'
        elif point['kind']=='diagnostic_root':point['kind']='validation_root'
        points.append(point)
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(preparation_sha256=SHA,audit_sha256=AUDIT_SHA,config=u.CONFIG,train_ids=[p['id'] for p in prep['pairs']['train']],
        validation_ids=[p['id'] for p in prep['pairs']['validation']],selection='fixed20 averaged candidate',outcome_loss_enabled=False,
        training_enabled=True,deployment_enabled=False,max_position_cp_change=10,missing_terminal_excluded=True,
        adoption='final decision from evidence; not automatic',further_investigation='consider only from final evidence; no automatic tuning')
    write_report(output/'plan.json',plan);write_report(output/'baseline-locations.json',points)
    with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json'),max_updates=20),f)
    required=dict(prep['required_sha256'])
    paths=[PREP/'report.json',PREP/'audit.json',Path(__file__),ROOT/'tools/learning/imitation/imitation_pilot.py',ROOT/'tools/learning/imitation/sparse_updater.py',
        ROOT/'test/learning/imitation/test_transfer_pilot.py',output/'plan.json',output/'baseline-locations.json',MARKER]
    extras={str(p.relative_to(ROOT)):digest(p) for p in paths};create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras);required.update(extras)
    binding=dict(plan_sha256=digest(output/'plan.json'),required_sha256=required)
    r=dict(plan=plan,binding=binding,updates=0,trajectory=[],saved=[],selected_update=20,errors=[],closed=False,searches=0,qsearch_calls=0,deployed=False,backup_sha256=digest(output/'backup/manifest.json'))
    state=u.initial(keys);train=[p['sample'] for p in prep['pairs']['train']]
    def save():
        avg=u.average(state);values=shared.evaluate(synthetic,points,avg,output/f'average-{state["updates"]:02d}.txt')
        groups={}
        for split,samples in prep['pairs'].items():
            base,_=objective([x['sample'] for x in samples],{},0);smooth,_=objective([x['sample'] for x in samples],avg,0)
            rows=[x for x in values['pairs'] if x['id'] in {p['id'] for p in samples}]
            integer,_=objective([dict(base_gap=x['gap'],factors={}) for x in rows],{})
            groups[split]=dict(pairs=len(rows),loss_base=base,loss_integer=integer,loss_smooth=smooth,
                relative_integer_improvement=(base-integer)/base,relative_smooth_improvement=(base-smooth)/base,
                pair_gaps=rows)
        values['transfer']=groups
        cp=output/f'checkpoint-{state["updates"]:02d}.json';write_report(cp,u.checkpoint(state,binding))
        if u.restore(json.loads(cp.read_bytes()),binding)!=state:raise ValueError('Checkpoint mismatch')
        values.update(update=state['updates'],checkpoint_sha256=digest(cp),sidecar_sha256=digest(output/f'average-{state["updates"]:02d}.txt'),
            max_abs_average=max(abs(x) for x in avg.values()),max_abs_current=max(abs(x) for x in state['delta'].values()),
            current_cap_hits=sum(abs(x)>=.01-1e-12 for x in state['delta'].values()))
        r['saved'].append(values);write_report(output/'report.json',r)
    try:
        save()
        while state['updates']<20:
            loss,g=objective(train,state['delta'],1e-6);state=u.step(state,g)
            r['updates']=state['updates'];r['trajectory'].append(dict(update=state['updates'],loss=loss,gradient=g,state=state))
            if state['updates'] in (5,10,20):save()
        load();verify_backup(output/'backup/manifest.json',extras)
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        r['closed']=True
    except Exception as e:r['errors'].append(str(e));r['closed']=True;raise
    finally:write_report(output/'report.json',r)
    print(json.dumps(dict(updates=20,transfer=r['saved'][-1]['transfer'],diagnostic=r['saved'][-1]['validation'],max_change=r['saved'][-1]['max_integer_change']),indent=2));return r

if __name__=='__main__':run(Path(sys.argv[1]))
