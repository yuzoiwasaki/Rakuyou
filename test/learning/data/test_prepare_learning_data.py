#!/usr/bin/env python3
"""Checks for draw handling, leakage exclusion, native validation and safe output."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.learning.data.prepare_learning_data import ROOT, Probe, outcome, split_rows, teacher_rejection, validate_game, zero_copy


def record():
    return dict(ply=25, color="black", player="shin_yonenaga", move="7g7f",
                source="search", analysis=dict(depth=15, score_type="cp", score="12",
                    pv=["7g7f"], raw="info depth 15 score cp 12 pv 7g7f"))


def rows():
    return [dict(id=f"{run}:{game}:{ply}", run=str(run), game=game, ply=ply,
                 sfen=f"position-{run}-{game}-{ply}", prefix24=f"prefix-{run}-{game}",
                 side_to_move="black" if ply % 2 else "white", stratum="draw")
            for run in range(10) for game in range(1, 4) for ply in range(24, 40)]


class PreparationTest(unittest.TestCase):
    def test_truncated_draw_has_no_outcome_but_keeps_cp_candidate(self):
        target = outcome(dict(result="draw", reason="max_plies"), "white")
        self.assertIsNone(target["target"])
        self.assertFalse(target["use_outcome_loss"])
        self.assertIsNone(teacher_rejection(record()))

    def test_decisive_targets_follow_color(self):
        game = dict(result="white_win", reason="resign")
        self.assertEqual(outcome(game, "white")["target"], 1)
        self.assertEqual(outcome(game, "black")["target"], 0)
        self.assertFalse(outcome(dict(result="draw", reason="repetition"), "white")["use_outcome_loss"])

    def test_bounds_book_off_and_raw_mismatch_rejected(self):
        r = record()
        r["analysis"]["raw"] = "info depth 15 score cp 12 lowerbound pv 7g7f"
        self.assertEqual(teacher_rejection(r), "missing_raw_or_bound")
        r = record(); r["source"] = "dedicated_book"
        self.assertEqual(teacher_rejection(r), "non_search")
        r = record(); r["player"] = "normal"
        self.assertEqual(teacher_rejection(r), "off_player")
        r = record(); r["analysis"]["raw"] = "info depth 15 score cp -12 pv 7g7f"
        self.assertEqual(teacher_rejection(r), "raw_mismatch")

    def test_split_is_deterministic_run_held_out_and_capped(self):
        data = rows()
        a, assignments, _ = split_rows(data)
        self.assertEqual(a, split_rows(list(reversed(data)))[0])
        self.assertEqual(set(assignments.values()), {"train", "validation", "test"})
        from collections import Counter
        for name, selected in a.items():
            counts = Counter((r["run"], r["game"]) for r in selected)
            self.assertTrue(all(v <= 8 for v in counts.values()))
            self.assertTrue(all(assignments[r["run"]] == name for r in selected))

    def test_cross_split_sfen_and_prefix_removed_before_caps(self):
        data = rows()
        _, assignments, _ = split_rows(data)
        train = next(r for r in data if assignments[r["run"]] == "train")
        test = next(r for r in data if assignments[r["run"]] == "test")
        train["sfen"] = test["sfen"] = "shared-root"
        train["prefix24"] = test["prefix24"] = "shared-long-prefix"
        next(r for r in data if assignments[r["run"]] == "train" and r is not train)["prefix24"] = "shared-long-prefix"
        next(r for r in data if assignments[r["run"]] == "test" and r is not test)["prefix24"] = "shared-long-prefix"
        a, _, excluded = split_rows(data, caps=(1, 1, 1))
        self.assertEqual(excluded["shared_sfen"], 2)
        self.assertGreater(excluded["shared_prefix24"], 0)
        for selected in a.values():
            self.assertTrue(all(r["sfen"] != "shared-root" and
                                r["prefix24"] != "shared-long-prefix" for r in selected))

    def test_zero_copy_rejects_overwrite_and_wrong_size(self):
        with tempfile.TemporaryDirectory() as directory:
            base, output = Path(directory)/"base", Path(directory)/"copy"
            base.write_bytes(b"test")
            with patch("tools.learning.data.prepare_learning_data.subprocess.check_output", return_value=json.dumps({"eval_parameters_bytes": 4})):
                zero_copy(base, output, "probe")
                self.assertEqual(output.read_bytes(), b"test")
                with self.assertRaises(FileExistsError):
                    zero_copy(base, output, "probe")
                with self.assertRaises(ValueError):
                    zero_copy(base, base, "probe")
                base.write_bytes(b"x")
                with self.assertRaises(ValueError):
                    zero_copy(base, Path(directory)/"new", "probe")

    def test_terminal_result_mismatch_is_rejected(self):
        game = dict(black="shin_yonenaga", white="normal", moves=["7g7f"],
            records=[dict(ply=1,color="black",player="shin_yonenaga",move="7g7f"),
                     dict(ply=2,color="white",player="normal",move="resign")],
            result="white_win", winner="normal", reason="resign")
        with self.assertRaises(ValueError):
            validate_game(game, {})


class NativeProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = ROOT / "results/learning-tools/learning-data-probe"
        if not cls.binary.exists():
            raise unittest.SkipTest("Build with make learning-probe first")

    def setUp(self):
        self.probe = Probe(self.binary)

    def tearDown(self):
        self.probe.close()

    def test_capture_promotion_drop_and_huffman_roundtrip(self):
        moves = ["7g7f", "3c3d", "8h2b+", "3a2b", "B*4e"]
        r = self.probe.replay(moves)
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["positions"]), 6)
        self.assertEqual(r["positions"][0]["sfen"],
                         "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1")
        self.assertTrue(all(len(p["huffman_hex"]) == 64 for p in r["positions"]))

    def test_bad_move_rejected_and_process_recovers(self):
        self.assertFalse(self.probe.replay(["7g7e"])["ok"])
        self.assertFalse(self.probe.replay(["3c3d"])["ok"])
        self.assertTrue(self.probe.replay(["7g7f"])["ok"])

    def test_repeated_history_detected_without_draw_adjudication(self):
        cycle = ["5i4h", "5a4b", "4h5i", "4b5a"]
        r = self.probe.replay(cycle)
        self.assertTrue(r["ok"])
        self.assertEqual(r["positions"][-1]["occurrences"], 2)


if __name__ == "__main__":
    unittest.main()
