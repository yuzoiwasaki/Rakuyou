import unittest
from tools.learning.constraints.common_direction import check,losses
from test.learning.constraints.test_weighted import row


class CommonTests(unittest.TestCase):
    def config(self):return dict(l2=1e-6,step_cp=.02,delta_limit_cp=.5,train_position_limit_cp=100.)

    def test_common_descent_and_no_mutation(self):
        a=dict(row(1),cohort='original',factors={'a':1.,'b':0.})
        b=dict(row(2,0,-300),target=0,cohort='additional',factors={'a':0.,'b':1.})
        delta={'a':0.,'b':0.};result=check([a,b],delta,self.config())
        self.assertEqual(delta,{'a':0.,'b':0.})
        for method in result['methods'].values():
            self.assertTrue(method['found'])
            self.assertTrue(all(x<0 for x in method['trials'][-1]['changes'].values()))

    def test_exact_opposition_does_not_claim_feasibility(self):
        rows=[dict(row(1),cohort='original'),dict(row(2,0,-300),cohort='additional',target=0)]
        r=check(rows,{'a':0.,'b':0.},self.config())
        self.assertFalse(any(v['found'] for v in r['methods'].values()))
        self.assertTrue(all(len(v['trials'])<=7 for v in r['methods'].values()))
