"""One equal-game weighted temporal search run; final-only diagnostics."""
import argparse
from pathlib import Path
from tools.learning.hybrid import data, runner as old
from tools.learning.constraints import temporal_teachers as teachers
from tools.learning.constraints import weighted_projected as optimizer
from tools.learning.constraints.weighted_objective import objective
from tools.learning.constraints import runner_v2 as previous

OUTPUT=data.ROOT/'results/learning-pilot/2026-10-18-temporal-training-v1'


def inputs():
    source,dataset=data.load_dataset(data.DEFAULT_OUTPUT)
    ot=data.load_teachers(data.DEFAULT_OUTPUT,source,dataset['rows'])
    parent,new=teachers.load()
    nt=data.load_teachers(teachers.OUTPUT,parent,new['rows'])
    if not nt['completed']:raise ValueError('Teachers incomplete')
    accepted={r['id']:r['teacher_cp'] for r in nt['records'] if r['status']=='accepted'}
    parts,_,_=old.cohort(dataset,ot)
    parts={s:[dict(r,cohort='original') for r in rs] for s,rs in parts.items()}
    additions=[dict(r,teacher_cp=accepted[r['id']],cohort='additional') for r in new['rows'] if r['id'] in accepted]
    for s in parts:parts[s].extend(r for r in additions if r['split']==s)
    if [len(parts[s]) for s in ('train','validation')]!=[750,187]:raise ValueError('Unexpected cohort')
    if {r['run'] for r in parts['train']} & {r['run'] for r in parts['validation']}:raise ValueError('Cross-split run')
    rows=dataset['rows']+additions
    reference=previous.OUTPUT/'projected-search/checkpoint.json'
    delta=old.unseal(reference)['delta']
    paths=[data.DEFAULT_OUTPUT/n for n in ('plan.json','dataset.json','teachers.json')]
    paths += [teachers.OUTPUT/n for n in ('plan.json','dataset.json','teachers.json')]+[reference]
    return source,rows,parts,delta,{str(p.relative_to(data.ROOT)):data.digest(p) for p in paths}


def dependencies():
    paths=[Path(__file__),Path(optimizer.__file__),Path(__file__).with_name('weighted_objective.py'),
           Path(__file__).with_name('projected.py'),Path(__file__).with_name('optimizer.py'),Path(old.__file__)]
    return {str(p.relative_to(data.ROOT)):data.digest(p) for p in paths}


def prepare(output=OUTPUT):
    source,rows,parts,reference,bindings=inputs()
    keys=sorted({k for r in parts['train'] for k in r['factors']})
    if not set(reference)<=set(keys):raise ValueError('Original train keys missing')
    frames=old.native_frames(source,data.DEFAULT_OUTPUT,rows)
    for row,frame in zip(rows,frames):old.check_frame(row,frame,{})
    plan=dict(schema='temporal-training-v1',training=source['training'],projected=optimizer.OPTIONS,
              inputs_sha256=bindings,code_sha256=dependencies(),keys=keys,
              train_ids=[r['id'] for r in parts['train']],alpha=0.,
              selection='Zero start, final train-stopped state <=200; no validation selection',
              weights='Equal game total: 1/(G*m), recomputed within each reporting subgroup',
              native_zero_checks=len(rows))
    output=data.output_path(output);output.mkdir(parents=True,exist_ok=False)
    old.seal(output/'plan.json',plan);return plan


def load(output=OUTPUT):
    plan=old.unseal(output/'plan.json');source,rows,parts,reference,bindings=inputs()
    if (plan['schema']!='temporal-training-v1' or plan['inputs_sha256']!=bindings
            or plan['code_sha256']!=dependencies() or plan['training']!=source['training']
            or plan['projected']!=optimizer.OPTIONS or plan['alpha']!=0.
            or plan['train_ids']!=[r['id'] for r in parts['train']]
            or plan['keys']!=sorted({k for r in parts['train'] for k in r['factors']})):
        raise ValueError('Temporal training binding differs')
    return plan,source,rows,parts,reference


def validate(state,keys,binding,config,rows):
    # Reuse structural/trajectory checks with normalized stopping labels only.
    if state['stopping_reason'] not in optimizer.REASONS|{None}:
        raise ValueError('Unknown stopping reason')
    compatible={**state,'stopping_reason':state['stopping_reason']}
    if state['stopping_reason'] not in (None,'zero_gradient','no_acceptable_improvement','update_budget'):
        compatible['stopping_reason']='no_acceptable_improvement'
    old.validate_state(compatible,keys,binding,config)
    for row in rows:
        if abs(optimizer.dot(row['factors'],state['delta']))>config['train_position_limit_cp']:
            raise ValueError('Checkpoint position cap exceeded')
    if state['updates']:
        loss,_=optimizer.objective(rows,state['delta'],binding['alpha'],config['l2'])
        if loss!=state['trajectory'][-1]['loss_after']:
            raise ValueError('Checkpoint objective differs from trajectory')


def train_arm(rows,keys,alpha,config,binding,directory,method,direction_options):
    directory.mkdir(exist_ok=True)
    path=directory/'checkpoint.json'
    state=old.unseal(path) if path.exists() else old.initial_state(keys,binding)
    validate(state,keys,binding,config,rows)
    options={k:config[k] for k in ('l2','step_cp','delta_limit_cp','train_position_limit_cp','max_backtracks')}
    if method!='projected':raise ValueError('Expected projected method')
    step=optimizer.propose_step
    if method=='projected': options.update(direction_options)
    if not path.exists():
        old.seal(path,state);old.seal(directory/'checkpoint-000.json',state)
    while state['updates']<config['max_updates'] and not state['stopped']:
        proposal=step(rows,state['delta'],alpha,**options)
        if not proposal['accepted']:
            state.update(stopped=True,stopping_reason=proposal['stopping_reason'])
            state['stop_diagnostic']={k:v for k,v in proposal.items() if k!='delta'}
            old.seal(path,state);break
        state['delta']=proposal.pop('delta');state['updates']+=1
        state['trajectory'].append(dict(update=state['updates'],**proposal))
        # Save every completed update: no repetition of a long training prefix.
        old.seal(path,state)
        if state['updates'] in config['save_updates']:
            old.seal(directory/f"checkpoint-{state['updates']:03d}.json",state)
            print(f"{directory.name}: {state['updates']} updates; loss {proposal['loss_after']:.9f}",flush=True)
    if not state['stopped']:
        state.update(stopped=True,stopping_reason='update_budget');old.seal(path,state)
    validate(state,keys,binding,config,rows)
    return state


def metrics(rows,predictions):
    if not rows:return dict(positions=0)
    before=[dict(r,factors={}) for r in rows]
    after=[dict(r,base_cp=predictions[r['id']],factors={}) for r in rows]
    result=dict(positions=len(rows),games=len({(r['run'],r['game']) for r in rows}))
    for name,alpha in [('search',0.),('outcome',1.)]:
        a=objective(before,{},alpha,0.)[0];b=objective(after,{},alpha,0.)[0]
        result[name]=dict(baseline=a,candidate=b,improvement_percent=100*(a-b)/a)
    result['max_abs_change_cp']=max(abs(predictions[r['id']]-r['base_cp']) for r in rows)
    return result


def evaluate(source,rows,parts,delta,path):
    raw=old.save_delta(path,delta);frames=old.native_frames(source,data.DEFAULT_OUTPUT,rows,path)
    integer={r['id']:old.check_frame(r,f,raw) for r,f in zip(rows,frames)}
    smooth={r['id']:old.score(r,delta) for r in rows}
    result={}
    for mode,predictions in [('integer',integer),('smooth',smooth)]:
        result[mode]={}
        for split,rs in parts.items():
            groups={'all':rs,**{c:[r for r in rs if r['cohort']==c] for c in ('original','additional')},
                    **{s:[r for r in rs if r['side']==s] for s in ('black','white')},
                    **{s:[r for r in rs if r['target']==v] for s,v in [('win',1),('loss',0)]}}
            result[mode][split]={g:metrics(sub,predictions) for g,sub in groups.items()}
    draws=[r for r in rows if not r['use_outcome_loss']]
    result['draw_diagnostics']={s:dict(positions=sum(r['side']==s for r in draws),
        max_abs_cp=max((abs(integer[r['id']]-r['base_cp']) for r in draws if r['side']==s),default=0)) for s in ('black','white')}
    result['observations']=[dict(id=r['id'],base_cp=r['base_cp'],candidate_cp=integer[r['id']],smooth_cp=smooth[r['id']]) for r in rows]
    result['sidecar_sha256']=data.digest(path)
    return result


def train(output=OUTPUT):
    plan,source,rows,parts,reference=load(output)
    with old.exclusive(output/'training.lock'):
        binding=dict(plan_sha256=data.digest(output/'plan.json'),method='projected',arm='search',alpha=0.)
        state=train_arm(parts['train'],plan['keys'],0.,plan['training'],binding,output/'search','projected',plan['projected'])
        # Only after training: evaluate both fixed old and new deltas on identical rows.
        reports={}
        for name,delta in [('old-search',reference),('temporal-search',state['delta'])]:
            folder=output/name;folder.mkdir(exist_ok=True)
            reports[name]=evaluate(source,rows,parts,delta,folder/'delta.txt')
        load(output)
        old.seal(output/'comparison.json',dict(plan_sha256=binding['plan_sha256'],
                 checkpoint_sha256=data.digest(output/'search/checkpoint.json'),updates=state['updates'],
                 stopping_reason=state['stopping_reason'],reports=reports,deployed=False))
        lines=['Equal-game temporal search comparison; loss improvements are NOT win rates.',
               f"Updates {state['updates']}; stop {state['stopping_reason']}",
               'candidate split cohort outcome% search% max-cp']
        for name,r in reports.items():
            for split in ('train','validation'):
                for cohort in ('original','additional','all'):
                    m=r['integer'][split][cohort]
                    lines.append(f"{name} {split} {cohort} {m['outcome']['improvement_percent']:.6f} {m['search']['improvement_percent']:.6f} {m['max_abs_change_cp']}")
        lines.append('Exposed validation; no search, games or deployment. See comparison.json for smooth/side/outcome/draw diagnostics.')
        (output/'summary.txt').write_text('\n'.join(lines)+'\n')
    return reports


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','run'])
    args=parser.parse_args()
    if args.command=='prepare':
        p=prepare();print('Prepared 750 train /187 validation; native zero checks',p['native_zero_checks'])
    else:
        train();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':main()
