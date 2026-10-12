
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import sys
import unittest
from pathlib import Path
from tools.learning.tempo.close_refreshed_tempo_search import select_normal, normal_difference

class FinalSearchTest(unittest.TestCase):
    def test_six_first_strata_without_expansion(self):
        rows=[dict(id=str(i),stratum=str(i%6)) for i in range(18)]
        self.assertEqual([x['id'] for x in select_normal(rows)],[str(i) for i in range(6)])
        with self.assertRaises(ValueError):select_normal(rows[:5])

    def test_move_pv_score_change(self):
        a=dict(cp=10,analysis=dict(bestmove='7g7f',candidates=[{'pv':['7g7f']}]))
        b=dict(cp=11,analysis=dict(bestmove='2g2f',candidates=[{'pv':['2g2f']}]))
        self.assertEqual(normal_difference(a,b),dict(cp_change=1,bestmove_changed=True,pv_changed=True))
        b['cp']=None;self.assertIsNone(normal_difference(a,b)['cp_change'])

if __name__=='__main__':unittest.main()
