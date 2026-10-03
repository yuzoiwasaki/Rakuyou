#!/usr/bin/env python3
"""Checks for the paired-game audit without engine or local result files."""

import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from paired_selfplay import summarize
from review_black_runs import audit, stats


def fixture():
    games = []
    for number in range(1, 101):
        black = "shin_yonenaga" if number % 2 else "normal"
        white = "normal" if number % 2 else "shin_yonenaga"
        moves = ["5i4h", "3c3d"] if number % 2 else ["7g7f", "5a6b"]
        records = [dict(ply=1, color="black", player=black, move=moves[0],
                        source="fixed_opening" if number % 2 else "book"),
                   dict(ply=2, color="white", player=white, move=moves[1],
                        source="book" if number % 2 else "fixed_opening"),
                   dict(ply=3, color="black", player=black, move="resign", source="search")]
        counts = {p: Counter(r["source"] for r in records if r["player"] == p)
                  for p in ("normal", "shin_yonenaga")}
        games.append(dict(black=black, white=white, moves=moves, records=records,
            pair=(number + 1) // 2, game_in_pair=1 if number % 2 else 2,
            result="white_win", winner=white, reason="resign",
            source_counts_by_player={p: dict(c) for p, c in counts.items()},
            source_counts=dict(counts["normal"] + counts["shin_yonenaga"])))
    summary = summarize(games)
    summary["errors"] = 0
    return dict(games=games, requested_pairs=50, settings={"max_plies": 256},
                errors=[], summary=summary)


class AuditTest(unittest.TestCase):
    def test_valid_fixture(self):
        audit(fixture())

    def test_rejects_wrong_pair(self):
        d = fixture()
        d["games"][0]["pair"] = 2
        with self.assertRaises(AssertionError):
            audit(d)

    def test_rejects_wrong_result(self):
        d = fixture()
        d["games"][0]["result"] = "black_win"
        with self.assertRaises(AssertionError):
            audit(d)

    def test_rejects_incorrect_source_counts(self):
        d = fixture()
        d["games"][0]["records"][0]["source"] = "search"
        with self.assertRaises(AssertionError):
            audit(d)

    def test_stats_include_draw_half_point(self):
        rows = [{"game": {"winner": w}} for w in ("shin_yonenaga", "normal", None)]
        self.assertEqual(stats(rows)["score_rate"], .5)
        self.assertIsNone(stats([])["score_rate"])


if __name__ == "__main__":
    unittest.main()
