import copy
import unittest

from tools.learning.hybrid.optimizer import propose_step


class OptimizerTests(unittest.TestCase):
    def row(self, factor=1.):
        return dict(base_cp=0., teacher_cp=300., target=1, factors={'x': factor})

    def test_decreasing_and_no_mutation(self):
        rows, delta = [self.row()], {'x': 0.}
        saved = copy.deepcopy((rows, delta))
        result = propose_step(rows, delta, .5)
        self.assertTrue(result['accepted'])
        self.assertLess(result['loss_after'], result['loss_before'])
        self.assertEqual(result['delta']['x'], .02)
        self.assertEqual((rows, delta), saved)

    def test_fixed_cap(self):
        result = propose_step([self.row()], {'x': .49}, 1)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['delta']['x'], .5)
        self.assertEqual(result['cap_hits'], 1)
        stopped = propose_step([self.row()], {'x': .5}, 1)
        self.assertFalse(stopped['accepted'])

    def test_training_impact_backtracks(self):
        result = propose_step([self.row(10000.)], {'x': 0.}, 1,
                              train_position_limit_cp=60.)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['backtracks'], 2)
        self.assertLessEqual(result['max_train_change_cp'], 60.)
        self.assertEqual(result['step_cp'], .005)

    def test_training_objective_backtracks(self):
        row = self.row()
        row['teacher_cp'] = 0.
        row['base_cp'] = 1.
        result = propose_step([row], {'x': 0.}, 0, step_cp=10., delta_limit_cp=20.)
        self.assertTrue(result['accepted'])
        self.assertGreater(result['backtracks'], 0)
        self.assertLess(result['loss_after'], result['loss_before'])

    def test_zero_gradient_and_exhaustion(self):
        row = self.row()
        row['teacher_cp'] = 0.
        result = propose_step([row], {'x': 0.}, 0)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['stopping_reason'], 'zero_gradient')
        result = propose_step([self.row(10000.)], {'x': 0.}, 1,
                              train_position_limit_cp=1., max_backtracks=0)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['delta'], {'x': 0.})

    def test_invalid_configuration_and_initial_state(self):
        for kwargs in (dict(step_cp=0), dict(delta_limit_cp=float('nan')),
                       dict(max_backtracks=True), dict(train_position_limit_cp=-1)):
            with self.assertRaises(ValueError):
                propose_step([self.row()], {'x': 0.}, 1, **kwargs)
        with self.assertRaises(ValueError):
            propose_step([self.row()], {'x': .6}, 1)
        with self.assertRaises(ValueError):
            propose_step([self.row(1000.)], {'x': .4}, 1)
