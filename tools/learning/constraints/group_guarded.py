"""Fixed mixed objective with strict train win/loss guards and balanced fallback."""
from tools.learning.constraints import common_direction as diagnostic
from tools.learning.constraints.weighted_objective import objective

EPSILON = 1e-12


def improves(before, after):
    return all(after[k] < v - EPSILON for k, v in before.items())


def propose_step(rows, delta, config):
    before = diagnostic.losses(rows, delta, config['l2'])
    _, mean = objective(rows, delta, .5, config['l2'])
    audit = diagnostic.audit
    cap = config['delta_limit_cp']
    limit = config['train_position_limit_cp']
    initial = max(abs(audit.dot(r['factors'], delta)) for r in rows)
    if initial > limit or any(abs(v) > cap for v in delta.values()):
        raise ValueError('Infeasible initial delta')
    trials = []
    for method in ('mean', 'unit_group_sum'):
        if method == 'mean':
            gradient = mean
        else:
            groups = audit.groups(rows, delta, .5)
            norms = {g: audit.norm(groups[g]) for g in ('win', 'loss')}
            gradient = {k: sum(groups[g].get(k, 0.) / norms[g] for g in norms if norms[g]) for k in delta}
        maximum = max(map(abs, gradient.values()), default=0.)
        if not maximum:
            trials.append(dict(method=method, reason='zero_gradient'))
            continue
        for backtrack in range(config['max_backtracks'] + 1):
            amount = config['step_cp'] * 2. ** (-backtrack)
            raw = {k: v - amount * gradient[k] / maximum for k, v in delta.items()}
            candidate = {k: max(-cap, min(cap, v)) for k, v in raw.items()}
            used = any(abs(audit.dot(r['factors'], candidate)) > limit for r in rows)
            sweeps = 0
            if used:
                candidate, sweeps = audit.base.optimizer.correct(
                    rows, delta, candidate, amount, cap, limit, **audit.base.optimizer.OPTIONS)
            trial = dict(method=method, backtracks=backtrack, step_cp=amount,
                         correction_used=used, correction_sweeps=sweeps)
            if candidate is None:
                trials.append(dict(trial, reason='infeasible_correction'))
                continue
            impact = max(abs(audit.dot(r['factors'], candidate)) for r in rows)
            actual_step = max(abs(candidate[k] - v) for k, v in delta.items())
            if impact > limit or max(map(abs, candidate.values())) > cap or actual_step > amount + 1e-12:
                raise ValueError('Correction violated bounds')
            after = diagnostic.losses(rows, candidate, config['l2'])
            rejected = [k for k, v in before.items() if not after[k] < v - EPSILON]
            trials.append(dict(trial, reason='accepted' if not rejected else 'group_or_total_guard',
                               rejected_metrics=rejected, changes={k: after[k] - v for k, v in before.items()}))
            if not rejected:
                return dict(delta=candidate, accepted=True, loss_before=before['total_mixed_l2'],
                            loss_after=after['total_mixed_l2'], group_before=before, group_after=after,
                            method=method, max_train_change_cp=impact, actual_max_step=actual_step,
                            stopping_reason=None, trials=trials, **{k: v for k, v in trial.items() if k != 'method'})
    return dict(delta=dict(delta), accepted=False, loss_before=before['total_mixed_l2'],
                loss_after=before['total_mixed_l2'], group_before=before, group_after=before,
                stopping_reason='no_acceptable_improvement', trials=trials)
