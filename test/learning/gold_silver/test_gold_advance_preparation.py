import unittest
from unittest.mock import patch
from tools.learning.gold_silver import gold_advance_preparation as p
from tools.learning.core.king_safety_objective import FrozenLeaf
from tools.learning.core.king_safety_updater import initial,checkpoint,restore


class GoldPreparationTests(unittest.TestCase):
    def test_changed_artifact_rejected_before_search(self):
        with patch.object(p,'digest',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'Bound artifact changed'):p.verify_inputs()

    def test_coefficient_bounds_rejected_before_process(self):
        for raw in ((32769,0),(0,-32769),(0,),(.1,0),(True,0)):
            with self.assertRaises(ValueError):p.GoldAdvanceProbe(raw)

    def test_sfen_counter_and_signed_objective(self):
        # G5f supported by G4g: own fourth rank=2. Mirror reverses net sign.
        black='k8/9/9/9/9/4G4/5G3/9/8K b - 1'
        self.assertEqual(p.independent_counts(black),{'black':2,'white':0})
        a=FrozenLeaf(0,0,.5,'black',(2,0,0,0))
        b=FrozenLeaf(0,0,.5,'white',(2,0,0,0))
        self.assertAlmostEqual(a.predict((.5,.5)+(0,)*6),1)
        self.assertAlmostEqual(b.predict((.5,.5)+(0,)*6),-1)

    def test_zero_checkpoint(self):
        state=initial(p.CONFIG);binding={'feature':p.FEATURE}
        self.assertEqual(restore(checkpoint(state,p.CONFIG,binding),p.CONFIG,binding),state)
        self.assertEqual(state.average(),(0.0,)*8)

    def test_cross_split_leaf_rejected(self):
        parts={s:[dict(row={'id':s,'source':{'run':s}},frame={'root_sfen':s,'leaf_sfen':'same'})]
               for s in ('train','validation')}
        with self.assertRaisesRegex(ValueError,'overlap'):p.disjoint(parts)

if __name__=='__main__':unittest.main()
