#!/usr/bin/env python3
"""Smooth, frozen-leaf objective for eight king-safety deltas; no optimizer or writes.

The engine's progress is quantized to 1/65536. Final score rounding is excluded
from this differentiable model. Leaves and progress stay fixed during checks.
"""
import math
from dataclasses import dataclass

PROGRESS_SCALE = 65536
GAIN = 1.0 / 600.0


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Expected finite numeric value")
    return value


def vector(delta):
    if len(delta) != 8:
        raise ValueError("Eight safety coefficients required")
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


@dataclass(frozen=True)
class FrozenLeaf:
    base_root_cp: float
    teacher_root_cp: float
    progress: float
    root_side: str
    counts: tuple

    def factors(self):
        finite(self.base_root_cp);finite(self.teacher_root_cp);finite(self.progress)
        if not 0<=self.progress<=1 or self.root_side not in ('black','white') or len(self.counts)!=4:
            raise ValueError('Invalid safety sample')
        p=int(self.progress*PROGRESS_SCALE)/PROGRESS_SCALE
        sign=1 if self.root_side=='black' else -1
        return tuple(sign*finite(count)*weight for count in self.counts for weight in (1-p,p))

    def predict(self,delta):
        return self.base_root_cp+sum(a*b for a,b in zip(self.factors(),vector(delta)))


def objective(samples, delta, l2=1e-4):
    """Mean sigmoid-square loss + (l2/2)*||delta||^2, and its exact gradient.

    Teacher cp is ROOT side-to-move; base cp is LEAF side-to-move.
    Coefficients/delta use cp units before engine score rounding.
    """
    delta = vector(delta)
    finite(l2)
    if l2 < 0 or not samples:
        raise ValueError("Nonempty samples and nonnegative L2 required")
    terms, derivatives = [], [[] for _ in range(8)]
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
    for i in range(8):
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
