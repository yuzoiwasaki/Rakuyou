
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import copy
import sys
import unittest
from pathlib import Path
from tools.learning.tempo.run_tempo_search import validate_result, comparison


def result(score='10',move='7g7f',kind='cp'):
    return dict(stopped_early=False,bestmove=move,candidates=[dict(depth=12,pv=[move],score_type=kind,score=score,raw='info depth 12 score '+kind+' '+score+' pv '+move)])


class SearchResultTest(unittest.TestCase):
    def test_completed_score_changes_recorded(self):
        a,b=result(),result('9','2g2f');validate_result(a);validate_result(b)
        c=comparison(a,b);self.assertEqual(c['cp_change'],-1)
        self.assertTrue(c['bestmove_changed'] and c['pv_changed'])

    def test_mate_not_subtracted_as_cp(self):
        self.assertIsNone(comparison(result(),result('3',kind='mate'))['cp_change'])

    def test_stop_depth_bound_and_move_mismatch_rejected(self):
        cases=[]
        a=result();a['stopped_early']=True;cases.append(a)
        a=result();a['candidates'][0]['depth']=11;cases.append(a)
        a=result();a['candidates'][0]['raw']+=' lowerbound';cases.append(a)
        a=result();a['bestmove']='2g2f';cases.append(a)
        for a in cases:
            with self.subTest(a=a),self.assertRaises(ValueError):validate_result(a)


if __name__=='__main__':unittest.main()
