"""Fixed old/new optimizer comparison, three teachers, no search or deployment."""
import argparse
from pathlib import Path

from tools.learning.hybrid import data, runner as old
from tools.learning.hybrid.optimizer import propose_step as legacy_step
from tools.learning.constraints import projected as optimizer

SOURCE=data.DEFAULT_OUTPUT
OUTPUT=data.ROOT/'results/learning-pilot/2026-10-17-constrained-training-v2'


def dependencies():
    names=['tools/learning/constraints/__init__.py','tools/learning/constraints/optimizer.py','tools/learning/constraints/projected.py',
           'tools/learning/constraints/runner_v2.py','tools/learning/hybrid/runner.py',
           'tools/learning/hybrid/optimizer.py','tools/learning/hybrid/objective.py']
    return {n:data.digest(data.ROOT/n) for n in names}


def inputs():
    plan,dataset=data.load_dataset(SOURCE)
    teachers=data.load_teachers(SOURCE,plan,dataset['rows'])
    parts,_,_=old.cohort(dataset,teachers)
    names=['plan.json','dataset.json','teachers.json']
    for arm in old.ARMS: names.extend([arm+'/checkpoint.json',arm+'/report.json'])
    return plan,dataset,parts,{n:data.digest(SOURCE/n) for n in names}


def prepare(output=OUTPUT):
    output=data.output_path(output)
    source,dataset,parts,bindings=inputs()
    plan=dict(schema='constrained-training-v2',source=str(SOURCE),inputs_sha256=bindings,
              code_sha256=dependencies(),training=source['training'],projected=optimizer.OPTIONS,
              arms=old.ARMS,methods=['legacy','projected'],train_ids=[r['id'] for r in parts['train']],
              keys=sorted({k for r in parts['train'] for k in r['factors']}),
              selection='fixed 200 update budget, no validation selection, no adoption')
    output.mkdir(parents=True,exist_ok=False)
    old.seal(output/'plan.json',plan)
    return plan


def load(output):
    plan=old.unseal(output/'plan.json')
    source,dataset,parts,bindings=inputs()
    if (plan['schema']!='constrained-training-v2' or plan['source']!=str(SOURCE)
            or plan['code_sha256']!=dependencies() or plan['inputs_sha256']!=bindings
            or plan['training']!=source['training'] or plan['projected']!=optimizer.OPTIONS
            or plan['arms']!=old.ARMS or plan['methods']!=['legacy','projected']
            or plan['train_ids']!=[r['id'] for r in parts['train']]
            or plan['keys']!=sorted({k for r in parts['train'] for k in r['factors']})):
        raise ValueError('Frozen comparison binding differs')
    return plan,source,dataset,parts


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
    step=legacy_step if method=='legacy' else optimizer.propose_step
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


def train(output=OUTPUT):
    output=data.output_path(output)
    plan,source,dataset,parts=load(output)
    with old.exclusive(output/'training.lock'):
        binding=data.digest(output/'plan.json')
        # All runs start at zero; frozen old results are only reproduction checks.
        for method in plan['methods']:
            for arm,alpha in plan['arms'].items():
                name=method+'-'+arm
                state=train_arm(parts['train'],plan['keys'],alpha,plan['training'],
                                dict(plan_sha256=binding,method=method,arm=arm,alpha=alpha),
                                output/name,method,plan['projected'])
                if method=='legacy':
                    original=old.unseal(SOURCE/arm/'checkpoint.json')
                    if any(state[k]!=original[k] for k in ('delta','trajectory','updates','stopping_reason')):
                        raise ValueError('Legacy reproduction differs: '+arm)
        # Validation/native reporting happens only after all six training runs.
        reports={}
        for method in plan['methods']:
            for arm in plan['arms']:
                name=method+'-'+arm;directory=output/name
                state=old.unseal(directory/'checkpoint.json');path=directory/'report.json'
                if path.exists():
                    report=old.unseal(path)
                    if (report['checkpoint_sha256']!=data.digest(directory/'checkpoint.json')
                            or report['evaluation']['sidecar_sha256']!=data.digest(directory/'delta.txt')):
                        raise ValueError('Saved evaluation binding differs')
                else:
                    evaluated=old.evaluate(source,SOURCE,dataset['rows'],parts,state['delta'],directory/'delta.txt')
                    report=dict(checkpoint_sha256=data.digest(directory/'checkpoint.json'),
                                updates=state['updates'],stopping_reason=state['stopping_reason'],
                                evaluation=evaluated,deployed=False)
                    old.seal(path,report)
                reports[name]=report
        load(output)
        old.seal(output/'comparison.json',dict(plan_sha256=binding,arms=reports,
                 limitation='Reused diagnostic validation, not win rate; no candidate selected or deployed.'))
        lines=['Old/new optimizer comparison; loss improvements are NOT win rates.',
               'run updates stop train-outcome% val-outcome% val-search% max-val-cp']
        for name,r in reports.items():
            e=r['evaluation'];t=e['integer']['train']['all'];v=e['integer']['validation']['all']
            lines.append(f"{name} {r['updates']} {r['stopping_reason']} "
                         f"{t['outcome_ce']['improvement_percent']:.6f} "
                         f"{v['outcome_ce']['improvement_percent']:.6f} "
                         f"{v['search_ce']['improvement_percent']:.6f} "
                         f"{e['impact']['validation']['max_abs_cp']}")
        lines.append('See comparison.json for side/result strata, smooth scores and draw diagnostics. No deployment.')
        (output/'summary.txt').write_text('\n'.join(lines)+'\n')
    return reports


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'))
    args=parser.parse_args()
    if args.command=='prepare':
        prepare();print('Prepared six zero-start runs; no training performed.')
    else:
        train();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__': main()
