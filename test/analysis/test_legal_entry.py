"""Legal-entry diagnostics: capture legality, pawn-drop mate, and color symmetry."""
import json
from pathlib import Path
import re
import subprocess
import unittest
ROOT = Path(__file__).resolve().parents[2]


def flip_sfen(sfen):
    board, side, hands, ply = sfen.split()
    rows = [re.findall(r'\+?[a-zA-Z]|[1-9]', row) for row in board.split('/')]
    return ' '.join(['/'.join(''.join(t.swapcase() for t in reversed(row)) for row in reversed(rows)),
                     'w' if side == 'b' else 'b', hands.swapcase(), ply])


def flip_move(move):
    def square(s):
        return str(10-int(s[0]))+chr(ord('a')+8-(ord(s[1])-ord('a')))
    return (move[:2] if move[1]=='*' else square(move[:2]))+square(move[2:4])+move[4:]


class LegalEntryTest(unittest.TestCase):
    def run_native(self, sfens):
        return self.run_lines(['sfen '+s for s in sfens])

    def run_lines(self, lines):
        binary = ROOT/'results/legal-entry-tools/native-test'
        if not binary.exists() or not (ROOT/'bin/params.bin').exists():
            self.skipTest('make legal-entry-test and install evaluation data first')
        r = subprocess.run([str(binary), str(ROOT/'bin/params.bin')],
                           input='\n'.join(lines)+'\n',
                           text=True, capture_output=True, check=True, timeout=60)
        rows = [{} for _ in lines]
        for line in r.stdout.splitlines():
            index, move, see, check, distance, *captures = line.split()
            rows[int(index)][move] = (int(see), int(check), int(distance),
                                     {m:int(v) for m,v in (c.split(':') for c in captures)})
        return rows

    def test_replayed_positions_match_saved_snapshots(self):
        fixtures = json.loads((ROOT/'test/analysis/legal_entry_positions.json').read_text())
        rows = self.run_lines(['moves '+' '.join(f['moves']) for f in fixtures]
                              + ['sfen '+f['sfen'] for f in fixtures])
        self.assertEqual(rows[:len(fixtures)], rows[len(fixtures):])

    def test_drop_and_pinned_capture_legality(self):
        sfens = ['3lkl3/9/4G4/9/9/9/9/9/K8 b P 1',
                 '4k4/9/4G4/9/9/9/9/9/K8 b P 1',
                 '4k4/9/4G4/9/4P4/9/9/9/K8 b P 1',
                 '4k4/4s4/9/9/9/9/9/9/K3R4 b P 1',
                 '4k4/4s4/9/9/9/9/9/9/K4R3 b P 1']
        r = self.run_native(sfens)
        self.assertNotIn('P*5b', r[0])  # Pawn-drop mate.
        self.assertIn('P*5b', r[1])     # King can escape on the back rank.
        self.assertNotIn('P*5b', r[2])  # Nifu.
        self.assertNotIn('5b4c', r[3]['P*4c'][3])  # Pinned silver.
        self.assertIn('5b4c', r[4]['P*4c'][3])

    def test_shape_difference_and_color_symmetry(self):
        fixtures = json.loads((ROOT/'test/analysis/legal_entry_positions.json').read_text())
        sfens = [f['sfen'] for f in fixtures]
        r = self.run_native(sfens+[flip_sfen(s) for s in sfens])
        self.assertNotIn('P*6d', r[0])
        self.assertGreater(r[1]['P*6d'][3]['5c6d'], 0)
        self.assertLess(r[2]['P*6d'][3]['5c6d'], 0)
        self.assertIn('5b5c', r[3]['4e5c+'][3])  # Necessary recapture stays available.
        self.assertEqual(r[4]['6i6d'][3], {})    # No immediate capture, not "undefendable".
        for i in range(len(fixtures)):
            flipped = {flip_move(m):(v[0],v[1],v[2],{flip_move(c):s for c,s in v[3].items()})
                       for m,v in r[i].items()}
            self.assertEqual(flipped, r[i+len(fixtures)])


if __name__ == '__main__':
    unittest.main()
