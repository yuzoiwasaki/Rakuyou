import unittest
from tools.learning.outcome import king_gold_comparison as p
class KingGoldTests(unittest.TestCase):
    def record(self):return dict(stopped_early=False,bestmove='7a8b',candidates=[dict(depth=20,score_type='cp',score='0',pv=[m],raw='info score cp 0') for m in p.MOVES])
    def test_both_fixed_moves_required(self):
        r=self.record();p.validate_result(r,20);r['candidates'][1]['pv']=['9c9d']
        with self.assertRaises(ValueError):p.validate_result(r,20)
    def test_incomplete_depth_and_bound_rejected(self):
        r=self.record();r['candidates'][1]['depth']=19
        with self.assertRaises(ValueError):p.validate_result(r,20)
        r=self.record();r['candidates'][0]['raw']+=' lowerbound'
        with self.assertRaises(ValueError):p.validate_result(r,20)
if __name__=='__main__':unittest.main()
