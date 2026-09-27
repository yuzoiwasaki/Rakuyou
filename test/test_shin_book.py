#!/usr/bin/env python3
"""Integration checks for the first dedicated White book."""

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.build_shin_book import compile_book  # noqa: E402
from tools.paired_selfplay import UsiEngine  # noqa: E402


class ShinBookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine_path = ROOT / "bin/release"
        cls.book_path = ROOT / "books/shin-yonenaga-white-book.txt"
        cls.candidates_path = ROOT / "books/shin-yonenaga-white-candidates.json"
        if not cls.engine_path.is_file():
            raise unittest.SkipTest("build bin/release first")

    def test_book_matches_reviewed_candidates(self):
        self.assertEqual(self.book_path.read_text(encoding="utf-8"),
                         compile_book(self.candidates_path))
        entries = json.loads(self.candidates_path.read_text(encoding="utf-8"))["entries"]
        engine = UsiEngine(self.engine_path, True, True, 1, 64, None, 20,
                           self.book_path)
        try:
            for entry in entries:
                with self.subTest(entry=entry["id"]):
                    move, _, source = engine.choose_move(entry["moves"], 1, 30)
                    if entry["status"] == "unstable":
                        self.assertEqual(source, "search")
                    else:
                        self.assertEqual((move, source),
                                         (entry["book_move"], "dedicated_book"))
        finally:
            engine.close()

    def test_normal_side_keeps_standard_book(self):
        engine = UsiEngine(self.engine_path, False, True, 1, 64, None, 20)
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[2], "book")
        finally:
            engine.close()

    def test_transposed_position_uses_same_move(self):
        engine = UsiEngine(self.engine_path, True, True, 1, 64, None, 20,
                           self.book_path)
        try:
            moves = ["7g7f", "5a6b", "2h6h", "5c5d", "5i4h", "3a4b", "3i3h"]
            move, _, source = engine.choose_move(moves, 1, 30)
            self.assertEqual((move, source), ("4b5c", "dedicated_book"))
        finally:
            engine.close()

    def test_own_book_off_disables_dedicated_book(self):
        engine = UsiEngine(self.engine_path, True, False, 1, 64, None, 20,
                           self.book_path)
        try:
            move, _, source = engine.choose_move(["7g7f", "5a6b", "2h6h"], 1, 30)
            self.assertEqual(source, "search")
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
