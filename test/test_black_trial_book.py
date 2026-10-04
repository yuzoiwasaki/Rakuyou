"""Compilation and integration checks for the short Black pawn26 trial."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_shin_book import compile_book
from tools.paired_selfplay import UsiEngine

SOURCE = ROOT / "books/shin-yonenaga-black-pawn26-experiment.json"
BOOK = ROOT / "books/shin-yonenaga-black-book-pawn26-experiment.txt"
CONDITIONAL_SOURCE = ROOT / "books/shin-yonenaga-black-conditional-experiment.json"
CONDITIONAL_BOOK = ROOT / "books/shin-yonenaga-black-book-conditional-experiment.txt"
SILVER_SOURCE = ROOT / "books/shin-yonenaga-black-silver38-experiment.json"
SILVER_BOOK = ROOT / "books/shin-yonenaga-black-book-silver38-experiment.txt"


class CompilationTest(unittest.TestCase):
    def test_generated_book_and_explicit_side(self):
        self.assertEqual(BOOK.read_text(),
                         compile_book(SOURCE, experimental=True, side="black"))
        with self.assertRaisesRegex(ValueError, "White candidates"):
            compile_book(SOURCE, experimental=True)
        with self.assertRaisesRegex(ValueError, "no adopted"):
            compile_book(SOURCE, side="black")

    def test_wrong_turn_invalid_move_and_duplicate_rejected(self):
        original = json.loads(SOURCE.read_text())
        for kind in ("turn", "move", "duplicate"):
            data = json.loads(json.dumps(original))
            if kind == "turn":
                data["entries"][0]["moves"].append("2g2f")
            elif kind == "move":
                data["entries"][0]["book_move"] = "bad"
            else:
                data["entries"].append(data["entries"][0].copy())
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "source.json"
                source.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    compile_book(source, experimental=True, side="black")

    def test_cli_requires_explicit_trial_and_protects_white_books(self):
        protected = list((ROOT / "books").glob("shin-yonenaga-white-*.txt"))
        before = {p: p.read_bytes() for p in protected}
        base = [sys.executable, str(ROOT / "tools/build_shin_book.py"),
                "--side", "black", "--source", str(SOURCE)]
        variants = [[], ["--experimental"]]
        variants += [["--experimental", "--output", str(p)] for p in protected]
        for extra in variants:
            result = subprocess.run(base + extra, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual({p: p.read_bytes() for p in protected}, before)


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = ROOT / "bin/release"
        if not cls.executable.is_file():
            raise unittest.SkipTest("build bin/release first")

    def make_engine(self, own_book=True, max_ply=20, shin=True):
        return UsiEngine(self.executable, shin, own_book, 1, 64, None,
                         max_ply, BOOK)

    def test_all_entries_and_fixed_opening(self):
        engine = self.make_engine()
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[::2],
                             ("5i4h", "fixed_opening"))
            for entry in json.loads(SOURCE.read_text())["entries"]:
                with self.subTest(entry=entry["id"]):
                    self.assertEqual(engine.choose_move(entry["moves"], 1, 30)[::2],
                                     (entry["book_move"], "dedicated_book"))
        finally:
            engine.close()

    def test_transposition(self):
        engine = self.make_engine()
        try:
            moves = ["5i4h", "3c3d", "7g7f", "4a3b", "2g2f", "8c8d"]
            self.assertEqual(engine.choose_move(moves, 1, 30)[::2],
                             ("2f2e", "dedicated_book"))
        finally:
            engine.close()

    def test_uncovered_and_other_side_search_without_standard_fallback(self):
        engine = self.make_engine()
        try:
            for moves in (["5i4h", "3c3d", "2g2f", "4c4d"],
                          ["5i4h", "3c3d", "2g2f"]):
                self.assertEqual(engine.choose_move(moves, 1, 30)[2], "search")
        finally:
            engine.close()

    def test_own_book_off_and_max_ply(self):
        for own_book, max_ply in ((False, 20), (True, 2)):
            engine = self.make_engine(own_book=own_book, max_ply=max_ply)
            try:
                self.assertEqual(engine.choose_move(["5i4h", "3c3d"], 1, 30)[2],
                                 "search")
            finally:
                engine.close()

    def test_normal_side_ignores_shin_book(self):
        engine = self.make_engine(shin=False)
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[2], "book")
        finally:
            engine.close()


class ConditionalBookTest(unittest.TestCase):
    def test_only_root_entry_removed(self):
        original = json.loads(SOURCE.read_text())
        revised = json.loads(CONDITIONAL_SOURCE.read_text())
        self.assertEqual(original["entries"][0]["id"], revised["removed_entry"])
        self.assertEqual(revised["entries"], original["entries"][1:])
        self.assertEqual(len(revised["entries"]), 6)
        self.assertTrue(all(len(e["moves"]) >= 4 for e in revised["entries"]))
        self.assertEqual(CONDITIONAL_BOOK.read_text(),
                         compile_book(CONDITIONAL_SOURCE, experimental=True, side="black"))
        self.assertEqual(CONDITIONAL_BOOK.read_text().splitlines(),
                         BOOK.read_text().splitlines()[:2] + BOOK.read_text().splitlines()[4:])

    def make_engine(self, own_book=True, max_ply=20):
        executable = ROOT / "bin/release"
        if not executable.is_file():
            self.skipTest("build bin/release first")
        return UsiEngine(executable, True, own_book, 1, 64, None,
                         max_ply, CONDITIONAL_BOOK)

    def test_root_search_and_first_move_preserved(self):
        engine = self.make_engine()
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[::2],
                             ("5i4h", "fixed_opening"))
            self.assertEqual(engine.choose_move(["5i4h", "3c3d"], 1, 30)[2], "search")
        finally:
            engine.close()

    def test_all_remaining_entries_and_transposition(self):
        engine = self.make_engine()
        try:
            for entry in json.loads(CONDITIONAL_SOURCE.read_text())["entries"]:
                with self.subTest(entry=entry["id"]):
                    self.assertEqual(engine.choose_move(entry["moves"], 1, 30)[::2],
                                     (entry["book_move"], "dedicated_book"))
            moves = ["5i4h", "3c3d", "7g7f", "7a6b", "2g2f", "4a3b"]
            self.assertEqual(engine.choose_move(moves, 1, 30)[::2],
                             ("2f2e", "dedicated_book"))
        finally:
            engine.close()

    def test_uncovered_own_book_off_and_max_ply(self):
        engine = self.make_engine()
        try:
            self.assertEqual(engine.choose_move(
                ["5i4h", "3c3d", "2g2f", "4c4d"], 1, 30)[2], "search")
        finally:
            engine.close()
        for own_book, max_ply in ((False, 20), (True, 4)):
            engine = self.make_engine(own_book=own_book, max_ply=max_ply)
            try:
                self.assertEqual(engine.choose_move(
                    ["5i4h", "3c3d", "2g2f", "4a3b"], 1, 30)[2], "search")
            finally:
                engine.close()


class Silver38BookTest(unittest.TestCase):
    def make_engine(self, own_book=True, max_ply=20):
        executable = ROOT / "bin/release"
        if not executable.is_file():
            self.skipTest("build bin/release first")
        return UsiEngine(executable, True, own_book, 1, 64,
                         ROOT / "bin/book.bin", max_ply, SILVER_BOOK)

    def test_generated_four_short_entries(self):
        entries = json.loads(SILVER_SOURCE.read_text())["entries"]
        self.assertEqual([(len(e["moves"]), e["book_move"]) for e in entries],
                         [(2, "3i3h"), (4, "7g7f"), (6, "2g2f"), (4, "2g2f")])
        self.assertTrue(all(e["status"] == "experimental" for e in entries))
        self.assertEqual(SILVER_BOOK.read_text(),
                         compile_book(SILVER_SOURCE, experimental=True, side="black"))

    def test_all_entries_fixed_opening_and_transposition(self):
        engine = self.make_engine()
        try:
            self.assertEqual(engine.choose_move([], 1, 30)[::2],
                             ("5i4h", "fixed_opening"))
            for entry in json.loads(SILVER_SOURCE.read_text())["entries"]:
                with self.subTest(entry=entry["id"]):
                    self.assertEqual(engine.choose_move(entry["moves"], 1, 30)[::2],
                                     (entry["book_move"], "dedicated_book"))
            self.assertEqual(engine.choose_move(
                ["5i4h", "3c3d", "7g7f", "8c8d", "3i3h", "8d8e"],
                1, 30)[::2], ("2g2f", "dedicated_book"))
        finally:
            engine.close()

    def test_unknown_replies_and_after_book_search_without_fallback(self):
        engine = self.make_engine()
        try:
            positions = [["5i4h", "8c8d"]]
            positions += [["5i4h", "3c3d", "3i3h", reply]
                          for reply in ("3a3b", "7a6b", "8b3b", "5c5d")]
            positions += [["5i4h", "3c3d", "3i3h", "8c8d", "2g2f", "8d8e"],
                          ["5i4h", "3c3d", "3i3h", "8c8d", "7g7f", "8d8e",
                           "2g2f", "4a3b"]]
            for moves in positions:
                with self.subTest(moves=moves):
                    self.assertEqual(engine.choose_move(moves, 1, 30)[2], "search")
        finally:
            engine.close()

    def test_own_book_off_and_each_ply_cutoff(self):
        entries = json.loads(SILVER_SOURCE.read_text())["entries"]
        for own_book, max_ply, entry in [(False, 20, entries[0])] + [
                (True, len(e["moves"]), e) for e in entries]:
            engine = self.make_engine(own_book=own_book, max_ply=max_ply)
            try:
                self.assertEqual(engine.choose_move(entry["moves"], 1, 30)[2], "search")
            finally:
                engine.close()


if __name__ == "__main__":
    unittest.main()
