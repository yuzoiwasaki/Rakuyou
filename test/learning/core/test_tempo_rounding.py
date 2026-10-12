#!/usr/bin/env python3
"""Signed rounding, tempo-only memory changes and native perturbation bounds."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import sys
import unittest
from pathlib import Path

from tools.learning.checks.check_tempo_rounding import SCALE, trunc_div, score_from_parts, compare
from tools.learning.data.prepare_learning_data import ROOT, Probe, digest


class IntegerRoundingTest(unittest.TestCase):
    def test_signed_division_truncates_towards_zero(self):
        self.assertEqual(trunc_div(-19,10),-1)
        self.assertEqual(trunc_div(19,10),1)
        self.assertEqual(trunc_div(-1,2),0)

    def test_tempo_is_positive_for_each_own_turn(self):
        parts=dict(kp=[0,0,0,0],others=[0,0,0,0],tempo=[2*SCALE,0,0,123])
        for side in ("black","white"):
            self.assertEqual(score_from_parts(parts,side,0),1)

    def test_non_tempo_turn_component_and_negative_rounding(self):
        parts=dict(kp=[-SCALE,0,0,0],others=[0,-19*SCALE,0,0],tempo=[0,0,0,0])
        self.assertEqual(score_from_parts(parts,"black",0),-2)
        self.assertEqual(score_from_parts(parts,"white",0),0)

    def test_probe_input_guard(self):
        for values in ((True,0,0),(6*SCALE,0,0),(0,0)):
            with self.assertRaises(ValueError):
                Probe("unused","unused",tempo_raw=values)

    def test_crossing_zero_can_exceed_one_cp_delta_error(self):
        parts=dict(kp=[-3*SCALE//4,0,0,0],others=[0,0,0,0],tempo=[0,0,0,0])
        before=score_from_parts(parts,"black",0)
        parts["tempo"][0]=5*SCALE
        after=score_from_parts(parts,"black",0)
        self.assertEqual((before,after),(0,1))
        self.assertEqual(abs((after-before)-2.5),1.5)


class NativeTempoTest(unittest.TestCase):
    def test_small_memory_delta_preserves_file_and_other_components(self):
        binary=ROOT/"results/learning-tools/learning-data-probe"
        params=ROOT/"bin/params.bin"
        if not binary.exists() or not params.exists():
            self.skipTest("Build learning-probe and provide runtime data first")
        before=digest(params)
        base=Probe(binary,params,details=True)
        changed=Probe(binary,params,tempo_raw=(SCALE,0,0))
        try:
            for moves in ([],["5i4h"],["7g7f","5a6b"]):
                a,b=base.replay(moves),changed.replay(moves)
                self.assertTrue(a["ok"] and b["ok"])
                side="black" if len(moves)%2==0 else "white"
                compare(a["positions"][-1],b["positions"][-1],side,(SCALE,0,0))
        finally:
            base.close();changed.close()
        self.assertEqual(before,digest(params))


if __name__ == "__main__":
    unittest.main()
