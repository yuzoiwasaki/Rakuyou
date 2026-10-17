"""Native formal adjudication fixtures (no search or engine data required)."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / 'results/match-tools-v2/match-referee'


@unittest.skipUnless(BINARY.exists(), 'build with python3 -m tools.learning.playtest.build_referee')
class RefereeTest(unittest.TestCase):
    def replay(self, moves='', sfen=None):
        args = [str(BINARY), '--replay'] if sfen is None else [str(BINARY), '--sfen', sfen]
        run = subprocess.run(args, input=moves + '\n', text=True, capture_output=True, check=True)
        return json.loads(run.stdout)

    def test_failed_game107_regression(self):
        # Saved game1 after107: White lance9d can promote on9i. Enumerating
        # the forbidden unpromoted alternative must not abort the referee.
        sfen = '1n1g5/1ks1g4/1pp1p4/l2ps4/3P3P1/2P1Pn1+B1/1P4P1P/3+bL2KL/L4GNR1 w RSN2Pgs5p 108'
        self.assertEqual(self.replay('', sfen)['result'], 'ongoing')
        self.assertTrue(self.replay('9d9i+', sfen)['ok'])
        self.assertFalse(self.replay('9d9i', sfen)['ok'])

    def test_invalid_structural_tokens_rejected_without_abort(self):
        for move in ['5i5i', '5i4i', '5i4h+', 'P*5a', 'L*1a', 'N*2b']:
            self.assertFalse(self.replay(move)['ok'], move)
        for sfen, move in [
            ('8k/4P4/9/9/9/9/9/9/K8 b - 1', '5b5a'),
            ('8k/9/9/9/9/9/9/4p4/K8 w - 1', '5h5i')]:
            self.assertFalse(self.replay(move, sfen)['ok'])
            self.assertTrue(self.replay(move+'+', sfen)['ok'])

    def test_start_and_illegal(self):
        start = self.replay()
        self.assertEqual(start['positions'][0]['legal_moves'], 30)
        self.assertEqual(start['result'], 'ongoing')
        for move in ['7g7e', '1a1b', 'P*5e', 'resign', 'win']:
            self.assertFalse(self.replay(move)['ok'])

    def test_fourfold_not_twofold(self):
        cycle = '5i6h 5a6b 6h5i 6b5a '
        self.assertEqual(self.replay(cycle * 2)['result'], 'ongoing')
        terminal = self.replay(cycle * 3)
        self.assertEqual(terminal['result'], 'draw')
        self.assertEqual(terminal['reason'], 'repetition')
        self.assertEqual(terminal['positions'][-1]['occurrences'], 4)
        self.assertEqual(len(terminal['positions']), 13)
        self.assertEqual(self.replay(cycle * 3 + '7g7f')['error'], 'history_after_terminal')

    def test_continuous_checker_loses(self):
        sfen = '4k4/9/4R4/9/9/9/9/9/K8 w - 1'
        cycle = '5a4a 5c4c 4a5a 4c5c '
        terminal = self.replay(cycle * 3, sfen)
        self.assertEqual(terminal['result'], 'white_win')
        self.assertEqual(terminal['reason'], 'perpetual_check')
        self.assertEqual(self.replay(cycle * 2, sfen)['result'], 'ongoing')

    def test_interrupted_check_is_draw(self):
        sfen = '4k4/9/4R4/9/9/9/9/9/K8 w - 1'
        # Return to the same checked position through one nonchecking rook move.
        cycle = '5a4a 5c3c 4a5a 3c5c '
        terminal = self.replay(cycle + '5a4a 5c4c 4a5a 4c5c ' * 2, sfen)
        self.assertEqual(terminal['result'], 'draw')
        self.assertEqual(terminal['reason'], 'repetition')

    def test_pawn_drop_mate_and_mate_terminal(self):
        sfen = '7lk/7p1/7G1/9/9/9/9/9/K8 b P 1'
        self.assertFalse(self.replay('P*1b', sfen)['ok'])
        # A rook drop on the same square is legal and mates.
        sfen = sfen.replace(' b P ', ' b R ')
        terminal = self.replay('R*1b', sfen)
        self.assertEqual(terminal['result'], 'black_win')
        self.assertEqual(terminal['reason'], 'checkmate')
        self.assertEqual(terminal['positions'][-1]['legal_moves'], 0)
        self.assertEqual(self.replay('R*1b 1a1b', sfen)['error'], 'history_after_terminal')

    def test_csa_declaration_threshold(self):
        sfen = 'RBGSKGSBR/PP7/9/9/9/9/9/9/4k4 b 2P 1'
        self.assertTrue(self.replay('', sfen)['positions'][0]['can_declare'])
        self.assertFalse(self.replay('', sfen.replace(' b 2P ', ' b P '))['positions'][0]['can_declare'])
        self.assertEqual(self.replay('', sfen)['result'], 'ongoing')

    def test_full_sfen_identity_includes_hands_and_turn(self):
        out = self.replay('7g7f 3c3d')
        positions = out['positions']
        self.assertEqual([p['side'] for p in positions], ['black', 'white', 'black'])
        self.assertEqual([p['occurrences'] for p in positions], [1, 1, 1])
        self.assertEqual(positions[-1]['sfen'].split()[1:3], ['b', '-'])

    def test_white_checker_loses(self):
        sfen = 'k8/9/9/9/9/9/4r4/9/4K4 b - 1'
        terminal = self.replay('5i4i 5g4g 4i5i 4g5g ' * 3, sfen)
        self.assertEqual(terminal['result'], 'black_win')
        self.assertEqual(terminal['reason'], 'perpetual_check')

    def test_no_legal_moves_without_check(self):
        sfen = '8k/9/6NG1/9/9/9/9/9/K8 w - 1'
        terminal = self.replay('', sfen)
        self.assertFalse(terminal['positions'][0]['in_check'])
        self.assertEqual(terminal['positions'][0]['legal_moves'], 0)
        self.assertEqual(terminal['result'], 'black_win')
        self.assertEqual(terminal['reason'], 'no_legal_moves')

    def test_white_csa_27_threshold(self):
        sfen = '4K4/9/9/9/9/9/9/pp7/rbgskgsbr w p 1'
        self.assertTrue(self.replay('', sfen)['positions'][0]['can_declare'])
        self.assertFalse(self.replay('', sfen.replace(' w p ', ' w - '))['positions'][0]['can_declare'])

    def test_underpromotion_is_in_legal_count(self):
        # Sparse rook can both promote and decline on entering the zone.
        sfen = 'k8/9/9/4R4/9/9/9/9/8K b - 1'
        out = self.replay('', sfen)
        self.assertTrue(self.replay('5d5c', sfen)['ok'])
        self.assertTrue(self.replay('5d5c+', sfen)['ok'])
        # Rook 16 destinations, 3 extra promotion variants; king 3 moves.
        self.assertEqual(out['positions'][0]['legal_moves'], 22)


class BuildGuardTest(unittest.TestCase):
    def test_output_cannot_escape_results(self):
        from tools.learning.playtest.build_referee import build
        with self.assertRaises(ValueError):
            build(ROOT / 'bin/release')

    @unittest.skipUnless(BINARY.exists(), 'native build unavailable')
    def test_existing_referee_cannot_be_overwritten(self):
        from tools.learning.playtest.build_referee import build
        before = BINARY.read_bytes()
        with self.assertRaises(FileExistsError):
            build(BINARY)
        self.assertEqual(BINARY.read_bytes(), before)
