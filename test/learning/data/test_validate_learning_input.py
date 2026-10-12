#!/usr/bin/env python3
"""Semantic teacher checks and zero-update-only entry guards."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools.learning.data.validate_learning_input import CHECKPOINT_SCHEMA, VERSION, check_zero_delta, read_rows, verify_row


def fixture(draw=False):
    moves = ["7g7f" if i % 2 == 0 else "3c3d" for i in range(25)]
    records = [dict(ply=i+1, color="black" if i % 2 == 0 else "white",
                    player="shin_yonenaga" if i % 2 == 0 else "normal",
                    move=m, source="search") for i, m in enumerate(moves)]
    records[-1]["analysis"] = dict(depth=15, score_type="cp", score="12",
        pv=[moves[-1]], raw="info depth 15 score cp 12 pv " + moves[-1])
    if not draw:
        records.append(dict(ply=26, color="white", player="normal", move="resign"))
    game = dict(moves=moves, records=records, black="shin_yonenaga", white="normal",
                result="draw" if draw else "black_win", winner=None if draw else "shin_yonenaga",
                reason="max_plies" if draw else "resign")
    source = dict(games=[game], settings={"max_plies": 25})
    row = dict(schema=VERSION, split="train", depth=15, teacher_cp=12,
        ShinYonenagaGyoku=True, game=1, ply=25, run="run", id="run:1:25",
        moves_before=moves[:-1], move=moves[-1], pv=[moves[-1]], side_to_move="black",
        result=game["result"], termination=game["reason"], prefix24=" ".join(moves[:24]),
        stratum="black:" + game["result"], provenance_status="historical_runtime_not_verified",
        outcome=dict(kind="truncated" if draw else "decisive", target=None if draw else 1.0,
                     use_outcome_loss=not draw))
    # This fixture tests source semantics only; native legality is checked separately.
    return row, source


class InputTest(unittest.TestCase):
    def test_only_zero_checkpoint_accepted(self):
        state = dict(schema=CHECKPOINT_SCHEMA, base_sha256="base", updates=0,
                     tempo_delta_cp=[0, 0.0, -0.0])
        check_zero_delta(state, "base")
        variants = [dict(updates=1), dict(updates=True), dict(base_sha256="other"),
                    dict(tempo_delta_cp=[0, 0, 0.1]), dict(tempo_delta_cp=[0, 0, float("nan")]),
                    dict(tempo_delta_cp=[False, 0, 0]), dict(tempo_delta_cp=[0, 0])]
        for changed in variants:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                check_zero_delta({**state, **changed}, "base")

    def test_source_semantics_and_draw_masks(self):
        for draw in (False, True):
            row, source = fixture(draw)
            verify_row(row, source)
        row["outcome"] = dict(kind="decisive", target=1.0, use_outcome_loss=True)
        with self.assertRaises(ValueError):
            verify_row(row, source)

    def test_changed_root_turn_pv_or_cp_rejected(self):
        row, source = fixture()
        for changed in (dict(side_to_move="white"), dict(pv=["2g2f"]),
                        dict(teacher_cp=-12), dict(moves_before=[]),
                        dict(provenance_status="verified")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                verify_row({**row, **changed}, source)

    def test_changed_source_bound_rejected(self):
        row, source = fixture()
        source["games"][0]["records"][24]["analysis"]["raw"] = "info depth 15 score cp 12 lowerbound pv 7g7f"
        with self.assertRaises(ValueError):
            verify_row(row, source)

    def test_jsonl_hash_schema_count_and_on_flag(self):
        row, _ = fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"train.jsonl"
            def write(value):
                path.write_text(json.dumps(value) + "\n")
                return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), positions=1)
            expected = write(row)
            self.assertEqual(read_rows(path, expected, "train"), [row])
            with self.assertRaises(ValueError):
                read_rows(path, {**expected, "positions": 2}, "train")
            for changed in (dict(schema="bad"), dict(split="test"),
                            dict(ShinYonenagaGyoku=False), dict(teacher_cp=True)):
                value = {**row, **changed}
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    read_rows(path, write(value), "train")
            path.write_text("changed")
            with self.assertRaises(ValueError):
                read_rows(path, expected, "train")


if __name__ == "__main__":
    unittest.main()
