"""Check source integration against the previously adopted binary and native probe."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from tools.analysis.paired_selfplay import UsiEngine

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


class AdoptedEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((HERE / 'evaluation_reference.json').read_text())
        params = ROOT / 'bin/params.bin'
        if not params.is_file():
            raise unittest.SkipTest('evaluation data required')
        if hashlib.sha256(params.read_bytes()).hexdigest() != cls.reference['params_sha256']:
            raise unittest.SkipTest('golden values require the reference evaluation data')

    def test_full_incremental_and_unmake_match_adopted_reference(self):
        binary = ROOT / 'results/support-chain-tools/native-test'
        if not binary.is_file():
            self.skipTest('make support-chain-test first')
        run = subprocess.run([str(binary), str(ROOT / 'bin/params.bin')],
                             input=(HERE / 'evaluation_positions.txt').read_text(),
                             text=True, capture_output=True, check=True, timeout=60)
        actual = {key: [] for key in self.reference['scores']}
        for line in run.stdout.splitlines():
            contact, support, black, white, score = map(int, line.split())
            actual[f'{support}/{contact}'].append(score)
        self.assertEqual(actual, self.reference['scores'])

    def test_usi_adopted_defaults(self):
        binary = ROOT / 'bin/release'
        if not binary.is_file():
            self.skipTest('make release first')
        output = subprocess.run([str(binary)], input='usi\nquit\n', cwd=ROOT / 'bin',
                                text=True, capture_output=True, check=True, timeout=10).stdout
        self.assertIn('id name Rakuyou\n', output)
        self.assertIn('option name ExperimentalSupportChainBonus type spin default 10 min 0 max 10', output)
        self.assertIn('option name KingContactDeficitBonus type spin default 10 min 0 max 10', output)
        self.assertIn('option name ShinBookFile type filename default shin-yonenaga-book-v1.txt', output)

    def test_fixed_depth_search_matches_adopted_reference(self):
        binary = ROOT / 'bin/release'
        if not binary.is_file():
            self.skipTest('make release first')
        data = json.loads((HERE / 'search_reference.json').read_text())
        for case in data['cases']:
            with self.subTest(position=case['position'], support=case['support'], contact=case['contact']):
                engine = UsiEngine(binary, True, False, 1, 64, None, 0,
                                   support=case['support'], contact=case['contact'])
                try:
                    engine.new_game()
                    best, analysis, source = engine.choose_move(case['moves'], 7, 30)
                    self.assertEqual(source, 'search')
                    self.assertEqual(best, case['bestmove'])
                    self.assertEqual({k: analysis[k] for k in ('depth', 'score_type', 'score', 'pv')}, case['analysis'])
                finally:
                    engine.close()
