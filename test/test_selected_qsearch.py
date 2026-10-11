#!/usr/bin/env python3
"""PV changes and held-out loss direction must be observed without reselection."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"tools"))
from check_selected_qsearch import compare_frames,summarize


def frame(score=0,pv=None):
    pv=pv or []
    return dict(ok=True,root_sfen="root",root_side="black",pv=pv,leaf_sfen="leaf"+str(len(pv)),
                leaf_side="white" if len(pv)%2 else "black",
                qscore=score,leaf_eval_cached=-score if len(pv)%2 else score,
                leaf_eval_full=-score if len(pv)%2 else score,leaf_repetition=False,leaf_in_check=False)


class SelectedQsearchTest(unittest.TestCase):
    def row(self):return dict(id="id",run="run",stratum="black:draw",sfen="root",side_to_move="black",teacher_cp=10)

    def test_score_and_pv_changes_recorded(self):
        r=compare_frames(self.row(),frame(),frame(1,["7g7f"]))
        self.assertEqual(r["cp_change"],1)
        self.assertTrue(r["pv_changed"] and r["leaf_changed"])
        s=summarize([r]);self.assertEqual(s["score_changed"],1)
        self.assertLess(s["raw_sigmoid_loss_candidate"],s["raw_sigmoid_loss_base"])

    def test_regression_is_not_hidden(self):
        r=compare_frames(self.row(),frame(),frame(-1))
        s=summarize([r])
        self.assertGreater(s["raw_sigmoid_loss_candidate"],s["raw_sigmoid_loss_base"])

    def test_root_mismatch_rejected(self):
        f=frame();f["root_sfen"]="other"
        with self.assertRaises(ValueError):compare_frames(self.row(),frame(),f)

    def test_special_return_excluded_from_loss(self):
        r=compare_frames(self.row(),frame(),frame(32000))
        self.assertNotIn("cp_change",r)
        self.assertEqual(summarize([r])["comparable"],0)


if __name__=="__main__":unittest.main()
