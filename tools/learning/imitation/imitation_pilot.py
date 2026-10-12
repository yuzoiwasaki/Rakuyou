#!/usr/bin/env python3
"""One fixed twenty-update sparse imitation pilot; static evaluation only."""
import sys,json,math,argparse
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.imitation import sparse_updater as updater
from tools.learning.imitation.sparse_objective import native,objective,factors,root_cp,write_delta,PROBE
from tools.learning.imitation.prepare_imitation import OLD
from tools.learning.data.prepare_learning_data import ROOT,digest
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.core.king_safety_objective import sigmoid,GAIN
from tools.learning.tempo.run_tempo_search import write_report

PREP=ROOT/'results/learning-pilot/2026-10-12-imitation-preparation-v1'
PREP_SHA='c119a11de5a9b53655c0396ade1deb3da5d0491516710675b2f822da9f22cc96'
AUDIT_SHA='4a701a83029fc3d5ec63c4d1c7814b3e1e6ef767bdddc808ab3b61b85bd45116'
MARKER=PREP/'learning-attempt-v1.json'


def verify_inputs():
    if digest(PREP/'report.json')!=PREP_SHA or digest(PREP/'saved-results-audit.json')!=AUDIT_SHA:raise ValueError('Preparation/audit changed')
    prep=json.loads((PREP/'report.json').read_bytes());audit=json.loads((PREP/'saved-results-audit.json').read_bytes())
    if (not audit['accepted'] or audit['report_sha256']!=PREP_SHA or prep['updates'] or prep['excluded']
        or prep['errors'] or not prep['closed'] or len(prep['pairs'])!=6 or audit['proposed_per_key_cap_cp']!=.01):raise ValueError('Wrong audited scope')
    covered=verify_backup(OLD/'backup/manifest.json');covered.update(verify_backup(PREP/'backup/manifest.json'))
    verify_backup(PREP/'audit-backup/manifest.json')
    for name,sha in prep['required_sha256'].items():
        if covered.get(name)!=sha or digest(ROOT/name)!=sha:raise ValueError('Protected input changed: '+name)
    if digest(PREP/'checkpoint-00.json')!=prep['checkpoint_sha256']:raise ValueError('Zero checkpoint changed')
    zero=json.loads((PREP/'checkpoint-00.json').read_bytes())
    if zero['updates'] or any(zero['delta_cp'].values()):raise ValueError('Expected zero')
    return prep,zero['active_keys']


def locations(prep):
    result=[]
    for pair in prep['pairs']:
        for label,branch in pair['branches'].items():
            result.append(dict(id=pair['id']+':'+label,kind='train_leaf',root_side='white',baseline=branch['features']))
    for r in prep['validation']:
        result.append(dict(id=r['row']['id']+':leaf',kind='validation_leaf',root_side=r['row']['side_to_move'],
            stratum=r['row']['stratum'],teacher_cp=r['row']['teacher_cp'],baseline=r['features']))
    root_audit=json.loads((PREP/'saved-results-audit.json').read_bytes())
    sfens=[x['sfen'] for x in root_audit['cap_direction_checks']['1']['observations']][47:]
    roots=native(sfens)
    for pair,f in zip(prep['pairs'],roots[:6]):result.append(dict(id=pair['id']+':root',kind='train_root',root_side='white',baseline=f))
    for r,f in zip(prep['validation'],roots[6:]):result.append(dict(id=r['row']['id']+':root',kind='validation_root',
        root_side=r['row']['side_to_move'],stratum=r['row']['stratum'],baseline=f))
    if len(result)!=88:raise ValueError('Expected12+35+6+35 locations')
    return result


def summarize(observations):
    def group(rows):
        if not rows:return dict(positions=0)
        base=math.fsum(x['loss_base'] for x in rows)/len(rows)
        loss=math.fsum(x['loss_candidate'] for x in rows)/len(rows)
        return dict(positions=len(rows),changed=sum(x['change']!=0 for x in rows),
            max_integer_change=max(abs(x['change']) for x in rows),max_smooth_change=max(abs(x['smooth_change']) for x in rows),
            loss_base=base,loss=loss,relative_improvement=(base-loss)/base if base else 0)
    rows=[x for x in observations if x['kind']=='validation_leaf']
    return dict(all=group(rows),side={s:group([x for x in rows if x['side']==s]) for s in ('black','white')},
        draw=group([x for x in rows if x['stratum'].endswith(':draw')]),
        strata={s:group([x for x in rows if x['stratum']==s]) for s in sorted({x['stratum'] for x in rows})})


def evaluate(prep,points,delta,path):
    raw={k:math.trunc(v*65536) for k,v in delta.items()}
    if any(abs(x)>655 for x in raw.values()):raise ValueError('Raw cap exceeds authorized0.01cp')
    write_delta(path,raw)
    frames=native([x['baseline']['sfen'] for x in points],path);observations=[]
    for point,after in zip(points,frames):
        before=point['baseline'];side=point['root_side']
        if before['features']!=after['features'] or before['progress']!=after['progress']:raise ValueError('Position/progress changed')
        expected={'kp':[0,0,0,0],'others':[0,0,0,0]}
        for t,a,b,count in before['features']:
            for lane in ((0,1,2) if t==0 else (0,2)):
                expected['kp' if t==0 else 'others'][lane]+=count*raw.get(f'{t}:{a}:{b}:{lane}',0)
        for mode in ('on_parts','off_parts'):
            if before[mode]['tempo']!=after[mode]['tempo']:raise ValueError('Tempo changed')
            for part in ('kp','others'):
                if [after[mode][part][l]-before[mode][part][l] for l in range(4)]!=expected[part]:raise ValueError('Protected/table lanes changed')
        base=root_cp(before,side);candidate=root_cp(after,side)
        smooth=math.fsum(v*delta.get(k,0) for k,v in factors(before,side).items())
        raw_smooth=math.fsum(v*raw.get(k,0)/65536 for k,v in factors(before,side).items())
        if abs(candidate-base)>10 or abs(candidate-base-raw_smooth)>2.000001:raise ValueError('Evaluation bound/mismatch')
        x=dict(id=point['id'],kind=point['kind'],side=side,base_cp=base,candidate_cp=candidate,
            change=candidate-base,smooth_change=smooth,raw_smooth_change=raw_smooth)
        if 'stratum' in point:x['stratum']=point['stratum']
        if 'teacher_cp' in point:
            target=sigmoid(GAIN*point['teacher_cp'])
            x.update(loss_base=(sigmoid(GAIN*base)-target)**2,loss_candidate=(sigmoid(GAIN*candidate)-target)**2)
        observations.append(x)
    pairs=[];samples=[]
    for i,pair in enumerate(prep['pairs']):
        actual,alt=observations[2*i:2*i+2]
        gap=alt['candidate_cp']-actual['candidate_cp'];base=pair['sample']['base_gap']
        smooth=base+math.fsum(v*delta.get(k,0) for k,v in pair['sample']['factors'].items())
        pairs.append(dict(id=pair['id'],base_gap=base,gap=gap,gap_change=gap-base,smooth_gap=smooth,
            actual_cp_change=actual['change'],alternative_cp_change=alt['change']))
        samples.append(dict(base_gap=gap,factors={}))
    loss,_=objective([p['sample'] for p in prep['pairs']],delta,0)
    integer_loss,_=objective(samples,{})
    return dict(pair_loss_smooth=loss,pair_loss_integer=integer_loss,pairs=pairs,validation=summarize(observations),
        observations=observations,max_integer_change=max(abs(x['change']) for x in observations),
        max_smooth_change=max(abs(x['smooth_change']) for x in observations),raw_nonzero=sum(v!=0 for v in raw.values()))


def run(output,execute=False):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Learning attempt already started/closed')
    prep,keys=verify_inputs()
    points=locations(prep)
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(config=updater.CONFIG,preparation_sha256=PREP_SHA,audit_sha256=AUDIT_SHA,
        full_batch_pairs=6,temperature_cp=600,selected_update=20,selection='fixed final averaged candidate; no reselection',
        max_position_cp_change=10,outcome_loss_enabled=False,deployment_enabled=False,training_enabled=execute)
    write_report(output/'plan.json',plan)
    write_report(output/'baseline-locations.json',points)
    if execute:
        with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json'),max_updates=20),f)
    required=dict(prep['required_sha256'])
    paths=[PREP/'report.json',PREP/'audit.json',PREP/'saved-results-audit.json',PREP/'checkpoint-00.json',
        Path(__file__),ROOT/'tools/learning/imitation/sparse_updater.py',output/'plan.json',output/'baseline-locations.json',
        ROOT/'test/learning/imitation/test_sparse_updater.py',ROOT/'test/learning/imitation/test_imitation_pilot.py']
    if execute:paths.append(MARKER)
    extras={str(p.relative_to(ROOT)):digest(p) for p in paths}
    create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras);required.update(extras)
    binding=dict(plan_sha256=digest(output/'plan.json'),required_sha256=required)
    r=dict(plan=plan,binding=binding,updates=0,trajectory=[],saved=[],selected_update=20 if execute else None,
        deployed=False,searches=0,qsearch_calls=0,errors=[],closed=False,backup_sha256=digest(output/'backup/manifest.json'))
    state=updater.initial(keys);samples=[p['sample'] for p in prep['pairs']]
    def save():
        avg=updater.average(state);cp=output/f'checkpoint-{state["updates"]:02d}.json'
        write_report(cp,updater.checkpoint(state,binding))
        if updater.restore(json.loads(cp.read_bytes()),binding)!=state:raise ValueError('Checkpoint mismatch')
        values=evaluate(prep,points,avg,output/f'average-{state["updates"]:02d}.txt')
        if state['updates']==0 and any(x['change'] for x in values['observations']):raise ValueError('Zero mismatch')
        values.update(update=state['updates'],checkpoint_sha256=digest(cp),sidecar_sha256=digest(output/f'average-{state["updates"]:02d}.txt'),
            mean_abs_average=math.fsum(abs(v) for v in avg.values())/len(avg),max_abs_average=max(abs(v) for v in avg.values()),
            average_cap_hits=sum(abs(v)>=.01-1e-12 for v in avg.values()),current_cap_hits=sum(abs(v)>=.01-1e-12 for v in state['delta'].values()))
        r['saved'].append(values);write_report(output/'report.json',r)
    try:
        save()
        if execute:
            while state['updates']<20:
                loss,g=objective(samples,state['delta'],1e-6)
                state=updater.step(state,g);r['updates']=state['updates']
                r['trajectory'].append(dict(update=state['updates'],loss=loss,gradient=g,state=state))
                if state['updates'] in (5,10,20):save()
        verify_inputs();verify_backup(output/'backup/manifest.json',extras)
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        r['closed']=True
    except Exception as e:r['closed']=True;r['errors'].append(str(e));raise
    finally:write_report(output/'report.json',r)
    print(json.dumps(dict(updates=r['updates'],selected_update=r['selected_update'],saved=[{k:v for k,v in x.items() if k not in ('observations','checkpoint_sha256','sidecar_sha256')} for x in r['saved']]),indent=2));return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--run',action='store_true')
    args=parser.parse_args();run(args.output,args.run)
