import unittest
from tools.learning.constraints.conflict_audit import groups,diagnose
from tools.learning.constraints.weighted_objective import objective
from test.learning.constraints.test_weighted import row


class ConflictTests(unittest.TestCase):
    def test_full_cohort_weights_preserved_in_groups(self):
        rows=[dict(row(1),cohort='original'),dict(row(1,50),cohort='additional'),dict(row(2,200,-300),target=0,cohort='original')]
        delta={'a':.1,'b':-.2};gs=groups(rows,delta,.5);_,g=objective(rows,delta,.5,0)
        for a,b in [('win','loss'),('original','additional')]:
            for k in delta:self.assertAlmostEqual(gs[a].get(k,0)+gs[b].get(k,0),g[k],places=14)

    def test_hypothetical_step_does_not_mutate(self):
        rows=[dict(row(1),cohort='original'),dict(row(2,200,-300),target=0,cohort='additional')]
        delta={'a':0.,'b':0.};before=dict(delta)
        result=diagnose(rows,delta,.5,dict(l2=1e-6,step_cp=.02,delta_limit_cp=.5,train_position_limit_cp=.001))
        self.assertEqual(delta,before)
        self.assertLessEqual(result['hypothetical_steps']['position_corrected']['max_position_change'],.001)
