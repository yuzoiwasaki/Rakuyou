import json
import subprocess
import unittest
from tools.learning.data.prepare_learning_data import ROOT
from tools.learning.gold_silver.gold_advance_features import gold_advance_details,scores
from test.learning.gold_silver.test_supported_pawn_preparation import sfen,rotated

PROBE=ROOT/'results/gold-advance-tools/gold-advance-probe'


class GoldAdvanceProbeTests(unittest.TestCase):
    def test_rank_support_scope_and_caps_match_native(self):
        fixtures=[({'6h':'G','5g':'S'},0),({'6g':'G','5f':'S'},1),
            ({'5f':'G','5g':'S'},2),({'5e':'G','5f':'S'},3),({'5d':'G','5e':'S'},3),
            ({'4c':'G','5c':'G'},6),({'5e':'G','4f':'K'},0),
            ({'6g':'G','5f':'+S'},0),({'5e':'+P','5f':'S'},0),({'8g':'G','9h':'S'},1)]
        positions=[];expected=[]
        for pieces,value in fixtures:
            for data,answer in [(pieces,dict(black=value,white=0)),(rotated(pieces),dict(black=0,white=value))]:
                self.assertEqual(scores(gold_advance_details(data)),answer)
                native=dict(data)
                if 'K' in data.values() and data.get('1i')!='K':native['1i']=None
                if 'k' in data.values() and data.get('9a')!='k':native['9a']=None
                positions.append(sfen(native));expected.append(answer)
        run=subprocess.run([str(PROBE),'--gold-sfen',str(ROOT/'bin/params.bin')],
            input='\n'.join(positions)+'\n',text=True,capture_output=True,check=True,timeout=30)
        self.assertEqual([json.loads(s)['gold_advance_scores'] for s in run.stdout.splitlines()],expected)


if __name__=='__main__':unittest.main()
