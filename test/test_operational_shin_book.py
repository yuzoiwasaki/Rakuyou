"""Check the provisional combined book without playing additional games."""

import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_operational_shin_book as builder
from tools.paired_selfplay import UsiEngine


def rows(path):
    return [line for line in path.read_text().splitlines()
            if line and not line.startswith("#")]


class CompilationTest(unittest.TestCase):
    def test_reproducible_exact_union_and_unchanged_inputs(self):
        self.assertEqual(builder.OUTPUT.read_text(), builder.compile_operational_book())
        black = rows(ROOT / builder.BLACK_BOOK)
        white = rows(ROOT / builder.WHITE_BOOK)
        self.assertEqual((len(black), len(white)), (6, 11))
        self.assertEqual(rows(builder.OUTPUT), black + white)
        for name, sha in [
                (builder.BLACK_BOOK, "cb8d7e3e3a4ed2817752ea93d4890837fa43c91db752b5ce3a1dc534f38bb7eb"),
                (builder.WHITE_BOOK, "28e59ec12cb86ada7280687d130e29bdb28eb0d550840d634c73e003aa2ffc62")]:
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), sha)

    def test_stale_selected_book_is_rejected(self):
        with patch.object(builder, "compile_book", return_value="# stale\n"):
            with self.assertRaisesRegex(ValueError, "differs from its source"):
                builder.compile_operational_book()


class EngineTest(unittest.TestCase):
    def make_engine(self, own=True, shin=True, max_ply=20):
        if not (ROOT / "bin/release").is_file():
            self.skipTest("build bin/release first")
        return UsiEngine(ROOT / "bin/release", shin, own, 1, 64,
                         None, max_ply, builder.OUTPUT)

    def test_all_seventeen_entries_in_one_engine(self):
        engine = self.make_engine()
        try:
            # Ask for another ready cycle so the loader's full diagnostics
            # can be inspected rather than silently accepting rejected rows.
            engine.send("isready")
            diagnostics = []
            while True:
                line = engine.lines.get(timeout=30)
                diagnostics.append(line)
                if line.startswith("readyok"):
                    break
            self.assertIn("info string ShinBookFile loaded 17 positions", diagnostics)
            self.assertFalse(any("ShinBookFile line" in line or
                                 "Failed to open ShinBookFile" in line
                                 for line in diagnostics))
            for row in rows(builder.OUTPUT):
                moves, book_move = row.split(" | ")
                with self.subTest(moves=moves):
                    self.assertEqual(engine.choose_move(moves.split(), 1, 30)[::2],
                                     (book_move, "dedicated_book"))
            self.assertEqual(engine.choose_move([], 1, 30)[::2],
                             ("5i4h", "fixed_opening"))
            self.assertEqual(engine.choose_move(["7g7f"], 1, 30)[::2],
                             ("5a6b", "fixed_opening"))
        finally:
            engine.close()

    def test_transpositions_on_both_sides(self):
        engine = self.make_engine()
        try:
            for moves, expected in [
                    (["5i4h", "7a6b", "7g7f", "3c3d"], "2g2f"),
                    (["7g7f", "5a6b", "2h6h", "5c5d", "5i4h", "3a4b", "3i3h"], "4b5c")]:
                self.assertEqual(engine.choose_move(moves, 1, 30)[::2],
                                 (expected, "dedicated_book"))
        finally:
            engine.close()

    def test_unknown_and_held_additions_remain_search(self):
        engine = self.make_engine()
        try:
            for moves in [
                    ["5i4h", "3c3d", "7g7f", "4c4d"],
                    ["7g7f", "5a6b", "2g2f"],
                    "5i4h 3c3d 7g7f 7a6b 2g2f 4a3b 6i7h 4c4d".split(),
                    "7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 7a7b 6g6f 6b7a 7i7h 8c8d 7h6g 2c2d 6f6e".split()]:
                with self.subTest(moves=moves):
                    self.assertEqual(engine.choose_move(moves, 1, 30)[2], "search")
        finally:
            engine.close()

    def test_ownbook_off_and_ply_boundaries(self):
        for own, max_ply, expected in [(False, 20, "search"),
                                       (True, 2, "search"),
                                       (True, 3, "dedicated_book")]:
            engine = self.make_engine(own=own, max_ply=max_ply)
            try:
                for moves in [["5i4h", "3c3d"], ["7g7f", "5a6b", "2h6h"]]:
                    # Black entry is move3; White entry is move4.
                    source = expected if len(moves) == 2 else "search"
                    self.assertEqual(engine.choose_move(moves, 1, 30)[2], source)
            finally:
                engine.close()
        engine = self.make_engine(max_ply=4)
        try:
            self.assertEqual(engine.choose_move(["7g7f", "5a6b", "2h6h"], 1, 30)[2],
                             "dedicated_book")
        finally:
            engine.close()

    def test_normal_side_still_uses_standard_book(self):
        engine = self.make_engine(shin=False)
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[2], "book")
        finally:
            engine.close()


if __name__ == "__main__":
    unittest.main()
