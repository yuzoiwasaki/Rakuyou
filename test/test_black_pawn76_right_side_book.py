"""Check the pawn76 pilot's evidence, exact-position use and search exits."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_white_positions import Board
from tools.build_shin_book import compile_book
from tools.paired_selfplay import UsiEngine
import test_black_trial_book as revision_tests

SOURCE = ROOT / "books/shin-yonenaga-black-pawn76-right-side-experiment.json"
BOOK = ROOT / "books/shin-yonenaga-black-book-pawn76-right-side-experiment.txt"
CONTROL = ROOT / "books/shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt"


def entries():
    return json.loads(SOURCE.read_text())["entries"]


def position(moves):
    board = Board()
    for move in moves:
        board.push(move)
    return board.sfen()


class CompilationTest(unittest.TestCase):
    def test_separate_six_position_short_book(self):
        rows = entries()
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["book_move"], "7g7f")
        self.assertEqual(max(len(e["moves"]) + 1 for e in rows), 9)
        self.assertEqual(len({position(e["moves"]) for e in rows}), 6)
        self.assertTrue(all(e["status"] == "experimental" for e in rows))
        self.assertEqual(BOOK.read_text(), compile_book(
            SOURCE, experimental=True, side="black"))
        self.assertNotEqual(BOOK.read_text(), CONTROL.read_text())
        with self.assertRaisesRegex(ValueError, "White candidates"):
            compile_book(SOURCE, experimental=True)

    def test_evidence_matches_saved_search_and_scope(self):
        rows = entries()
        if any(not (ROOT / e["evidence"]["result"]).exists() for e in rows):
            self.skipTest("local ignored search results are unavailable")
        for entry in rows:
            evidence = entry["evidence"]
            data = json.loads((ROOT / evidence["result"]).read_text())
            with self.subTest(entry=entry["id"]):
                self.assertFalse(data["errors"])
                found = next(p for p in data["positions"]
                             if p["id"] == evidence["position_id"])
                self.assertEqual(found["moves"], entry["moves"])
                analysis = found["analysis"]
                self.assertFalse(analysis["stopped_early"])
                candidate = next(c for c in analysis["candidates"]
                                 if c["pv"][0] == entry["book_move"])
                self.assertEqual(candidate["depth"], evidence["depth"])
                self.assertEqual(candidate["multipv"], evidence["rank"])
                self.assertEqual(candidate["score_type"], "cp")
                self.assertEqual(int(candidate["score"]), evidence["score_cp"])
                self.assertEqual(int(analysis["candidates"][0]["score"])
                                 - int(candidate["score"]),
                                 evidence["gap_to_leader_cp"])
                scope = ("restricted: " + " ".join(found["searchmoves"])
                         if found.get("searchmoves") else "unrestricted")
                self.assertEqual(scope, evidence["search_scope"])


class EngineTest(unittest.TestCase):
    def make_engine(self, own_book=True, max_ply=20, shin=True, book=BOOK):
        executable = ROOT / "bin/release"
        if not executable.exists():
            self.skipTest("build bin/release first")
        return UsiEngine(executable, shin, own_book, 1, 64, None, max_ply, book)

    def test_fixed_opening_and_all_entries(self):
        engine = self.make_engine()
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[::2],
                             ("5i4h", "fixed_opening"))
            for row in entries():
                with self.subTest(entry=row["id"]):
                    self.assertEqual(engine.choose_move(row["moves"], 1, 30)[::2],
                                     (row["book_move"], "dedicated_book"))
        finally:
            engine.close()

    def test_transposed_positions(self):
        cases = [
            (["5i4h", "7a6b", "7g7f", "3c3d"], 1),
            (["5i4h", "7a6b", "2g2f", "6c6d", "7g7f", "3c3d"], 2),
            (["5i4h", "7a6b", "2g2f", "6c6d", "7g7f", "3c3d",
              "2f2e", "6b6c"], 3),
            (["5i4h", "8b4b", "7g7f", "3c3d"], 4),
            (["5i4h", "8b4b", "3i3h", "5a6b", "7g7f", "3c3d"], 5),
        ]
        engine = self.make_engine()
        try:
            rows = entries()
            for moves, index in cases:
                with self.subTest(entry=rows[index]["id"]):
                    self.assertEqual(position(moves), position(rows[index]["moves"]))
                    self.assertEqual(engine.choose_move(moves, 1, 30)[::2],
                                     (rows[index]["book_move"], "dedicated_book"))
        finally:
            engine.close()

    def test_uncovered_replies_and_later_moves_search(self):
        rows = entries()
        cases = [
            ["5i4h", "3c3d", "7g7f", "4c4d"],
            ["5i4h", "3c3d", "7g7f", "7a6b", "2g2f", "4a3b"],
            rows[2]["moves"] + ["2f2e", "2b8h+"],
            rows[4]["moves"] + ["3i3h", "4c4d"],
            rows[3]["moves"] + ["3i3h", "2b8h+"],
            rows[5]["moves"] + ["2g2f", "4c4d"],
            ["5i4h", "3c3d", "7g7f"],
        ]
        engine = self.make_engine()
        try:
            for moves in cases:
                with self.subTest(moves=moves):
                    self.assertEqual(engine.choose_move(moves, 1, 30)[2], "search")
        finally:
            engine.close()

    def test_ownbook_off_and_ply_boundaries(self):
        for own_book, max_ply, index, expected in [
                (False, 20, 0, "search"), (True, 2, 0, "search"),
                (True, 3, 0, "dedicated_book"), (True, 8, 3, "search"),
                (True, 9, 3, "dedicated_book")]:
            engine = self.make_engine(own_book=own_book, max_ply=max_ply)
            try:
                self.assertEqual(engine.choose_move(entries()[index]["moves"], 1, 30)[2],
                                 expected)
            finally:
                engine.close()

    def test_normal_ignores_trial_and_control_keeps_silver_entry(self):
        normal = self.make_engine(shin=False)
        try:
            self.assertEqual(normal.choose_move([], 1, 30)[2], "book")
        finally:
            normal.close()
        control = self.make_engine(book=CONTROL)
        try:
            self.assertEqual(control.choose_move(["5i4h", "3c3d"], 1, 30)[::2],
                             ("3i3h", "dedicated_book"))
        finally:
            control.close()


class ConditionalPawn36RevisionTest(revision_tests.Common17Pawn76RevisionTest):
    base_source = SOURCE
    base_book = BOOK
    source = ROOT / "books/shin-yonenaga-black-pawn76-right-side-pawn36-experiment.json"
    book = ROOT / "books/shin-yonenaga-black-book-pawn76-right-side-pawn36-experiment.txt"
    parent = ["5i4h", "3c3d", "7g7f", "7a6b", "2g2f", "4a3b", "6i7h", "4c4d"]
    book_move = "3g3f"
    followup_reply = "6c6d"
    transposed = ["5i4h", "3c3d", "7g7f", "7a6b", "6i7h", "4c4d", "2g2f", "4a3b"]

    def test_added_evidence_and_unique_positions(self):
        rows = json.loads(self.source.read_text())["entries"]
        self.assertEqual(len({position(e["moves"]) for e in rows}), 7)
        evidence = rows[-1]["evidence"]
        path = ROOT / evidence["result"]
        if not path.exists():
            self.skipTest("local ignored search result is unavailable")
        result = json.loads(path.read_text())
        self.assertFalse(result["errors"])
        parent = next(p for p in result["positions"]
                      if p["id"] == evidence["position_id"])
        self.assertEqual(parent["moves"], self.parent)
        self.assertFalse(parent.get("searchmoves"))
        analysis = parent["analysis"]
        self.assertFalse(analysis["stopped_early"])
        candidate = next(c for c in analysis["candidates"]
                         if c["pv"][0] == self.book_move)
        self.assertEqual((candidate["depth"], candidate["multipv"],
                          candidate["score_type"], int(candidate["score"])),
                         (24, 2, "cp", -44))
        self.assertEqual(evidence["gap_to_leader_cp"], 4)
        self.assertEqual(int(analysis["candidates"][0]["score"])
                         - int(candidate["score"]), 4)

    def test_other_reply_and_planned_move11_remain_search(self):
        cases = [self.parent[:-1] + ["6c6d"],
                 ["5i4h", "3c3d", "7g7f", "7a6b", "2g2f", "6c6d",
                  "2f2e", "6b6c", "3i3h", "4a3b"]]
        engine = self.make_engine()
        try:
            for moves in cases:
                with self.subTest(moves=moves):
                    self.assertEqual(engine.choose_move(moves, 1, 30)[2], "search")
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
