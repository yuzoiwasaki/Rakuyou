import unittest,math
from tools.learning.outcome.outcome_objective import objective
from tools.learning.data.prepare_learning_data import outcome
class OutcomeObjectiveTests(unittest.TestCase):
    def sample(self,target):return dict(target=target,use_outcome_loss=True,base_cp=100,factors={'x':2,'y':-.5})
    def test_winner_moves_score_up_loser_down(self):
        self.assertLess(objective([self.sample(1)],{})[1]['x'],0)
        self.assertGreater(objective([self.sample(0)],{})[1]['x'],0)
    def test_gradient_including_l2(self):
        rows=[self.sample(0),dict(self.sample(1),base_cp=-200)];delta={'x':.003,'y':-.002}
        _,g=objective(rows,delta,1e-6)
        for k in delta:
            h=.001;a=dict(delta);b=dict(delta);a[k]+=h;b[k]-=h
            self.assertAlmostEqual((objective(rows,a,1e-6)[0]-objective(rows,b,1e-6)[0])/(2*h),g[k],places=10)
    def test_masked_draw_not_in_gradient_or_denominator(self):
        draw=dict(target=None,use_outcome_loss=False,base_cp=0,factors={'draw_only':1})
        self.assertEqual(objective([self.sample(1)],{}),objective([self.sample(1),draw],{}))
        with self.assertRaises(ValueError):objective([dict(draw,target=1)],{})
    def test_white_win_labels_and_truncated_draw(self):
        g=dict(result='white_win',reason='resign')
        self.assertEqual(outcome(g,'white')['target'],1)
        self.assertEqual(outcome(g,'black')['target'],0)
        self.assertFalse(outcome(dict(result='draw',reason='max_plies'),'white')['use_outcome_loss'])
    def test_color_reversal_preserves_loss(self):
        a=dict(self.sample(1),base_cp=150,factors={'x':1})
        b=dict(self.sample(0),base_cp=-150,factors={'x':-1})
        self.assertAlmostEqual(objective([a],{'x':.01})[0],objective([b],{'x':.01})[0])
    def test_extreme_scores_finite(self):
        for cp in (1e9,-1e9):self.assertTrue(math.isfinite(objective([dict(self.sample(1),base_cp=cp)],{})[0]))
if __name__=='__main__':unittest.main()
