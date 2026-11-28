"""Boundary checks for the offline, annotated move-selection experiment."""
import unittest
from tools.analysis.defense_preference_audit import select


def cp(move, score, depth=18):
    return dict(pv=[move], score=str(score), depth=depth, score_type='cp')


class DefensePreferenceTest(unittest.TestCase):
    def decide(self, rows, **kwargs):
        return select(rows,['P*6d','5b4c'],['8e8f'],**kwargs)

    def test_threshold_and_best_defense(self):
        r=self.decide([cp('8e8f',-100),cp('P*6d',-150),cp('5b4c',-149)])
        self.assertEqual(r['selected'],'5b4c')
        self.assertEqual(self.decide([cp('8e8f',-100),cp('P*6d',-150)])['selected'],'P*6d')
        self.assertEqual(self.decide([cp('8e8f',-100),cp('P*6d',-151)])['selected'],'8e8f')

    def test_eligibility_unknown_role_and_existing_defense(self):
        rows=[cp('8e8f',-100),cp('P*6d',-120)]
        self.assertEqual(self.decide(rows,eligible=False)['selected'],'8e8f')
        self.assertEqual(self.decide([cp('4d3c',0)]+rows)['selected'],'4d3c')
        self.assertEqual(self.decide([cp('P*6d',0),cp('8e8f',-10)])['selected'],'P*6d')

    def test_mixed_depth_bounds_and_mate_are_not_compared(self):
        self.assertIsNone(self.decide([cp('8e8f',0,18),cp('P*6d',-20,17)])['selected'])
        bound=cp('8e8f',0);bound['raw']='info score cp 0 lowerbound'
        self.assertIsNone(self.decide([bound,cp('P*6d',-20)])['selected'])
        mate=cp('8e8f',3);mate['score_type']='mate'
        self.assertIsNone(self.decide([mate,cp('P*6d',-20)])['selected'])


if __name__=='__main__': unittest.main()
