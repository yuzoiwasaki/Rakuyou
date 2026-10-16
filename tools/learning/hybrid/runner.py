"""Train and summarize three matched root-static teacher experiments.

Run only on the new hybrid dataset. Old runs and operational files are read-only.
Training can resume at a saved arithmetic checkpoint; validation never selects it.
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
import math
from pathlib import Path
import subprocess

from tools.learning.core.king_safety_updater import fingerprint
from tools.learning.data.prepare_learning_data import ROOT, digest
from tools.learning.imitation.sparse_objective import root_cp, write_delta
from tools.learning.tempo.run_tempo_search import write_report
from .objective import objective
from .optimizer import propose_step

ARMS = {'search': 0.0, 'outcome': 1.0, 'mixed': 0.5}


@contextmanager
def exclusive(path):
    """OS lock releases on interruption; the lock file is not an attempt marker."""
    with Path(path).open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Another hybrid training process is running') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def seal(path, body):
    write_report(path, {**body, 'content_sha256': fingerprint(body)})


def unseal(path):
    record = json.loads(Path(path).read_text())
    sha = record.pop('content_sha256')
    if fingerprint(record) != sha:
        raise ValueError('Checkpoint/report content changed')
    return record


def cohort(dataset, teachers):
    """Exactly the same accepted decisive roots feed all three arms."""
    rows = dataset['rows']
    decisive = {r['id']: r for r in rows if r['use_outcome_loss']}
    records = teachers['records']
    if not teachers['completed'] or len(records) != len(decisive):
        raise ValueError('Teacher collection is incomplete or has failed searches')
    ids = [r['id'] for r in records]
    if len(set(ids)) != len(ids) or set(ids) != set(decisive):
        raise ValueError('Teacher membership differs from frozen decisive roots')
    by_id = {}
    excluded = []
    for record in records:
        if record['status'] == 'accepted':
            cp = record['teacher_cp']
            if type(cp) not in (float, int) or not math.isfinite(cp) or abs(cp) >= 31000:
                raise ValueError('Invalid accepted cp teacher')
            by_id[record['id']] = cp
        elif record['status'] == 'excluded' and record.get('teacher_cp') is None:
            excluded.append(record['id'])
        else:
            raise ValueError('Failed or invalid teacher cannot become a silent exclusion')
    parts = {s: [{**r, 'teacher_cp': by_id[r['id']]} for r in rows
                 if r['split'] == s and r['id'] in by_id] for s in ('train', 'validation')}
    for split, selected in parts.items():
        original = [r for r in decisive.values() if r['split'] == split]
        if len(selected) < math.ceil(.9 * len(original)) or not original:
            raise ValueError('Less than 90% of a decisive split has usable teachers')
        if {(r['side'], r['target']) for r in selected} != {
                (side, target) for side in ('black', 'white') for target in (0, 1)}:
            raise ValueError('A side/outcome stratum disappeared')
    return parts, by_id, excluded


def score(row, delta):
    return row['base_cp'] + math.fsum(v * delta.get(k, 0) for k, v in row['factors'].items())


def metrics(rows, predictions):
    """Two common quality measures; no comparison of unlike arm objectives."""
    if not rows:
        return {'positions': 0}
    base = [{**r, 'factors': {}} for r in rows]
    changed = [{**r, 'base_cp': predictions[r['id']], 'factors': {}} for r in rows]
    result = {'positions': len(rows)}
    for name, alpha in (('search_ce', 0), ('outcome_ce', 1)):
        before = objective(base, {}, alpha, 0)[0]
        after = objective(changed, {}, alpha, 0)[0]
        result[name] = dict(baseline=before, candidate=after,
                            improvement_percent=100 * (before-after)/before)
    result['teacher_rmse_cp'] = math.sqrt(math.fsum(
        (predictions[r['id']]-r['teacher_cp'])**2 for r in rows)/len(rows))
    result['baseline_teacher_rmse_cp'] = math.sqrt(math.fsum(
        (r['base_cp']-r['teacher_cp'])**2 for r in rows)/len(rows))
    result['toward_winner'] = sum((predictions[r['id']]-r['base_cp'])*(2*r['target']-1) > 0 for r in rows)
    result['away_from_winner'] = sum((predictions[r['id']]-r['base_cp'])*(2*r['target']-1) < 0 for r in rows)
    return result


def split_metrics(rows, predictions):
    return dict(all=metrics(rows, predictions),
                side={s: metrics([r for r in rows if r['side'] == s], predictions)
                      for s in ('black', 'white')},
                outcome={s: metrics([r for r in rows if r['target'] == t], predictions)
                         for s, t in (('win', 1), ('loss', 0))})


def native_frames(plan, output, rows, delta_file=None, params=None):
    binary = ROOT/plan['probes']['features']['path']
    command = [str(binary), '--features-sfen', str(params or output/'runtime/bin/params.bin')]
    if delta_file is not None:
        command.append(str(delta_file))
    process = subprocess.run(command, input='\n'.join(r['features']['sfen'] for r in rows)+'\n',
                             capture_output=True, text=True, check=True, timeout=120)
    frames = [json.loads(line) for line in process.stdout.splitlines()]
    if len(frames) != len(rows):
        raise ValueError('Native score frame count mismatch')
    return frames


def check_frame(row, after, raw):
    before = row['features']
    if any(before[k] != after[k] for k in ('features', 'progress', 'sfen')):
        raise ValueError('Feature, progress or position changed')
    expected = {'kp': [0]*4, 'others': [0]*4}
    for kind, a, b, count in before['features']:
        for lane in ((0, 1, 2) if kind == 0 else (0, 2)):
            expected['kp' if kind == 0 else 'others'][lane] += count*raw.get(f'{kind}:{a}:{b}:{lane}', 0)
    for mode in ('on_parts', 'off_parts'):
        if set(before[mode]) != set(after[mode]):
            raise ValueError('Evaluation component schema changed')
        for part in before[mode]:
            if part in expected:
                difference = [after[mode][part][i]-before[mode][part][i] for i in range(4)]
                if difference != expected[part]:
                    raise ValueError('Sparse table/packed component mismatch')
            elif before[mode][part] != after[mode][part]:
                raise ValueError('Protected evaluation component changed')
    change = root_cp(after, row['side'])-row['base_cp']
    raw_change = math.fsum(v*raw.get(k, 0)/65536 for k, v in row['factors'].items())
    if abs(change-raw_change) > 2.000001:
        raise ValueError('Native/smooth rounding discrepancy')
    return root_cp(after, row['side'])


def save_delta(path, delta):
    raw = {k: math.trunc(v*65536) for k, v in delta.items()}
    if any(abs(v) > 32768 for v in raw.values()):
        raise ValueError('Native sparse coefficient limit exceeded')
    if path.exists():
        expected = ''.join(k.replace(':', ' ')+f' {v}\n' for k, v in sorted(raw.items()))
        if path.read_text() != expected:
            raise ValueError('Existing sidecar differs from checkpoint')
    else:
        write_delta(path, raw)
    return raw


def evaluate(plan, output, rows, parts, delta, path):
    raw = save_delta(path, delta)
    frames = native_frames(plan, output, rows, path)
    integer = {r['id']: check_frame(r, frame, raw) for r, frame in zip(rows, frames)}
    smooth = {r['id']: score(r, delta) for r in rows}
    observations = [dict(id=r['id'], split=r['split'], side=r['side'], target=r['target'],
                         base_cp=r['base_cp'], candidate_cp=integer[r['id']], smooth_cp=smooth[r['id']])
                    for r in rows]
    def impact(selected):
        changes = [integer[r['id']]-r['base_cp'] for r in selected]
        return dict(positions=len(selected), changed=sum(x != 0 for x in changes),
                    max_abs_cp=max(map(abs, changes), default=0),
                    mean_cp=math.fsum(changes)/len(changes) if changes else None)
    return dict(integer={s: split_metrics(part, integer) for s, part in parts.items()},
                smooth={s: split_metrics(part, smooth) for s, part in parts.items()},
                impact={s: impact([r for r in rows if r['split'] == s])
                        for s in ('train', 'validation', 'diagnostic')},
                draw_impact={s: {side: impact([r for r in rows if r['split'] == s
                                             and not r['use_outcome_loss'] and r['side'] == side])
                                 for side in ('black', 'white')}
                             for s in ('train', 'validation', 'diagnostic')},
                max_smooth_change_cp=max(abs(smooth[r['id']]-r['base_cp']) for r in rows),
                observations=observations, sidecar_sha256=digest(path))


def initial_state(keys, binding):
    return dict(schema='rakuyou-hybrid-checkpoint-v1', binding=binding, updates=0,
                delta={k: 0.0 for k in keys}, trajectory=[], stopped=False, stopping_reason=None)


def validate_state(state, keys, binding, config):
    if state['schema'] != 'rakuyou-hybrid-checkpoint-v1' or state['binding'] != binding:
        raise ValueError('Training checkpoint binding mismatch')
    if type(state['updates']) is not int or not 0 <= state['updates'] <= config['max_updates']:
        raise ValueError('Invalid checkpoint update count')
    if set(state['delta']) != set(keys) or len(state['trajectory']) != state['updates']:
        raise ValueError('Checkpoint key/trajectory mismatch')
    if any(type(v) not in (float, int) or not math.isfinite(v) or abs(v) > config['delta_limit_cp']
           for v in state['delta'].values()):
        raise ValueError('Checkpoint coefficient bound')
    if type(state['stopped']) is not bool or state['stopping_reason'] not in (
            None, 'zero_gradient', 'no_acceptable_improvement', 'update_budget'):
        raise ValueError('Invalid checkpoint stopping state')
    if state['stopped'] != (state['stopping_reason'] is not None):
        raise ValueError('Checkpoint stopping state mismatch')
    if state['stopping_reason'] == 'update_budget' and state['updates'] != config['max_updates']:
        raise ValueError('Incomplete update budget')
    if state['updates'] == 0 and any(state['delta'].values()):
        raise ValueError('Initial checkpoint must have zero delta')
    previous = None
    for update, entry in enumerate(state['trajectory'], 1):
        if entry['update'] != update or entry['accepted'] is not True:
            raise ValueError('Checkpoint trajectory mismatch')
        if any(not math.isfinite(entry[k]) for k in ('loss_before', 'loss_after', 'max_train_change_cp')):
            raise ValueError('Nonfinite checkpoint trajectory')
        if not entry['loss_after'] < entry['loss_before'] or (previous is not None and entry['loss_before'] != previous):
            raise ValueError('Training trajectory did not monotonically improve')
        if entry['max_train_change_cp'] > config['train_position_limit_cp']:
            raise ValueError('Training trajectory exceeded impact bound')
        previous = entry['loss_after']


def train_arm(train, keys, alpha, config, binding, directory):
    directory.mkdir(exist_ok=True)
    current = directory/'checkpoint.json'
    state = unseal(current) if current.exists() else initial_state(keys, binding)
    validate_state(state, keys, binding, config)
    if max(abs(score(row, state['delta'])-row['base_cp']) for row in train) > config['train_position_limit_cp']+1e-9:
        raise ValueError('Checkpoint training position bound')
    if not current.exists():
        seal(current, state)
        seal(directory/'checkpoint-000.json', state)
    options = {k: config[k] for k in ('l2', 'step_cp', 'delta_limit_cp',
                                     'train_position_limit_cp', 'max_backtracks')}
    while state['updates'] < config['max_updates'] and not state['stopped']:
        proposed = propose_step(train, state['delta'], alpha, **options)
        if not proposed['accepted']:
            state['stopped'] = True
            state['stopping_reason'] = proposed['stopping_reason']
            seal(current, state)
            break
        state['delta'] = proposed.pop('delta')
        state['updates'] += 1
        state['trajectory'].append(dict(update=state['updates'], **proposed))
        if state['updates'] in config['save_updates']:
            seal(directory/f'checkpoint-{state["updates"]:03d}.json', state)
            seal(current, state)
            print(f'{directory.name}: {state["updates"]} updates, train loss '
                  f'{proposed["loss_after"]:.9f}, max train change '
                  f'{proposed["max_train_change_cp"]:.2f}cp', flush=True)
    if not state['stopped']:
        state['stopped'] = True
        state['stopping_reason'] = 'update_budget'
    seal(current, state)
    return state


def train(output):
    from .data import load_dataset, load_teachers
    output = Path(output).resolve()
    plan, dataset = load_dataset(output)
    if plan['arms'] != ARMS:
        raise ValueError('Expected fixed three-arm comparison')
    teacher_path = output/'teachers.json'
    teachers = load_teachers(output, plan, dataset['rows'])
    if teachers['plan_sha256'] != digest(output/'plan.json') or teachers['dataset_sha256'] != digest(output/'dataset.json'):
        raise ValueError('Teachers belong to another plan or dataset')
    parts, teacher_by_id, excluded = cohort(dataset, teachers)
    keys = sorted({k for r in parts['train'] for k in r['factors']})
    if not keys:
        raise ValueError('Empty training features')
    binding = dict(plan_sha256=digest(output/'plan.json'), teachers_sha256=digest(teacher_path),
                   train_ids=[r['id'] for r in parts['train']], keys_sha256=fingerprint(keys))
    with exclusive(output/'training.lock'):
        zero = native_frames(plan, output, dataset['rows'])
        for row, frame in zip(dataset['rows'], zero):
            if check_frame(row, frame, {}) != row['base_cp']:
                raise ValueError('Zero overlay differs from saved baseline')
        reports = {}
        for arm, alpha in ARMS.items():
            directory = output/arm
            state = train_arm(parts['train'], keys, alpha, plan['training'],
                              {**binding, 'arm': arm, 'alpha': alpha}, directory)
            report_path = directory/'report.json'
            if report_path.exists():
                report = unseal(report_path)
                if (report['checkpoint_sha256'] != digest(directory/'checkpoint.json')
                        or report['binding'] != state['binding']
                        or report['evaluation']['sidecar_sha256'] != digest(directory/'delta.txt')):
                    raise ValueError('Saved arm report differs from final checkpoint')
            else:
                evaluated = evaluate(plan, output, dataset['rows'], parts, state['delta'], directory/'delta.txt')
                report = dict(schema='rakuyou-hybrid-arm-v1', binding=state['binding'],
                              updates=state['updates'], stopping_reason=state['stopping_reason'],
                              checkpoint_sha256=digest(directory/'checkpoint.json'), evaluation=evaluated,
                              eligible_for_search=evaluated['max_smooth_change_cp'] <= plan['training']['train_position_limit_cp'],
                              deployed=False)
                seal(report_path, report)
            reports[arm] = report
        # Quality is observed only after fixed training, never used for step choice.
        load_dataset(output)
        if digest(teacher_path) != binding['teachers_sha256']:
            raise ValueError('Teachers changed during training')
        summary = dict(schema='rakuyou-hybrid-comparison-v1', binding=binding,
                       accepted={s: len(r) for s, r in parts.items()}, excluded_ids=excluded,
                       validation='reused diagnostic runs; not unseen or win-rate evidence',
                       selection='no winning arm or checkpoint selected automatically',
                       arms={a: dict(updates=r['updates'], stopping_reason=r['stopping_reason'],
                                     eligible_for_search=r['eligible_for_search'],
                                     integer=r['evaluation']['integer'], smooth=r['evaluation']['smooth'],
                                     impact=r['evaluation']['impact'], draw_impact=r['evaluation']['draw_impact'],
                                     report_sha256=digest(output/a/'report.json')) for a, r in reports.items()})
        seal(output/'comparison.json', summary)
        summary_text(output, summary)
    return summary


def summary_text(output, summary):
    lines = ['Search/outcome/mixed comparison (positive improvement = lower loss, NOT win rate)',
             f'Accepted train/validation: {summary["accepted"]}',
             'arm       updates train-outcome% val-outcome% val-search% max-val-cp']
    for arm, report in summary['arms'].items():
        train = report['integer']['train']['all']
        val = report['integer']['validation']['all']
        lines.append(f'{arm:9} {report["updates"]:7} '
                     f'{train["outcome_ce"]["improvement_percent"]:14.6f} '
                     f'{val["outcome_ce"]["improvement_percent"]:12.6f} '
                     f'{val["search_ce"]["improvement_percent"]:11.6f} '
                     f'{report["impact"]["validation"]["max_abs_cp"]:10}')
    lines += ['See comparison.json for smooth scores, side/result strata, and separate draw diagnostics.',
              'No candidate selected or deployed.']
    text = '\n'.join(lines)+'\n'
    (output/'summary.txt').write_text(text)
    print(text, end='')


def main():
    from .data import DEFAULT_OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    train(args.output)


if __name__ == '__main__':
    main()
