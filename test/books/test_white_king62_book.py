"""Branch-only tests for the conditional White king62 trial."""
import json
from pathlib import Path
import unittest
from tools.experiments.build_white_king62_book import SOURCE, OUTPUT, build
from tools.analysis.paired_selfplay import UsiEngine
from test.books import test_operational_shin_book as operational_tests
ROOT = Path(__file__).resolve().parents[2]


class WhiteKing62BookTest(unittest.TestCase):
    def engine(self, own=True):
        if not (ROOT/'bin/match').is_file():
            self.skipTest('make match first')
        return UsiEngine(ROOT/'bin/match',True,own,1,64,None,32,OUTPUT)

    def test_only_reviewed_root_is_replaced(self):
        rows=lambda text:{s for s in text.splitlines() if s and not s.startswith('#')}
        base=rows((ROOT/'books/shin-yonenaga-book-v1.txt').read_text())
        trial=rows(OUTPUT.read_text())
        root=json.loads(SOURCE.read_text())['entries'][0]['moves']
        self.assertEqual(base-trial, {' '.join(root)+' | 6b7a'})
        self.assertEqual(len(trial),41)
        self.assertEqual(OUTPUT.read_text(),build())

    def test_native_entries_and_legality(self):
        e=self.engine();helper=operational_tests.OperationalBookTest()
        try:
            e.send('isready');lines=[]
            while True:
                line=e.lines.get(timeout=30);lines.append(line)
                if line=='readyok':break
            self.assertIn('info string ShinBookFile loaded 41 positions',lines)
            self.assertFalse(any('ShinBookFile line' in s for s in lines))
            for entry in json.loads(SOURCE.read_text())['entries']:
                moves=entry['moves']
                for n,m in enumerate(moves+[entry['book_move']]):
                    self.assertIn(m,helper.legal(e,moves[:n]))
                self.assertEqual(e.choose_move(moves,1,30)[::2],(entry['book_move'],'dedicated_book'))
        finally:e.close()

    def test_unregistered_reply_and_book_off_search(self):
        root=json.loads(SOURCE.read_text())['entries'][0]['moves']
        moves=root+['6c6d','9i9h']
        e=self.engine()
        try:
            self.assertIn(moves[-1],operational_tests.OperationalBookTest().legal(e,moves[:-1]))
            self.assertEqual(e.choose_move(moves,1,30)[2],'search')
        finally:e.close()
        e=self.engine(False)
        try:self.assertEqual(e.choose_move(root,1,30)[2],'search')
        finally:e.close()
