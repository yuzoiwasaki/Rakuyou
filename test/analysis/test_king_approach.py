"""Experimental feature regression against adopted evaluation references."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


class KingApproachTest(unittest.TestCase):
    def test_geometry_updates_symmetry_and_off_reference(self):
        binary = ROOT/'results/king-approach-tools/native-test'
        if not binary.is_file() or not (ROOT/'bin/params.bin').is_file():
            self.skipTest('make king-approach-test and install evaluation data first')
        fixtures = json.loads((HERE/'king_approach_positions.json').read_text())
        lines = ['moves '+' '.join(f['moves']) for f in fixtures['static']]
        content = '\n'.join(lines)+'\n'+(HERE/'evaluation_positions.txt').read_text()
        run = subprocess.run([str(binary), str(ROOT/'bin/params.bin')], input=content,
                             text=True, capture_output=True, check=True, timeout=60)
        rows = [list(map(int, row.split())) for row in run.stdout.splitlines()]
        self.assertEqual(len(rows), 4*len(content.splitlines()))
        # Intrusion pressure is removed by the supported P*64 blocker.
        self.assertGreater(rows[4][2], rows[12][2])
        # At the attacked empty square, merely playing P86 leaves pressure unchanged.
        self.assertEqual(rows[0][2], rows[4][2])
        off = [rows[i][3] for i in range(4*len(lines), len(rows), 4)]
        reference = json.loads((HERE/'evaluation_reference.json').read_text())
        self.assertEqual(off, reference['scores']['10/10'])


if __name__ == '__main__':
    unittest.main()
