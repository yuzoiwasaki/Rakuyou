#!/usr/bin/env python3
"""Qsearch return values must identify valid, sign-correct static PV leaves."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import sys
import unittest
from pathlib import Path

from tools.learning.checks.check_qsearch_leaves import eligibility, select_roots
from tools.learning.data.prepare_learning_data import ROOT, Probe


class LeafEligibilityTest(unittest.TestCase):
    def fixture(self):
        return dict(ok=True,qscore=-15,pv=["3a2b"],root_side="white",leaf_side="black",
                    leaf_eval_cached=15,leaf_eval_full=15,leaf_repetition=False,leaf_in_check=False)

    def test_turn_conversion_and_mismatch_rejection(self):
        f=self.fixture()
        self.assertIsNone(eligibility(f))
        f["qscore"]=15
        self.assertEqual(eligibility(f),"qscore_not_static_leaf")
        f["leaf_side"]="white"
        with self.assertRaises(ValueError):eligibility(f)

    def test_nonstatic_terminal_excluded(self):
        for changed,reason in ((dict(qscore=32000),"known_win_or_mate"),
                               (dict(leaf_repetition=True),"repetition_or_shek"),
                               (dict(leaf_in_check=True),"nonstatic_terminal")):
            self.assertEqual(eligibility({**self.fixture(),**changed}),reason)

    def test_incremental_mismatch_is_error(self):
        f=self.fixture();f["leaf_eval_cached"]=14
        with self.assertRaises(ValueError):eligibility(f)

    def test_bounded_stratified_roots(self):
        rows=[dict(stratum=s,id=i) for s in ("white:draw","black:draw") for i in range(100)]
        selected=select_roots(rows)
        self.assertEqual(len(selected),64)
        self.assertEqual(sum(r["stratum"]=="white:draw" for r in selected),32)

    def test_qsearch_cannot_run_perturbed(self):
        with self.assertRaises(ValueError):
            Probe("unused","unused",qsearch_progress="unused",tempo_raw=(1,0,0))


class NativeLeafTest(unittest.TestCase):
    def test_empty_and_odd_pv_leaves(self):
        binary=ROOT/"results/learning-tools/learning-data-probe"
        if not binary.exists() or not (ROOT/"bin/params.bin").exists():
            self.skipTest("Native probe/data unavailable")
        probe=Probe(binary,ROOT/"bin/params.bin",qsearch_progress=ROOT/"bin/progress.bin")
        try:
            quiet=probe.replay([])
            capture=probe.replay(["7g7f","3c3d","8h2b+"])
            self.assertIsNone(eligibility(quiet))
            self.assertEqual(quiet["pv"],[])
            self.assertIsNone(eligibility(capture))
            self.assertEqual(capture["pv"],["3a2b"])
        finally:probe.close()


if __name__=="__main__":unittest.main()
