
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import copy,os,sys,unittest
from pathlib import Path
from tools.learning.gold_silver.final_pair_search_review import choose, raw_env

class FinalPairSearchTest(unittest.TestCase):
    def test_selection_ignores_scores_features_and_input_order(self):
        rows=[dict(row=dict(id=f'{s}:{i}',stratum=s,teacher_cp=0),feature=0) for s in ('black:black_win','black:draw','black:white_win','white:black_win','white:draw','white:white_win') for i in range(4)]
        ids=[r['row']['id'] for r in choose(rows)]
        altered=copy.deepcopy(list(reversed(rows)))
        for i,r in enumerate(altered):r['row']['teacher_cp']=i*100;r['feature']=100-i
        self.assertEqual(ids,[r['row']['id'] for r in choose(altered)])
        self.assertEqual(len(ids),6)

    def test_process_environment_restored_on_failure(self):
        keys=('RAKUYOU_PAIR_RAW_OPEN','RAKUYOU_PAIR_RAW_END');before={k:os.environ.get(k) for k in keys}
        with self.assertRaises(RuntimeError):
            with raw_env([7457,7524]):
                self.assertEqual([os.environ[k] for k in keys],['7457','7524']);raise RuntimeError('test')
        self.assertEqual({k:os.environ.get(k) for k in keys},before)

if __name__=='__main__':unittest.main()
