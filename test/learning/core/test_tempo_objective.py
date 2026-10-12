#!/usr/bin/env python3
"""Sign, scaling, saturation and finite-difference checks; no engine updates."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import sys
import unittest
from pathlib import Path

from tools.learning.core.tempo_objective import FrozenLeaf, tempo_factors, objective, check_gradient, sigmoid


class TempoObjectiveTest(unittest.TestCase):
    def test_own_turn_tempo_positive_for_both_colors(self):
        for side in ("black", "white"):
            self.assertEqual(tempo_factors(0, side, side), (.5, 0, 0))
            self.assertEqual(tempo_factors(.5, side, side), (0, .5, 0))
            self.assertEqual(tempo_factors(1, side, side), (0, 0, .5))

    def test_odd_leaf_flips_baseline_and_derivative(self):
        for root, leaf in (("black", "white"), ("white", "black")):
            s = FrozenLeaf(100, 0, 0, root, leaf)
            self.assertEqual(s.predict((2, 0, 0)), -101)
            self.assertEqual(s.factors(), (-.5, 0, 0))

    def test_progress_quantized_and_boundary_continuous(self):
        self.assertEqual(tempo_factors(.25+.25/65536, "black", "black"), (.25, .25, 0))
        for p in (.5-1/65536, .5, .5+1/65536):
            self.assertAlmostEqual(sum(tempo_factors(p, "white", "white")), .5)

    def test_batch_mean_not_sum_and_l2_not_duplicated(self):
        s = FrozenLeaf(-500, 200, .25, "black", "black")
        a, b = objective([s], (1,2,3)), objective([s]*10, (1,2,3))
        self.assertAlmostEqual(a[0], b[0], places=15)
        for x, y in zip(a[1], b[1]):
            self.assertAlmostEqual(x, y, places=15)

    def test_zero_residual_and_regularizer(self):
        s = FrozenLeaf(0, 0, 0, "black", "black")
        self.assertEqual(objective([s], (0,0,0)), (0, (0,0,0)))
        loss, grad = objective([s], (0,2,3), l2=.01)
        self.assertAlmostEqual(loss, .065)
        self.assertEqual(grad, (0,.02,.03))

    def test_finite_difference_sign_and_extreme_scores(self):
        for side, leaf in (("black","black"), ("black","white"),
                           ("white","black"), ("white","white")):
            s = FrozenLeaf(1200, -600, .75, side, leaf)
            self.assertLess(check_gradient([s], (.25,-.5,.75))["max_absolute_error"], 1e-9)
        self.assertEqual(sigmoid(10000), 1)
        self.assertEqual(sigmoid(-10000), 0)

    def test_invalid_progress_nonfinite_and_empty_rejected(self):
        for p in (-.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                tempo_factors(p,"black","white")
        with self.assertRaises(ValueError):
            objective([], (0,0,0))
        s = FrozenLeaf(0,0,.5,"black","black")
        for delta in ((False,0,0), (0,0,float("inf")), (0,0)):
            with self.assertRaises(ValueError):
                objective([s],delta)


if __name__ == "__main__":
    unittest.main()
