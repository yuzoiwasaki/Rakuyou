"""One fixed 50/50 temporal run against saved search-only controls."""
import argparse
from pathlib import Path
from tools.learning.constraints import temporal_runner as base

OUTPUT=base.data.ROOT/'results/learning-pilot/2026-10-18-temporal-mixed-v1'
ALPHA=.5


def inputs():
    parent,source,rows,parts,_=base.load()
    path=base.OUTPUT/'search/checkpoint.json';state=base.old.unseal(path)
    binding=dict(plan_sha256=base.data.digest(base.OUTPUT/'plan.json'),method='projected',arm='search',alpha=0.)
    base.validate(state,parent['keys'],binding,parent['training'],parts['train'])
    if not state['stopped']:raise ValueError('Search control not finished')
    control=base.old.unseal(base.OUTPUT/'comparison.json')
    if control['checkpoint_sha256']!=base.data.digest(path) or control['plan_sha256']!=binding['plan_sha256']:
        raise ValueError('Search comparison binding differs')
    names=['plan.json','comparison.json','search/checkpoint.json','old-search/delta.txt','temporal-search/delta.txt']
    for name,r in control['reports'].items():
        base.data.checked(base.OUTPUT/name/'delta.txt',r['sidecar_sha256'])
    return parent,source,rows,parts,control,{n:base.data.digest(base.OUTPUT/n) for n in names}


def prepare(output=OUTPUT):
    parent,_,_,_,_,bindings=inputs()
    plan=dict(schema='temporal-mixed-v1',alpha=ALPHA,training=parent['training'],projected=parent['projected'],
              keys=parent['keys'],train_ids=parent['train_ids'],control_sha256=bindings,
              code_sha256=base.data.digest(Path(__file__)),
              selection='Zero start; one fixed50/50 mix, final train-stopped state; no ratio sweep/adoption')
    output=base.data.output_path(output);output.mkdir(parents=True,exist_ok=False)
    base.old.seal(output/'plan.json',plan);return plan


def load(output=OUTPUT):
    plan=base.old.unseal(output/'plan.json');parent,source,rows,parts,control,bindings=inputs()
    if (plan['schema']!='temporal-mixed-v1' or plan['alpha']!=ALPHA
            or plan['training']!=parent['training'] or plan['projected']!=parent['projected']
            or plan['keys']!=parent['keys'] or plan['train_ids']!=parent['train_ids']
            or plan['control_sha256']!=bindings or plan['code_sha256']!=base.data.digest(Path(__file__))):
        raise ValueError('Mixed experiment binding differs')
    return plan,source,rows,parts,control


def train(output=OUTPUT):
    plan,source,rows,parts,control=load(output)
    with base.old.exclusive(output/'training.lock'):
        binding=dict(plan_sha256=base.data.digest(output/'plan.json'),method='projected',arm='mixed',alpha=ALPHA)
        state=base.train_arm(parts['train'],plan['keys'],ALPHA,plan['training'],binding,
                             output/'mixed','projected',plan['projected'])
        folder=output/'temporal-mixed';folder.mkdir(exist_ok=True)
        evaluated=base.evaluate(source,rows,parts,state['delta'],folder/'delta.txt')
        reports={**control['reports'],'temporal-mixed':evaluated}
        load(output)
        base.old.seal(output/'comparison.json',dict(plan_sha256=binding['plan_sha256'],
            checkpoint_sha256=base.data.digest(output/'mixed/checkpoint.json'),updates=state['updates'],
            stopping_reason=state['stopping_reason'],reports=reports,deployed=False))
        lines=['Fixed 50/50 mix vs saved search controls; loss improvements are NOT win rates.',
               f"Updates {state['updates']}; stop {state['stopping_reason']}",
               'candidate split cohort outcome% search% max-cp']
        for name,r in reports.items():
            for split in ('train','validation'):
                for group in ('original','additional','all','loss'):
                    m=r['integer'][split][group]
                    lines.append(f"{name} {split} {group} {m['outcome']['improvement_percent']:.6f} {m['search']['improvement_percent']:.6f} {m['max_abs_change_cp']}")
        lines.append('Exposed validation; no search, games or deployment. See comparison.json for smooth/side/outcome/draw diagnostics.')
        (output/'summary.txt').write_text('\n'.join(lines)+'\n')
    return reports


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','run'])
    args=parser.parse_args()
    if args.command=='prepare':prepare();print('Prepared one zero-start mixed run; controls reused, no learning performed.')
    else:train();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':main()
