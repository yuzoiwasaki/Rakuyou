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
        for mode in ([], ['exchange'], ['coverage']):
            with self.subTest(mode=mode):
                run = subprocess.run([str(binary), str(ROOT/'bin/params.bin')]+mode,
                                     input=content, text=True, capture_output=True,
                                     check=True, timeout=60)
                rows = [list(map(int, row.split())) for row in run.stdout.splitlines()]
                self.assertEqual(len(rows), 4*len(content.splitlines()))
                # Supported P*64 removes pressure; P86 leaves it unchanged.
                if mode != ['coverage']:
                    self.assertGreater(rows[4][2], rows[12][2])
                self.assertEqual(rows[0][2], rows[4][2])
                off = [rows[i][3] for i in range(4*len(lines), len(rows), 4)]
                reference = json.loads((HERE/'evaluation_reference.json').read_text())
                self.assertEqual(off, reference['scores']['10/10'])

    def test_coverage_after_exchange_and_king_retreat(self):
        binary = ROOT/'results/king-approach-tools/native-test'
        if not binary.is_file() or not (ROOT/'bin/params.bin').is_file():
            self.skipTest('make king-approach-test and install evaluation data first')
        fixtures = json.loads((HERE/'guard_coverage_positions.json').read_text())['coverage_checks']
        content = ''.join('moves '+' '.join(f['moves'])+'\n' for f in fixtures)
        run = subprocess.run([str(binary), str(ROOT/'bin/params.bin'), 'coverage'],
                             input=content, text=True, capture_output=True,
                             check=True, timeout=60)
        rows = [list(map(int, row.split())) for row in run.stdout.splitlines()]
        self.assertEqual(len(rows), len(fixtures)*4)
        for i, f in enumerate(fixtures):
            for row in rows[i*4:(i+1)*4]:
                self.assertEqual(row[1:3], f['expected'], f['id'])



if __name__ == '__main__':
    unittest.main()
