import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.constraints import runner_v2 as runner
from tools.learning.constraints import projected as p
from tools.learning.hybrid.optimizer import propose_step as legacy
from test.learning.constraints.test_optimizer import row


class ProjectedTests(unittest.TestCase):
    def test_near_coefficient_cap_does_not_shrink_other_coordinate(self):
        rows=[row({'x':1}),row({'y':1})];delta=dict(x=.499999,y=0.)
        a=legacy(rows,delta,0.);b=p.propose_step(rows,delta,0.)
        self.assertTrue(b['accepted']);self.assertFalse(b['correction_used'])
        for k in a: self.assertEqual(a[k],b[k])
        self.assertEqual(b['delta']['x'],.5)
        self.assertGreater(b['delta']['y'],.019)

    def test_position_boundary_preserved_while_other_shape_improves(self):
        rows=[row({'x':1}),row({'y':1})];delta=dict(x=.1,y=0.)
        b=p.propose_step(rows,delta,0.,train_position_limit_cp=.1)
        self.assertTrue(b['accepted']);self.assertTrue(b['correction_used'])
        self.assertLessEqual(b['delta']['x'],.1)
        self.assertGreater(b['delta']['y'],.019)

    def test_positive_negative_interacting_bounds_over_many_steps(self):
        rows=[row({'x':2,'y':1}),row({'x':1,'y':-2},-1000),row({'z':1})]
        delta=dict(x=0.,y=0.,z=0.);corrected=0
        for _ in range(40):
            b=p.propose_step(rows,delta,.5,train_position_limit_cp=.1,delta_limit_cp=.08)
            if not b['accepted']: break
            corrected+=b['correction_used']
            self.assertTrue(all(abs(p.dot(r['factors'],b['delta']))<=.1 for r in rows))
            self.assertTrue(all(abs(x)<=.08 for x in b['delta'].values()))
            self.assertTrue(all(abs(b['delta'][k]-delta[k])<=b['step_cp']+1e-16 for k in delta))
            delta=b['delta']
        self.assertGreater(corrected,0)

    def test_no_descent_at_saturated_coefficient(self):
        b=p.propose_step([row({'x':1})],dict(x=.5),0.)
        self.assertFalse(b['accepted'])
        self.assertEqual(b['stopping_reason'],'no_acceptable_improvement')

    def test_runner_restart_and_finished_run(self):
        rows=[row({'x':1}),row({'y':2},-400)]
        config=dict(max_updates=8,save_updates=[0,8],step_cp=.02,delta_limit_cp=.5,
                    train_position_limit_cp=.1,max_backtracks=20,l2=1e-6)
        binding=dict(alpha=0.)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            args=(rows,['x','y'],0.,config,binding)
            expected=runner.train_arm(*args,root/'full','projected',p.OPTIONS)
            actual=p.propose_step;calls=0
            def interrupted(*args,**kwargs):
                nonlocal calls
                calls+=1
                if calls==4:raise KeyboardInterrupt()
                return actual(*args,**kwargs)
            with patch.object(p,'propose_step',side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt):
                    runner.train_arm(*args,root/'resume','projected',p.OPTIONS)
            got=runner.train_arm(*args,root/'resume','projected',p.OPTIONS)
            self.assertEqual(expected,got)
            with patch.object(p,'propose_step',side_effect=AssertionError('rerun')):
                self.assertEqual(got,runner.train_arm(*args,root/'resume','projected',p.OPTIONS))

    def test_nonfinite_and_invalid_budgets(self):
        for kwargs in [dict(max_sweeps=0),dict(interior_margin=float('nan')),dict(max_backtracks=-1)]:
            with self.assertRaises(ValueError):p.propose_step([row({'x':1})],dict(x=0.),0.,**kwargs)


if __name__=='__main__':unittest.main()
