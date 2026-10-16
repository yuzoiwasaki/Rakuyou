"""Bounded full-batch gradient descent with training-only backtracking.

Training improvement is an arithmetic acceptance rule, not a generalization claim.
The position bound measures total overlay relative to the frozen baseline.
"""
import math

from .objective import finite, objective


def propose_step(rows, delta, alpha, *, l2=1e-6, step_cp=.02,
                 delta_limit_cp=.5, train_position_limit_cp=100,
                 max_backtracks=20):
    for name, value in [('step_cp', step_cp), ('delta_limit_cp', delta_limit_cp),
                        ('train_position_limit_cp', train_position_limit_cp)]:
        finite(value, name)
        if value <= 0:
            raise ValueError(f'{name} must be positive')
    if type(max_backtracks) is not int or max_backtracks < 0:
        raise ValueError('max_backtracks must be a nonnegative integer')
    before, gradient = objective(rows, delta, alpha, l2)
    if any(abs(value) > delta_limit_cp for value in delta.values()):
        raise ValueError('initial delta exceeds coefficient cap')

    def impact(candidate):
        return max(abs(math.fsum(v * candidate[k] for k, v in row['factors'].items())) for row in rows)

    initial_impact = impact(delta)
    if initial_impact > train_position_limit_cp:
        raise ValueError('initial delta exceeds training position cap')
    maximum = max((abs(v) for v in gradient.values()), default=0.0)
    result = dict(delta=dict(delta), loss_before=before, loss_after=before,
                  accepted=False, step_cp=0.0, backtracks=0,
                  gradient_max=maximum, max_train_change_cp=initial_impact,
                  cap_hits=0, stopping_reason='zero_gradient')
    if maximum == 0:
        return result
    for backtracks in range(max_backtracks + 1):
        amount = step_cp * 2.0 ** (-backtracks)
        proposed = {k: value - amount * (gradient[k] / maximum) for k, value in delta.items()}
        cap_hits = sum(abs(value) > delta_limit_cp for value in proposed.values())
        candidate = {k: max(-delta_limit_cp, min(delta_limit_cp, value)) for k, value in proposed.items()}
        max_change = impact(candidate)
        if max_change <= train_position_limit_cp:
            after, _ = objective(rows, candidate, alpha, l2)
            if after < before:
                result.update(delta=candidate, loss_after=after, accepted=True,
                              step_cp=amount, backtracks=backtracks,
                              max_train_change_cp=max_change, cap_hits=cap_hits,
                              stopping_reason=None)
                return result
    result.update(backtracks=max_backtracks, stopping_reason='no_acceptable_improvement')
    return result
