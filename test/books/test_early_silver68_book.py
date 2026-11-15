"""Checks for the branch-only early-silver book; never changes release defaults."""
import hashlib
import json
from pathlib import Path
import unittest
from tools.experiments.build_early_silver68_book import BASE, OUTPUT, SOURCE, build, rows
from tools.experiments.early_silver68 import position
from tools.analysis.paired_selfplay import UsiEngine

ROOT = Path(__file__).resolve().parents[2]


class RecordingEngine(UsiEngine):
    def __init__(self, *args, **kwargs):
        self.diagnostics = []
        super().__init__(*args, **kwargs)

    def _read_output(self):
        for line in self.process.stdout:
            self.diagnostics.append(line.rstrip())
            self.lines.put(line.rstrip())


class EarlySilverBookTest(unittest.TestCase):
    def engine(self, book=OUTPUT, own_book=True):
        if not (ROOT / 'bin/match').is_file():
            self.skipTest('make match first')
        return RecordingEngine(ROOT / 'bin/match', True, own_book, 1, 64, None, 32, book)

    def test_reproduction_and_only_expected_changes(self):
        self.assertEqual(OUTPUT.read_text(), build())
        self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(),
                         'd080bc78583695da22641509ca93682653baa4761cb633f4f144ec1aef7c7e07')
        original, trial = set(rows(BASE.read_text())), set(rows(OUTPUT.read_text()))
        self.assertEqual(original - trial, {'5i4h 3c3d | 7g7f'})
        self.assertEqual(len(trial - original), 10)
        self.assertEqual(len(trial), 26)

    def test_entries_are_legal_and_returned_by_engine(self):
        e = self.engine()
        try:
            self.assertIn('info string ShinBookFile loaded 26 positions', e.diagnostics)
            self.assertFalse(any('ShinBookFile line' in line for line in e.diagnostics))
            for entry in json.loads(SOURCE.read_text())['entries']:
                moves = entry['moves']
                for n, move in enumerate(moves):
                    _, legal = position(e, moves[:n])
                    self.assertIn(move, legal)
                _, legal = position(e, moves)
                self.assertIn(entry['book_move'], legal)
                self.assertEqual(e.choose_move(moves, 1, 30)[::2],
                                 (entry['book_move'], 'dedicated_book'))
            self.assertEqual(json.loads(SOURCE.read_text())['entries'][2]['book_move'], '3h4g')
        finally:
            e.close()

    def test_gold_plan_does_not_trigger_before_attacking_silver_advance(self):
        entries = json.loads(SOURCE.read_text())['entries']
        root = next(e['moves'] for e in entries if e['id'] == 'bogin-silver83-move17-ply17-4i5h')
        e = self.engine()
        try:
            for moves in [root[:14], ['5i4h', '3c3d', '7i6h', '7a6b']]:
                self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
        finally:
            e.close()

    def test_other_response_searches(self):
        entry = json.loads(SOURCE.read_text())['entries'][1]
        moves = entry['moves'] + ['4g4f', '4a5b']
        e = self.engine()
        try:
            _, legal = position(e, moves[:-1])
            self.assertIn(moves[-1], legal)
            self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
        finally:
            e.close()

    def test_operational_entry_and_book_off(self):
        for book, own, expected in [(BASE, True, 'dedicated_book'), (OUTPUT, False, 'search')]:
            e = self.engine(book, own)
            try:
                move, _, source = e.choose_move(['5i4h', '3c3d'], 1, 30)
                self.assertEqual(source, expected)
                if book == BASE:
                    self.assertEqual(move, '7g7f')
            finally:
                e.close()
