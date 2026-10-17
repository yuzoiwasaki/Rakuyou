import unittest
from tools.learning.constraints.audit import direction, feasible_step, dot


class ConstraintDirectionTests(unittest.TestCase):
    def test_other_coordinate_can_improve_at_boundary(self):
        rows=[dict(factors={'x':1.})];delta=dict(x=100.,y=0.);g=dict(x=-1.,y=-2.)
        v,_=direction(rows,delta,g,coefficient_limit=200.)
        self.assertAlmostEqual(v['x'],0.)
        self.assertLess(dot(g,v),0.)
        self.assertGreater(feasible_step(rows,delta,v,coefficient_limit=200.),0.)

    def test_interacting_position_and_coefficient_constraints(self):
        rows=[dict(factors={'x':1.,'y':1.})];delta=dict(x=.5,y=.5);g=dict(x=-2.,y=1.)
        v,_=direction(rows,delta,g,limit=1.)
        self.assertLessEqual(v['x'],0.)
        self.assertLessEqual(v['y'],0.)
        self.assertLessEqual(sum(v.values()),1e-10)

    def test_inactive_constraint_limits_finite_step(self):
        rows=[dict(factors={'x':10.})];delta=dict(x=9.9);v=dict(x=1.)
        step=feasible_step(rows,delta,v,coefficient_limit=200.,step=1.)
        self.assertAlmostEqual(step,.099)
        self.assertLess(10*(delta['x']+step),100.)

    def test_negative_boundary(self):
        rows=[dict(factors={'x':1.})];delta=dict(x=-100.,y=0.);g=dict(x=1.,y=2.)
        v,_=direction(rows,delta,g,coefficient_limit=200.)
        self.assertGreaterEqual(v['x'],-1e-10)
        self.assertLess(dot(g,v),0.)


if __name__=='__main__': unittest.main()
