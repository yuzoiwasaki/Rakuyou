
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tools.learning.gold_silver.gold_silver_pair_pilot import PROBE, CONFIG, PairProbe
from tools.learning.core.king_safety_objective import FrozenLeaf, check_gradient, objective
from tools.learning.core.king_safety_updater import initial, step, checkpoint, restore
from tools.learning.data.prepare_learning_data import ROOT
from test.learning.king_safety.test_king_safety_learning import flip_sfen

class PairLearningTest(unittest.TestCase):
    def counts(self,sfens):
        r=subprocess.run([str(PROBE),'--pair-sfen',str(ROOT/'bin/params.bin')],input='\n'.join(sfens)+'\n',text=True,capture_output=True,check=True,timeout=30)
        rows=[json.loads(x)['pair_counts'] for x in r.stdout.splitlines()]
        self.assertEqual(len(rows),len(sfens));return rows

    def test_mutual_strict_surplus_king_exclusion_and_promoted_exclusion(self):
        # The king supports the gold too; its control must not break a 1:1 tie.
        sfens=['k8/9/9/9/9/9/5S3/4G4/4K4 b - 1',
            'k3r4/9/9/9/9/9/5S3/4G4/4K4 b - 1',
            'k8/9/9/9/9/9/5+S3/4G4/4K4 b - 1',
            'k8/9/9/9/9/9/9/4GS3/4K4 b - 1']
        self.assertEqual([x['black'] for x in self.counts(sfens)],[1,0,0,0])

    def test_color_mirror(self):
        gen=json.loads((ROOT/'results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json').read_bytes())
        sfens=[x['sfen'] for x in gen['records'][:12]]
        rows=self.counts([x for s in sfens for x in (s,flip_sfen(s),flip_sfen(s,True))])
        for i in range(0,len(rows),3):
            a,b,c=rows[i:i+3];self.assertEqual(a,b);self.assertEqual(a['black'],c['white']);self.assertEqual(a['white'],c['black'])

    def test_signed_learning_and_masked_coordinates(self):
        sample=FrozenLeaf(0,-200,.25,'black',(1,0,0,0))
        check_gradient([sample],(.01,-.01)+(0,)*6,CONFIG.l2)
        state=initial(CONFIG)
        for _ in range(20):
            _,g=objective([sample],state.delta,CONFIG.l2);state=step(state,g,CONFIG)
        self.assertLess(state.delta[0],0);self.assertLess(state.delta[1],0)
        self.assertEqual(state.delta[2:],(0,)*6)
        self.assertEqual(restore(json.loads(json.dumps(checkpoint(state,CONFIG,{'sample':'signed'}))),CONFIG,{'sample':'signed'}),state)
        with self.assertRaises(ValueError):step(state,(0,)*8,CONFIG)

    def test_native_zero_and_invalid_signed_bounds(self):
        probe=PairProbe()
        try:
            row=probe.replay([])['positions'][0]
            self.assertEqual(row['eval_on'],row['base_eval_on']);self.assertEqual(row['on_parts'],row['base_on_parts'])
        finally:probe.close()
        for raw in ((32769,0),(0,-32769),(0.1,0),(0,)):
            with self.assertRaises(ValueError):PairProbe(raw)

if __name__=='__main__':unittest.main()
