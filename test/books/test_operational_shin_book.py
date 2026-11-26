"""Maintain the operational book's legality, reproduction and scope."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.books import build_operational_shin_book as builder
from tools.analysis.paired_selfplay import UsiEngine

ROOT = Path(__file__).resolve().parents[2]


class OperationalBookTest(unittest.TestCase):
    def entries(self):
        return json.loads(builder.SOURCE.read_text())['entries']

    def engine(self, own=True, max_ply=44, shin=True):
        binary = ROOT / ('bin/release' if shin else 'bin/match')
        if not binary.is_file():
            self.skipTest('make release and make match first')
        return UsiEngine(binary, shin, own, 1, 64, None, max_ply, builder.OUTPUT)

    def legal(self, engine, moves):
        engine.send('position startpos' + (' moves ' + ' '.join(moves) if moves else ''))
        engine.send('legalmoves')
        engine.send('d')
        legal = set()
        while True:
            line = engine.lines.get(timeout=10)
            if line.startswith('move: '):
                return legal
            words = line.split()
            if words and all(builder.MOVE.fullmatch(w) for w in words):
                legal.update(words)

    def test_reproduction_and_invalid_source_rejection(self):
        self.assertEqual(builder.OUTPUT.read_text(), builder.compile_operational_book())
        data = json.loads(builder.SOURCE.read_text())
        for mutation in ('duplicate', 'side', 'move'):
            bad = copy.deepcopy(data)
            if mutation == 'duplicate':
                bad['entries'].append(bad['entries'][0])
            elif mutation == 'side':
                bad['entries'][0]['side'] = 'white'
            else:
                bad['entries'][0]['book_move'] = 'invalid'
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'source.json'
                source.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    builder.compile_operational_book(source)

    def test_native_load_legality_and_every_entry(self):
        e = self.engine()
        try:
            e.send('isready')
            diagnostics = []
            while True:
                line = e.lines.get(timeout=30)
                diagnostics.append(line)
                if line == 'readyok':
                    break
            self.assertIn(f'info string ShinBookFile loaded {len(self.entries())} positions', diagnostics)
            self.assertFalse(any('ShinBookFile line' in s or 'Failed to open ShinBookFile' in s
                                 for s in diagnostics))
            for entry in self.entries():
                moves = entry['moves']
                for n, move in enumerate(moves + [entry['book_move']]):
                    self.assertIn(move, self.legal(e, moves[:n]))
                self.assertEqual(e.choose_move(moves, 1, 30)[::2],
                                 (entry['book_move'], 'dedicated_book'))
            self.assertEqual(e.choose_move(['5i4h', '3c3d'], 1, 30)[0], '7i6h')
            silver = next(x for x in self.entries()
                          if x['id']=='fourth_rook_silver38_to47_after_king71')
            self.assertEqual(silver['book_move'], '3h4g')
            white = [x for x in self.entries() if x['side']=='white']
            self.assertFalse(any(x['book_move']=='9c9d' for x in white))
            self.assertIn('6a7b', {x['book_move'] for x in white})
            self.assertEqual(next(x['book_move'] for x in white if x['id']=='fourth_rook_capture_early_pawn65'), '6d6e')
        finally:
            e.close()

    def test_unregistered_replies_do_not_force_formation(self):
        entries = {x['id']: x for x in self.entries()}
        bogin = entries['floating_exchange_ply17']['moves']
        fourth = entries['fourth_rook_prepare_silver47']['moves']
        white = entries['mainline_after_66_pawn']['moves']
        # Early attacks and skipping B77 must not force the quiet formation.
        white_replies = [white + ['8c8d','6f6e'],
                         white + ['8c8d','9g9f','8d8e','7i7h']]
        e = self.engine()
        try:
            # Developing the White gold must not prescribe later left-gold/king moves.
            for key in ('white_gold72_ply28', 'white_gold72_after_rook81_ply30'):
                entry = entries[key]
                for reply in ('3i2h', '1g1f'):
                    moves = entry['moves'] + [entry['book_move'], reply]
                    self.assertIn(reply, self.legal(e, moves[:-1]))
                    self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
            # The G32 formation is local to the reviewed rook-exchange line.
            for key, reply in [('white_rook_exchange_silver63_ply22', '4g4f'),
                               ('white_rook_exchange_gold32_ply34', '2i3g'),
                               ('white_rook_exchange_pawn44_ply38', '6h5h'),
                               ('white_rook_exchange_pawn44_after_knight37', '5f5e'),
                               ('white_rook_exchange_gold72_after_pawn16', '7h6g'),
                               ('white_rook_exchange_rook81_after_gold47', '5g5f'),
                               ('white_rook_exchange_rook81_after_gold47', '3g3f')]:
                entry = entries[key]
                moves = entry['moves'] + [entry['book_move'], reply]
                self.assertIn(reply, self.legal(e, moves[:-1]))
                self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
            for moves in [bogin[:13] + ['5a4b'], ['5i4h', '3c3d', '7i6h', '7a6b'],
                          fourth + ['4g4f', '4a5b']] + white_replies:
                self.assertIn(moves[-1], self.legal(e, moves[:-1]))
                self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
        finally:
            e.close()

    def test_floating_rook_scope_and_shared_silver_entry(self):
        entries = {x['id']: x for x in self.entries()}
        e = self.engine()
        try:
            silver = entries['floating_s42_s72_b33_ply19']['moves']
            self.assertEqual(e.choose_move(silver, 1, 30)[::2],
                             ('3i3h', 'dedicated_book'))
            # Both plans remain searched after developing the shared silver.
            for reply in ('4a3b', '4c4d', '6c6d', '7b8c', 'P*8f'):
                moves = silver + ['3i3h', reply]
                self.assertIn(reply, self.legal(e, moves[:-1]))
                self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
            knight = entries['n77_main39']['moves']
            attack = knight + ['8i7g', '6d6e']
            self.assertIn(attack[-1], self.legal(e, attack[:-1]))
            self.assertEqual(e.choose_move(attack, 1, 30)[2], 'search')
            promotion = entries['floating_exchange_ply23']['moves']
            self.assertEqual(e.choose_move(promotion, 1, 30)[::2],
                             ('2d2c+', 'dedicated_book'))
            # Moving the gold first defends 23; float instead of promoting.
            defended = entries['floating_exchange_ply23_after_g32']['moves']
            self.assertEqual(e.choose_move(defended, 1, 30)[::2],
                             ('2d2f', 'dedicated_book'))
        finally:
            e.close()

    def test_transpositions_and_fixed_first_moves(self):
        e = self.engine()
        try:
            for moves, expected in [([], '5i4h'), (['7g7f'], '5a6b')]:
                self.assertEqual(e.choose_move(moves, 1, 30)[::2], (expected, 'fixed_opening'))
            for moves, expected in [
                (['5i4h','7a6b','7g7f','3c3d'], '2g2f'),
                (['7g7f','5a6b','2h6h','5c5d','5i4h','3a4b','3i3h'], '4b5c')]:
                self.assertEqual(e.choose_move(moves, 1, 30)[::2], (expected, 'dedicated_book'))
        finally:
            e.close()

    def test_early_rook_formation_leaves_other_replies_to_search(self):
        entries = {x['id']: x for x in self.entries()}
        e = self.engine()
        try:
            # The bishop-opening choice applies after S22, not arbitrary replies.
            pawn = entries['early_rook_pawn96_before_pawn46']
            silver = entries['early_rook_silver77_after_bishop_exchange']
            # The closed-bishop formation also depends on the opponent's setup.
            closed_pawn = entries['black_closed_bishop_pawn66_ply13']
            closed_silver = entries['black_closed_bishop_silver47_ply23']
            closed_gold = entries['black_closed_bishop_gold58_ply29']
            for entry, replies in [(pawn, ('9c9d', '7b8c')),
                                   (silver, ('6c6d', '5a4b')),
                                   (closed_pawn, ('6b7c', '5a4b')),
                                   (closed_silver, ('6b7c', '9c9d')),
                                   (closed_gold, ('5c5d', '4c4b'))]:
                for reply in replies:
                    moves = entry['moves'] + [entry['book_move'], reply]
                    self.assertIn(reply, self.legal(e, moves[:-1]))
                    self.assertEqual(e.choose_move(moves, 1, 30)[2], 'search')
        finally:
            e.close()

    def test_book_off_and_late_entry_limit(self):
        entry = max(self.entries(), key=lambda x:len(x['moves']))
        ply = len(entry['moves']) + 1
        self.assertGreater(ply, 20)
        self.assertLessEqual(ply, 44)
        for own, limit, expected in [(False,44,'search'), (True,ply-1,'search'),
                                     (True,ply,'dedicated_book')]:
            e = self.engine(own=own, max_ply=limit)
            try:
                self.assertEqual(e.choose_move(entry['moves'], 1, 30)[2], expected)
            finally:
                e.close()

    def test_default_limit_and_normal_standard_book(self):
        e = self.engine(shin=False)
        try:
            self.assertEqual(e.choose_move([], 1, 30)[2], 'book')
            e.send('usi')
            lines=[]
            while True:
                line=e.lines.get(timeout=10)
                lines.append(line)
                if line=='usiok':break
            self.assertIn('option name BookMaxPly type spin default 44 min 0 max 50', lines)
        finally:
            e.close()


if __name__ == '__main__':
    unittest.main()
