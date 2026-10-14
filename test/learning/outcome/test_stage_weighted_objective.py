import copy
import math
import unittest
from tools.learning.outcome import stage_weighted_objective as w
from tools.learning.outcome.outcome_objective import objective as equal_objective


def records():
    result = []
    for side in ('black', 'white'):
        for target in (0., 1.):
            for i in range(64):
                result.append(dict(row={'side_to_move': side}, features={'progress': i/63},
                    sample=dict(base_cp=100, factors={'x': 1, 'y': -.4}, target=target, use_outcome_loss=True)))
    result.append(dict(sample=dict(target=None, use_outcome_loss=False)))
    return result


class StageWeightedObjectiveTest(unittest.TestCase):
    def test_strata_and_draw_mask(self):
        rows = w.training_samples(records())
        self.assertEqual(len(rows), 256)
        for start in range(0, 256, 64):
            self.assertAlmostEqual(math.fsum(x['weight'] for x in rows[start:start+64]), 64)
            self.assertLess(rows[start]['weight'], rows[start+63]['weight'])

    def test_finite_gradient(self):
        rows = w.training_samples(records())
        rows[0]['base_cp'] = -250
        delta = {'x': .02, 'y': -.03}
        _, gradient = w.objective(rows, delta, 1e-6)
        for key in delta:
            plus, minus = dict(delta), dict(delta)
            plus[key] += .001
            minus[key] -= .001
            finite = (w.objective(rows, plus, 1e-6)[0]-w.objective(rows, minus, 1e-6)[0])/.002
            self.assertAlmostEqual(gradient[key], finite, delta=1e-9)

    def test_equal_weights_reproduce_old_objective(self):
        rows = [{**r['sample'], 'weight': 1} for r in records()[:-1]]
        self.assertEqual(w.objective(rows, {'x': .1}, 1e-6), equal_objective(rows, {'x': .1}, 1e-6))

    def test_invalid_weights_and_membership(self):
        rows = w.training_samples(records())
        for invalid in (0, -1, float('nan'), True):
            changed = copy.deepcopy(rows)
            changed[0]['weight'] = invalid
            with self.assertRaises(ValueError): w.objective(changed, {})
        with self.assertRaises(ValueError): w.training_samples(records()[1:])
