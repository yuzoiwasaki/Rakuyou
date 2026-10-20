import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.learning.constraints import group_guarded as opt
from tools.learning.constraints import temporal_guarded as runner
from test.learning.constraints.test_weighted import row


class GuardTests(unittest.TestCase):
    def config(self):
        return dict(l2=1e-6, step_cp=.02, delta_limit_cp=.5, train_position_limit_cp=100.,
                    max_backtracks=20, max_updates=2, save_updates=[0, 1, 2])

    def rows(self):
        return [dict(row(1), cohort='original', factors={'a':1., 'b':0.}),
                dict(row(2, 0, -300), target=0, cohort='additional', factors={'a':0., 'b':1.})]

    def test_mean_first_and_strict_groups(self):
        delta = {'a':0., 'b':0.}
        p = opt.propose_step(self.rows(), delta, self.config())
        self.assertTrue(p['accepted'])
        self.assertEqual(p['method'], 'mean')
        self.assertTrue(opt.improves(p['group_before'], p['group_after']))
        self.assertEqual(delta, {'a':0., 'b':0.})

    def test_fallback_when_mean_hurts_loss_group(self):
        rows = self.rows()
        rows[0]['factors'] = {'a':10., 'b':1.}
        rows[1]['factors'] = {'a':1., 'b':1.}
        p = opt.propose_step(rows, {'a':0., 'b':0.}, self.config())
        self.assertTrue(p['accepted'])
        self.assertEqual(p['method'], 'unit_group_sum')
        self.assertTrue(opt.improves(p['group_before'], p['group_after']))
        self.assertEqual(len([t for t in p['trials'] if t['method']=='mean']),21)

    def test_opposition_stops_without_change(self):
        rows = self.rows()
        for r in rows:r['factors'] = {'a':1., 'b':0.}
        p = opt.propose_step(rows, {'a':0., 'b':0.}, self.config())
        self.assertFalse(p['accepted'])
        self.assertEqual(p['delta'], {'a':0., 'b':0.})
        self.assertLessEqual(len(p['trials']),42)

    def test_position_correction_and_resume(self):
        rows = self.rows()
        for r in rows:r['factors']={k:v*100 for k,v in r['factors'].items()}
        cfg = dict(self.config(), train_position_limit_cp=.1)
        binding = dict(plan_sha256='test', method='group-guarded', arm='mixed', alpha=.5)
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'run'
            state=runner.train_arm(rows, ['a','b'], cfg, binding, directory)
            self.assertGreater(state['updates'],0)
            self.assertTrue(state['trajectory'][0]['correction_used'])
            for r in rows:self.assertLessEqual(abs(opt.diagnostic.audit.dot(r['factors'],state['delta'])),.1)
            with patch.object(opt,'propose_step',side_effect=AssertionError('Must not retrain')):
                self.assertEqual(state,runner.train_arm(rows,['a','b'],cfg,binding,directory))
            state['trajectory'][0]['group_after']['loss_outcome'] += 1
            with self.assertRaises(ValueError):runner.validate(state,['a','b'],binding,cfg,rows)

    def test_plan_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)
            runner.base.old.seal(output/'plan.json',{'schema':'old'})
            with patch.object(runner,'specification',return_value={'schema':'new'}):
                with self.assertRaises(ValueError):runner.load(output)


if __name__ == '__main__':unittest.main()
