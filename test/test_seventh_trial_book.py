#!/usr/bin/env python3
"""Checks for the standalone, non-official seventh-file concept book."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_shin_book import compile_book  # noqa: E402
from tools.paired_selfplay import UsiEngine  # noqa: E402

SOURCE = ROOT / "books/shin-yonenaga-white-seventh-edge-experiment.json"
BOOK = ROOT / "books/shin-yonenaga-white-book-seventh-edge-experiment.txt"


class CompilationTest(unittest.TestCase):
    def test_generated_experimental_book(self):
        self.assertEqual(BOOK.read_text(), compile_book(SOURCE, experimental=True))
        entries = json.loads(SOURCE.read_text())["entries"]
        self.assertEqual(len(entries), 13)
        self.assertTrue(all(e["status"] == "experimental" for e in entries))

    def test_default_mode_does_not_adopt_experimental_entries(self):
        with self.assertRaisesRegex(ValueError, "no adopted book moves"):
            compile_book(SOURCE)

    def test_explicit_output_required_and_v1_v2_protected(self):
        protected = [ROOT / "books/shin-yonenaga-white-book.txt",
                     ROOT / "books/shin-yonenaga-white-book-v2-experiment.txt"]
        before = [p.read_bytes() for p in protected]
        for output in [None] + protected:
            with self.subTest(output=output):
                cmd = [sys.executable, str(ROOT / "tools/build_shin_book.py"),
                       "--source", str(SOURCE), "--experimental"]
                if output is not None:
                    cmd += ["--output", str(output)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual([p.read_bytes() for p in protected], before)


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = ROOT / "bin/release"
        if not cls.executable.is_file():
            raise unittest.SkipTest("build bin/release first")

    def test_all_entries_return_dedicated_book_moves(self):
        engine = UsiEngine(self.executable, True, True, 1, 64, None, 20, BOOK)
        try:
            for entry in json.loads(SOURCE.read_text())["entries"]:
                with self.subTest(entry=entry["id"]):
                    move, _, source = engine.choose_move(entry["moves"], 1, 30)
                    self.assertEqual((move, source),
                                     (entry["book_move"], "dedicated_book"))
        finally:
            engine.close()

    def test_king48_first_transposition(self):
        moves = ["7g7f", "5a6b", "2h6h", "1c1d", "5i4h", "1d1e",
                 "6g6f", "7a7b", "7i7h"]
        engine = UsiEngine(self.executable, True, True, 1, 64, None, 20, BOOK)
        try:
            move, _, source = engine.choose_move(moves, 1, 30)
            self.assertEqual((move, source), ("6b7a", "dedicated_book"))
        finally:
            engine.close()

    def test_uncovered_edge_reply_falls_back_to_search(self):
        engine = UsiEngine(self.executable, True, True, 1, 64, None, 20, BOOK)
        try:
            moves = ["7g7f", "5a6b", "2h6h", "1c1d", "1g1f"]
            self.assertEqual(engine.choose_move(moves, 1, 30)[2], "search")
        finally:
            engine.close()

    def test_own_book_off_disables_trial(self):
        engine = UsiEngine(self.executable, True, False, 1, 64, None, 20, BOOK)
        try:
            self.assertEqual(engine.choose_move(["7g7f", "5a6b", "2h6h"], 1, 30)[2],
                             "search")
        finally:
            engine.close()

    def test_normal_side_keeps_standard_book(self):
        engine = UsiEngine(self.executable, False, True, 1, 64, None, 20, BOOK)
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[2], "book")
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
