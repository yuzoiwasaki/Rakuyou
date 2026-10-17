import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.learning.constraints import optimizer as o, runner as r
from tools.learning.hybrid.optimizer import propose_step as legacy


def row(factors,teacher=1000):
    return dict(base_cp=0.,teacher_cp=teacher,target=1.,factors=factors)


class OptimizerTests(unittest.TestCase):
    def test_boundary_allows_other_shape_to_improve(self):
        rows=[row({'x':1}),row({'y':1})];delta=dict(x=.1,y=0.)
        options=dict(train_position_limit_cp=.1,delta_limit_cp=1.,l2=0.)
        self.assertFalse(legacy(rows,delta,0.,**options)['accepted'])
        result=o.propose_step(rows,delta,0.,**options)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['delta']['x'],.1)
        self.assertGreater(result['delta']['y'],0)
        self.assertLess(result['loss_after'],result['loss_before'])

    def test_repeated_interacting_constraints_remain_feasible(self):
        rows=[row({'x':2.,'y':1.}),row({'x':1.,'y':-2.},-500),row({'z':1.})]
        delta=dict(x=0.,y=0.,z=0.)
        accepted=0
        for _ in range(80):
            result=o.propose_step(rows,delta,.5,train_position_limit_cp=.1,delta_limit_cp=.08)
            if not result['accepted']: break
            accepted+=1;delta=result['delta']
            self.assertLess(result['loss_after'],result['loss_before'])
            self.assertLessEqual(max(map(abs,delta.values())),.08)
            self.assertTrue(all(abs(o.dot(x['factors'],delta))<=.1 for x in rows))
        self.assertGreater(accepted,5)

    def test_no_free_direction_stops_without_claiming_convergence(self):
        result=o.propose_step([row({'x':1})],dict(x=.5),0.)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['stopping_reason'],'no_descent_direction')

    def test_nonfinite_and_infeasible_rejected(self):
        for value in (math.nan, math.inf, .6):
            with self.assertRaises(ValueError):
                o.propose_step([row({'x':1})],dict(x=value),0.)

    def test_negative_boundary(self):
        result=o.propose_step([row({'x':1},-1000),row({'y':1})],dict(x=-.1,y=0.),0.,
                              train_position_limit_cp=.1,l2=0.)
        self.assertTrue(result['accepted']);self.assertEqual(result['delta']['x'],-.1)

    def test_direction_iteration_limit_is_explicit(self):
        # Position correction pushes x outward; clipping x reopens that plane.
        with patch.object(o, 'objective', return_value=(1.,dict(x=-1.,y=-1.))):
            result=o.propose_step([row({'x':-1.,'y':2.})],dict(x=.5,y=.4),0.,
                                  train_position_limit_cp=.3000000000000001,max_sweeps=1)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['stopping_reason'],'direction_iteration_limit')

    def test_budget_and_minimum_step(self):
        with self.assertRaises(ValueError):
            o.propose_step([row({'x':1})],dict(x=0.),0.,max_sweeps=0)
        result=o.propose_step([row({'x':1})],dict(x=0.),0.,minimum_step=1.)
        self.assertEqual(result['stopping_reason'],'step_too_small')

    def test_interrupted_training_resumes_identically(self):
        rows=[row({'x':1}),row({'y':2},-400)]
        config=dict(max_updates=8,save_updates=[0,4,8],step_cp=.02,delta_limit_cp=.5,
                    train_position_limit_cp=100.,max_backtracks=20,l2=1e-6)
        binding=dict(alpha=0.)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            expected=r.train_arm(rows,['x','y'],0.,config,binding,root/'full','direction',o.OPTIONS)
            actual_step=o.propose_step;calls=0
            def interrupt(*args,**kwargs):
                nonlocal calls
                calls+=1
                if calls==4: raise KeyboardInterrupt()
                return actual_step(*args,**kwargs)
            with patch.object(o,'propose_step',side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    r.train_arm(rows,['x','y'],0.,config,binding,root/'resume','direction',o.OPTIONS)
            got=r.train_arm(rows,['x','y'],0.,config,binding,root/'resume','direction',o.OPTIONS)
            self.assertEqual(got,expected)
            with patch.object(o,'propose_step',side_effect=AssertionError('rerun')):
                self.assertEqual(r.train_arm(rows,['x','y'],0.,config,binding,root/'resume','direction',o.OPTIONS),got)


if __name__=='__main__': unittest.main()
