#!/usr/bin/env python3
"""Smooth, frozen-leaf objective for three tempo deltas; no optimizer or writes.

The engine's progress is quantized to 1/65536. Final score rounding is excluded
from this differentiable model. Leaves and progress stay fixed during checks.
"""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import math
from dataclasses import dataclass

PROGRESS_SCALE = 65536
GAIN = 1.0 / 600.0


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Expected finite numeric value")
    return value


def vector(delta):
    if len(delta) != 3:
        raise ValueError("Three tempo coefficients required")
    return tuple(finite(x) for x in delta)


def sigmoid(x):
    finite(x)
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def leaf_sign(root_side, leaf_side):
    if root_side not in ("black", "white") or leaf_side not in ("black", "white"):
        raise ValueError("Invalid root/leaf side")
    return 1.0 if root_side == leaf_side else -1.0


def tempo_factors(progress, root_side, leaf_side):
    finite(progress)
    if not 0 <= progress <= 1:
        raise ValueError("Progress outside [0,1]")
    p = int(progress * PROGRESS_SCALE) / PROGRESS_SCALE
    weights = (1-2*p, 2*p, 0.0) if p < .5 else (0.0, 2-2*p, 2*p-1)
    # Tempo contributes +1/2 in either leaf's OWN side-to-move score.
    sign = leaf_sign(root_side, leaf_side)
    return tuple(sign * .5 * w for w in weights)


@dataclass(frozen=True)
class FrozenLeaf:
    base_leaf_cp: float
    teacher_root_cp: float
    progress: float
    root_side: str
    leaf_side: str

    def factors(self):
        finite(self.base_leaf_cp)
        finite(self.teacher_root_cp)
        return tempo_factors(self.progress, self.root_side, self.leaf_side)

    def predict(self, delta):
        factors = self.factors()
        delta = vector(delta)
        return leaf_sign(self.root_side, self.leaf_side) * self.base_leaf_cp + sum(
            a*b for a, b in zip(factors, delta))


def objective(samples, delta, l2=1e-4):
    """Mean sigmoid-square loss + (l2/2)*||delta||^2, and its exact gradient.

    Teacher cp is ROOT side-to-move; base cp is LEAF side-to-move.
    Coefficients/delta use cp units before engine score rounding.
    """
    delta = vector(delta)
    finite(l2)
    if l2 < 0 or not samples:
        raise ValueError("Nonempty samples and nonnegative L2 required")
    terms, derivatives = [], [[], [], []]
    for sample in samples:
        y = sigmoid(GAIN * sample.predict(delta))
        t = sigmoid(GAIN * finite(sample.teacher_root_cp))
        terms.append((y-t)**2)
        d_score = 2.0 * GAIN * (y-t) * y * (1-y)
        for i, a in enumerate(sample.factors()):
            derivatives[i].append(d_score*a)
    n = len(samples)
    loss = math.fsum(terms)/n + .5*l2*math.fsum(d*d for d in delta)
    gradient = tuple(math.fsum(g)/n + l2*d for g, d in zip(derivatives, delta))
    return loss, gradient


def finite_difference(samples, delta, l2=1e-4, epsilon=1e-3):
    delta = vector(delta)
    finite(epsilon)
    if epsilon <= 0:
        raise ValueError("Positive finite-difference step required")
    result = []
    for i in range(3):
        plus, minus = list(delta), list(delta)
        plus[i] += epsilon; minus[i] -= epsilon
        result.append((objective(samples, plus, l2)[0] - objective(samples, minus, l2)[0]) / (2*epsilon))
    return tuple(result)


def check_gradient(samples, delta, l2=1e-4, epsilon=1e-3):
    loss, analytical = objective(samples, delta, l2)
    numerical = finite_difference(samples, delta, l2, epsilon)
    errors = [abs(a-b) for a, b in zip(analytical, numerical)]
    if any(e > 1e-9 + 1e-6*max(abs(a), abs(b))
           for e, a, b in zip(errors, analytical, numerical)):
        raise ValueError("Gradient finite-difference check failed")
    return dict(loss=loss, analytical=list(analytical), numerical=list(numerical),
                max_absolute_error=max(errors), epsilon_cp=epsilon, l2=l2,
                mathematical_delta_cp=list(delta))
