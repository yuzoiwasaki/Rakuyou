#!/usr/bin/env python3
"""One fixed20-update winner-label pilot; reuse sparse updater, no searches."""
import sys,json,math,argparse
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.outcome.outcome_objective import objective,supervised
from tools.learning.imitation import sparse_updater as u
from tools.learning.imitation.sparse_objective import native,root_cp,factors,write_delta
from tools.learning.data.prepare_learning_data import ROOT,digest
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report

PREP=ROOT/'results/learning-pilot/2026-10-13-outcome-preparation-v1'
PREP_SHA='ac1edd4bbe2d15552bd980aebc05a3179174f9929b57af615ea1c3f131295d9e'
AUDIT_SHA='34af3efa9e216c9988090509fb76732fac0aee85df674a97c068ebb6980c0ee9'
PARENT=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
MARKER=PREP/'learning-attempt-v1.json'


def load():
    if digest(PREP/'report.json')!=PREP_SHA or digest(PREP/'saved-label-audit.json')!=AUDIT_SHA:raise ValueError('Outcome preparation/audit changed')
    r=json.loads((PREP/'report.json').read_bytes());a=json.loads((PREP/'saved-label-audit.json').read_bytes())
    if not a['accepted'] or a['report_sha256']!=PREP_SHA or r['updates'] or r['errors'] or not r['closed']:raise ValueError('Expected update-zero preparation')
    covered=verify_backup(PARENT/'backup/manifest.json');covered.update(verify_backup(PREP/'backup/manifest.json'))
    for n,s in r['required_sha256'].items():
        if covered.get(n)!=s or digest(ROOT/n)!=s:raise ValueError('Bound source changed: '+n)
    if digest(PREP/'checkpoint-00.json')!=r['checkpoint_sha256']:raise ValueError('Zero checkpoint changed')
    if u.restore(json.loads((PREP/'checkpoint-00.json').read_bytes()),r['binding'])!=u.initial(r['binding']['active_keys']):raise ValueError('Expected zero state')
    train=supervised([x['sample'] for x in r['records']['train']]);val=supervised([x['sample'] for x in r['records']['validation']])
    if len(train)!=96 or len(val)!=23 or sorted({k for x in train for k in x['factors']})!=r['binding']['active_keys']:raise ValueError('Fixed96/23 or train-only keys changed')
    return r


def summarize(rows):
    def group(selected):
        usable=[x for x in selected if x['use_outcome_loss']]
        if not usable:return dict(supervised=0)
        def loss(key):return objective([dict(target=x['target'],use_outcome_loss=True,base_cp=x[key],factors={}) for x in usable],{})[0]
        base=loss('base_cp');integer=loss('candidate_cp');smooth=loss('smooth_cp')
        return dict(supervised=len(usable),loss_base=base,loss_integer=integer,loss_smooth=smooth,
            relative_integer_improvement=(base-integer)/base,relative_smooth_improvement=(base-smooth)/base,
            integer_changed=sum(x['change']!=0 for x in usable),
            outcome_direction_improved=sum(x['change']*(1 if x['target']==1 else -1)>0 for x in usable),
            outcome_direction_worsened=sum(x['change']*(1 if x['target']==1 else -1)<0 for x in usable))
    def impact(selected):
        return dict(positions=len(selected),changed=sum(x['change']!=0 for x in selected),
            max_integer_change=max(abs(x['change']) for x in selected) if selected else 0,
            max_smooth_change=max(abs(x['smooth_cp']-x['base_cp']) for x in selected) if selected else 0,
            mean_cp_change=math.fsum(x['change'] for x in selected)/len(selected) if selected else 0)
    draw=[x for x in rows if not x['use_outcome_loss']]
    return dict(all=group(rows),side={s:group([x for x in rows if x['side']==s]) for s in ('black','white')},
        result={label:group([x for x in rows if x['target']==target]) for label,target in [('win',1),('loss',0)]},
        draw=dict(all=impact(draw),side={s:impact([x for x in draw if x['side']==s]) for s in ('black','white')}),
        whole=impact(rows))


def evaluate(prep,delta,path):
    raw={k:math.trunc(v*65536) for k,v in delta.items()}
    if any(abs(v)>655 for v in raw.values()):raise ValueError('Authorized coefficient cap exceeded')
    write_delta(path,raw);records=[x for rows in prep['records'].values() for x in rows]
    after=native([x['features']['sfen'] for x in records],path);observations={s:[] for s in prep['records']}
    for r,candidate in zip(records,after):
        before=r['features'];side=r['row']['side_to_move'];expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
        if before['features']!=candidate['features'] or before['progress']!=candidate['progress']:raise ValueError('Feature/progress changed')
        for t,a,b,count in before['features']:
            for lane in ((0,1,2) if t==0 else (0,2)):expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
        for mode in ('on_parts','off_parts'):
            if before[mode]['tempo']!=candidate[mode]['tempo']:raise ValueError('Tempo changed')
            for part in ('kp','others'):
                if [candidate[mode][part][l]-before[mode][part][l] for l in range(4)]!=expected[part]:raise ValueError('Protected/canonical table mismatch')
        base=root_cp(before,side);score=root_cp(candidate,side);fs=factors(before,side)
        smooth=base+math.fsum(v*delta.get(k,0) for k,v in fs.items())
        raw_smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in fs.items())
        if abs(score-base)>10 or abs(score-base-raw_smooth)>2.000001:raise ValueError('Position bound/rounding mismatch')
        observations[r['row']['split']].append(dict(id=r['id'],side=side,target=r['target'],use_outcome_loss=r['use_outcome_loss'],
            kind=r['kind'],base_cp=base,candidate_cp=score,smooth_cp=smooth,change=score-base,raw_smooth_change=raw_smooth))
    return dict(observations=observations,summary={s:summarize(rows) for s,rows in observations.items()})


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Outcome learning already started/closed')
    prep=load();keys=prep['binding']['active_keys'];output.mkdir(parents=True,exist_ok=False)
    plan=dict(preparation_sha256=PREP_SHA,audit_sha256=AUDIT_SHA,config=u.CONFIG,full_batch_supervised=96,
        target='verified decisive winner relative to Shin root side',draw_loss_enabled=False,
        selected_update=20,selection='fixed20 averaged candidate, no reselection',max_position_cp_change=10,
        training_enabled=True,deployment_enabled=False)
    write_report(output/'plan.json',plan)
    with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json'),max_updates=20),f)
    required=dict(prep['required_sha256']);paths=[PREP/'report.json',PREP/'saved-label-audit.json',PREP/'checkpoint-00.json',
        Path(__file__),ROOT/'test/learning/outcome/test_outcome_pilot.py',output/'plan.json',MARKER]
    extras={str(p.relative_to(ROOT)):digest(p) for p in paths};create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras);required.update(extras)
    binding=dict(plan_sha256=digest(output/'plan.json'),required_sha256=required)
    report=dict(plan=plan,binding=binding,updates=0,trajectory=[],saved=[],selected_update=20,errors=[],closed=False,
        deployed=False,searches=0,qsearch_calls=0,backup_sha256=digest(output/'backup/manifest.json'))
    state=u.initial(keys);train=[r['sample'] for r in prep['records']['train']]
    def save():
        avg=u.average(state);cp=output/f'checkpoint-{state["updates"]:02d}.json';write_report(cp,u.checkpoint(state,binding))
        if u.restore(json.loads(cp.read_bytes()),binding)!=state:raise ValueError('Checkpoint mismatch')
        result=evaluate(prep,avg,output/f'average-{state["updates"]:02d}.txt')
        if state['updates']==0 and any(x['change'] for rows in result['observations'].values() for x in rows):raise ValueError('Zero baseline mismatch')
        result.update(update=state['updates'],max_abs_average=max(abs(x) for x in avg.values()),max_abs_current=max(abs(x) for x in state['delta'].values()),
            current_cap_hits=sum(abs(x)>=.01-1e-12 for x in state['delta'].values()),
            checkpoint_sha256=digest(cp),sidecar_sha256=digest(output/f'average-{state["updates"]:02d}.txt'))
        report['saved'].append(result);write_report(output/'report.json',report)
    try:
        save()
        while state['updates']<20:
            loss,g=objective(train,state['delta'],1e-6);state=u.step(state,g)
            report['updates']=state['updates'];report['trajectory'].append(dict(update=state['updates'],loss=loss,gradient=g,state=state))
            if state['updates'] in (5,10,20):save()
        load();verify_backup(output/'backup/manifest.json',extras)
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        report['closed']=True
    except Exception as e:report['errors'].append(str(e));report['closed']=True;raise
    finally:write_report(output/'report.json',report)
    print(json.dumps(dict(updates=20,summary=report['saved'][-1]['summary']),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();run(a.output)
