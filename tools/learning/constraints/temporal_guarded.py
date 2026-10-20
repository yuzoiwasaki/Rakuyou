"""One zero-start guarded 50/50 run; saved ordinary mixed control, final-only scoring."""
import argparse
from collections import Counter
from pathlib import Path
from tools.learning.constraints import temporal_mixed as mixed
from tools.learning.constraints import group_guarded as optimizer

base = mixed.base
OUTPUT = base.data.ROOT / 'results/learning-pilot/2026-10-20-temporal-guarded-v1'


def inputs():
    parent, source, rows, parts, _ = mixed.load()
    path = mixed.OUTPUT / 'mixed/checkpoint.json'
    state = base.old.unseal(path)
    binding = dict(plan_sha256=base.data.digest(mixed.OUTPUT / 'plan.json'), method='projected', arm='mixed', alpha=.5)
    base.validate(state, parent['keys'], binding, parent['training'], parts['train'])
    control = base.old.unseal(mixed.OUTPUT / 'comparison.json')
    if not state['stopped'] or control['checkpoint_sha256'] != base.data.digest(path) or control['plan_sha256'] != binding['plan_sha256']:
        raise ValueError('Mixed control incomplete or mismatched')
    for name, report in control['reports'].items():
        folder = mixed.OUTPUT if name == 'temporal-mixed' else base.OUTPUT
        base.data.checked(folder / name / 'delta.txt', report['sidecar_sha256'])
    bindings = {n: base.data.digest(mixed.OUTPUT / n) for n in ('plan.json', 'comparison.json', 'mixed/checkpoint.json', 'temporal-mixed/delta.txt')}
    return parent, source, rows, parts, control, bindings


def specification():
    parent, _, _, _, _, bindings = inputs()
    modules = [Path(__file__), Path(optimizer.__file__), Path(optimizer.diagnostic.__file__), Path(optimizer.diagnostic.audit.__file__)]
    return dict(schema='temporal-guarded-v1', alpha=.5, training=parent['training'],
                keys=parent['keys'], train_ids=parent['train_ids'], projected=parent['projected'],
                control_sha256=bindings, epsilon=optimizer.EPSILON,
                code_sha256={str(p.relative_to(base.data.ROOT)): base.data.digest(p) for p in modules},
                selection='Zero start; mean then balanced fallback, each <=21 trials; all five train losses decrease; final-only <=200 updates')


def prepare(output=OUTPUT):
    plan = specification()
    output = base.data.output_path(output)
    output.mkdir(parents=True, exist_ok=False)
    base.old.seal(output / 'plan.json', plan)
    return plan


def load(output=OUTPUT):
    plan = base.old.unseal(output / 'plan.json')
    if plan != specification():
        raise ValueError('Guarded experiment binding differs')
    _, source, rows, parts, control, _ = inputs()
    return plan, source, rows, parts, control


def validate(state, keys, binding, config, rows):
    base.validate(state, keys, binding, config, rows)
    previous = optimizer.diagnostic.losses(rows, {k: 0. for k in keys}, config['l2'])
    for entry in state['trajectory']:
        if entry['group_before'] != previous or not optimizer.improves(previous, entry['group_after']):
            raise ValueError('Group trajectory failed guard')
        if entry['method'] not in ('mean', 'unit_group_sum'):
            raise ValueError('Unknown direction')
        previous = entry['group_after']
    if previous != optimizer.diagnostic.losses(rows, state['delta'], config['l2']):
        raise ValueError('Final group losses differ')


def train_arm(rows, keys, config, binding, directory):
    directory.mkdir(exist_ok=True)
    path = directory / 'checkpoint.json'
    state = base.old.unseal(path) if path.exists() else base.old.initial_state(keys, binding)
    validate(state, keys, binding, config, rows)
    if not path.exists():
        base.old.seal(path, state)
        base.old.seal(directory / 'checkpoint-000.json', state)
    while state['updates'] < config['max_updates'] and not state['stopped']:
        proposal = optimizer.propose_step(rows, state['delta'], config)
        if not proposal['accepted']:
            state.update(stopped=True, stopping_reason=proposal['stopping_reason'])
            state['stop_diagnostic'] = {k: v for k, v in proposal.items() if k != 'delta'}
            base.old.seal(path, state)
            break
        state['delta'] = proposal.pop('delta')
        state['updates'] += 1
        state['trajectory'].append(dict(update=state['updates'], **proposal))
        base.old.seal(path, state)
        if state['updates'] in config['save_updates']:
            base.old.seal(directory / f"checkpoint-{state['updates']:03d}.json", state)
            counts = dict(Counter(e['method'] for e in state['trajectory']))
            print(f"guarded: {state['updates']} updates; loss {proposal['loss_after']:.9f}; directions {counts}", flush=True)
    if not state['stopped']:
        state.update(stopped=True, stopping_reason='update_budget')
        base.old.seal(path, state)
    validate(state, keys, binding, config, rows)
    return state


def train(output=OUTPUT):
    plan, source, rows, parts, control = load(output)
    with base.old.exclusive(output / 'training.lock'):
        binding = dict(plan_sha256=base.data.digest(output / 'plan.json'), method='group-guarded', arm='mixed', alpha=.5)
        state = train_arm(parts['train'], plan['keys'], plan['training'], binding, output / 'mixed')
        folder = output / 'guarded-mixed'
        folder.mkdir(exist_ok=True)
        reports = {**control['reports'], 'guarded-mixed': base.evaluate(source, rows, parts, state['delta'], folder / 'delta.txt')}
        counts = dict(Counter(e['method'] for e in state['trajectory']))
        load(output)
        base.old.seal(output / 'comparison.json', dict(plan_sha256=binding['plan_sha256'],
            checkpoint_sha256=base.data.digest(output / 'mixed/checkpoint.json'), updates=state['updates'],
            stopping_reason=state['stopping_reason'], direction_counts=counts, reports=reports, deployed=False))
        lines = ['Train-group guarded mixed comparison; loss improvements are NOT win rates.',
                 f"Updates {state['updates']}; stop {state['stopping_reason']}; directions {counts}",
                 'candidate split group outcome% search% max-cp']
        for name in ('temporal-mixed', 'guarded-mixed'):
            for split in ('train', 'validation'):
                for group in ('all', 'win', 'loss', 'original', 'additional'):
                    m = reports[name]['integer'][split][group]
                    lines.append(f"{name} {split} {group} {m['outcome']['improvement_percent']:.6f} {m['search']['improvement_percent']:.6f} {m['max_abs_change_cp']}")
        lines.append('Guards use smooth training losses only. Exposed validation; no search, games or deployment.')
        (output / 'summary.txt').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'run'])
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
        print('Prepared guarded mixed run; no learning performed.')
    else:
        train()
        print((OUTPUT / 'summary.txt').read_text(), end='')


if __name__ == '__main__':
    main()
