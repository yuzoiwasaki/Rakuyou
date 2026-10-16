import math
import unittest

from tools.learning.hybrid.objective import objective, predict, sigmoid


class ObjectiveTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(base_cp=120., teacher_cp=-80., target=1,
                          factors={'KP:1': 2., 'PP:2': -3.}),
                     dict(base_cp=-210., teacher_cp=300., target=0,
                          factors={'KP:1': -1.})]
        self.delta = {'KP:1': .1, 'PP:2': -.2, 'unused': .3}

    def test_finite_difference_all_keys(self):
        for alpha in (0, .5, 1):
            _, gradient = objective(self.rows, self.delta, alpha)
            for key in self.delta:
                plus, minus = dict(self.delta), dict(self.delta)
                plus[key] += 1e-4
                minus[key] -= 1e-4
                numeric = (objective(self.rows, plus, alpha)[0] - objective(self.rows, minus, alpha)[0]) / 2e-4
                self.assertAlmostEqual(gradient[key], numeric, places=10)

    def test_mixture_and_search_endpoint(self):
        search = objective(self.rows, self.delta, 0)
        outcome = objective(self.rows, self.delta, 1)
        mixed = objective(self.rows, self.delta, .5)
        self.assertAlmostEqual(mixed[0], (search[0] + outcome[0]) / 2)
        for key in self.delta:
            self.assertAlmostEqual(mixed[1][key], (search[1][key] + outcome[1][key]) / 2)
        row = dict(base_cp=120., teacher_cp=120., target=0, factors={'x': 1.})
        self.assertEqual(objective([row], {'x': 0.}, 0)[1]['x'], 0.)

    def test_caller_orients_winning_white_as_target_one(self):
        row = dict(base_cp=0., teacher_cp=0., target=1, factors={'x': 1.})
        self.assertLess(objective([row], {'x': 0.}, 1)[1]['x'], 0)
        self.assertLess(objective([row], {'x': 10.}, 1)[0], objective([row], {'x': 0.}, 1)[0])
        row['target'] = 0
        self.assertGreater(objective([row], {'x': 0.}, 1)[1]['x'], 0)

    def test_stable_extremes_and_predict(self):
        self.assertEqual(sigmoid(-1e300), 0.)
        self.assertEqual(sigmoid(1e300), 1.)
        for score in (-1e300, 1e300):
            row = dict(base_cp=score, teacher_cp=-score, target=1, factors={})
            self.assertTrue(math.isfinite(objective([row], {}, .5)[0]))
        self.assertAlmostEqual(predict(self.rows[0], self.delta), 120.8)

    def test_invalid_data(self):
        for alpha in (-1, 2, float('nan'), True):
            with self.assertRaises(ValueError):
                objective(self.rows, self.delta, alpha)
        for field, value in [('base_cp', float('inf')), ('teacher_cp', None),
                             ('target', .5), ('factors', {'missing': 1.}),
                             ('factors', {'KP:1': float('nan')})]:
            row = dict(self.rows[0], **{field: value})
            with self.assertRaises(ValueError):
                objective([row], self.delta, .5)
        for delta in ({'KP:1': float('inf')}, {1: 0.}, None):
            with self.assertRaises(ValueError):
                objective(self.rows, delta, .5)
        with self.assertRaises(ValueError):
            objective([], {}, .5)
