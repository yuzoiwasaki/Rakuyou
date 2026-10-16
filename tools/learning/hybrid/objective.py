"""Stable logistic loss on caller-supplied, consistently oriented root scores.

Draw masking and score/label perspective conversion belong to preparation.
All supplied rows must have decisive binary targets, including search-only rows.
"""
import math

SCALE_CP = 600.0


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return value


def sigmoid(value):
    finite(value, 'logit')
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def validate_delta(delta):
    if not isinstance(delta, dict):
        raise ValueError('delta must be a dictionary')
    for key, value in delta.items():
        if not isinstance(key, str) or not key:
            raise ValueError('delta keys must be nonempty canonical strings')
        finite(value, 'delta')


def validate_row(row, delta):
    if not isinstance(row, dict):
        raise ValueError('row must be a dictionary')
    try:
        finite(row['base_cp'], 'base_cp')
        finite(row['teacher_cp'], 'teacher_cp')
        finite(row['target'], 'target')
        if row['target'] not in (0, 1):
            raise ValueError('target must be zero or one')
        factors = row['factors']
        if not isinstance(factors, dict):
            raise ValueError('factors must be a dictionary')
        for key, value in factors.items():
            if not isinstance(key, str) or not key or key not in delta:
                raise ValueError('factor key missing from delta')
            finite(value, 'factor')
    except KeyError as error:
        raise ValueError(f'missing row field: {error}') from error


def predict(row, delta):
    """Return smooth root score in cp; no rounding or native evaluation."""
    validate_delta(delta)
    validate_row(row, delta)
    return _score(row, delta)


def _score(row, delta):
    try:
        score = math.fsum([row['base_cp']] + [v * delta[k] for k, v in row['factors'].items()])
    except (OverflowError, ValueError) as error:
        raise ValueError('nonfinite predicted score') from error
    return finite(score, 'predicted score')


def objective(rows, delta, alpha, l2=1e-6):
    """Return mean cross entropy plus delta L2, and its full gradient."""
    finite(alpha, 'alpha')
    finite(l2, 'l2')
    if not 0 <= alpha <= 1 or l2 < 0:
        raise ValueError('alpha must be in [0,1] and l2 nonnegative')
    validate_delta(delta)
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError('nonempty rows required')
    gradient = {key: l2 * value for key, value in delta.items()}
    losses = []
    for row in rows:
        validate_row(row, delta)
        z = _score(row, delta) / SCALE_CP
        target = (1 - alpha) * sigmoid(row['teacher_cp'] / SCALE_CP) + alpha * row['target']
        # This form avoids exp overflow and subtraction of two huge logits.
        losses.append((1 - target) * max(z, 0) + target * max(-z, 0) + math.log1p(math.exp(-abs(z))))
        derivative = (sigmoid(z) - target) / (SCALE_CP * len(rows))
        for key, factor in row['factors'].items():
            gradient[key] += derivative * factor
    try:
        loss = math.fsum(losses) / len(rows) + .5 * l2 * math.fsum(v * v for v in delta.values())
    except (OverflowError, ValueError) as error:
        raise ValueError('nonfinite objective') from error
    finite(loss, 'loss')
    for value in gradient.values():
        finite(value, 'gradient')
    return loss, gradient
