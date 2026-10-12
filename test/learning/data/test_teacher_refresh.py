
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import sys
import unittest
from pathlib import Path
from tools.learning.data.prepare_teacher_refresh import select_rows, STRATA, pending_record


class TeacherRefreshTest(unittest.TestCase):
    def rows(self):
        return [dict(id=f'{s}:{i}',stratum=s,run=str(i),game=s,sfen=f'{s}:{i}') for s in STRATA for i in range(8)]

    def test_balanced_selection_independent_of_input_order(self):
        rows=self.rows()
        a=select_rows(rows,3,20261011);b=select_rows(list(reversed(rows)),3,20261011)
        self.assertEqual(a,b);self.assertEqual(len(a),18)
        self.assertEqual(len({(r['run'],r['game']) for r in a}),18)
        for s in STRATA:self.assertEqual(sum(r['stratum']==s for r in a),3)
        for run in {r['run'] for r in a}:self.assertLessEqual(sum(r['run']==run for r in a),6)

    def test_game_and_run_caps_are_enforced(self):
        rows=self.rows()
        for r in rows:r['run']='same';r['game']='same'
        with self.assertRaises(ValueError):select_rows(rows,1,1)
        with self.assertRaises(ValueError):select_rows(self.rows(),2,1,max_per_run=1)

    def test_duplicate_roots_cannot_fill_quota(self):
        rows=self.rows()
        for r in rows:r['sfen']='same'
        with self.assertRaises(ValueError):select_rows(rows,1,1)

    def test_archived_cp_is_not_a_fresh_teacher(self):
        r=dict(id='id',split='train',stratum='white:draw',side_to_move='white',sfen='s',huffman_hex='h',moves_before=[],
               source_path='source',source_sha256='sha',run='run',game=1,ply=1,termination='max_plies',teacher_cp=42,depth=15,provenance_status='unknown')
        p=pending_record(r)
        self.assertIsNone(p['teacher_cp']);self.assertEqual(p['archived_reference']['teacher_cp'],42)
        self.assertFalse(p['outcome_loss_enabled'])


if __name__=='__main__':unittest.main()
