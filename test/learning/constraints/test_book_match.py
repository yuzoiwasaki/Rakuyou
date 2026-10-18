import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from tools.analysis.audit_white_positions import Board
from tools.learning.constraints import book_match as m
from test.learning.playtest.test_match import Engine,Referee


class BookMatchTests(unittest.TestCase):
    def test_all_operational_leaves_without_score_filter(self):
        rows=m.book_starts()
        self.assertEqual([len(r['moves']) for r in rows],[9,7,6,6,14,16,16])
        self.assertEqual(sum(r['id'].startswith('black') for r in rows),2)
        self.assertEqual(rows[0]['moves'][-1],'3i3h')
        self.assertEqual(rows[1]['moves'][-1],'2g2f')
        self.assertEqual(rows[-1]['moves'][-1],'2c2d')
        games=m.first.previous.games(rows)
        self.assertEqual(len(games),14)
        for i,row in enumerate(rows):
            self.assertEqual(games[2*i]['moves'],row['moves'])
            self.assertEqual(games[2*i+1]['moves'],row['moves'])
            self.assertEqual([g['candidate_color'] for g in games[2*i:2*i+2]],['black','white'])

    def test_changed_book_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'book.txt';path.write_text('5i4h 3c3d | 7g7f\n')
            with self.assertRaisesRegex(ValueError,'17'):m.book_starts(path)

    def test_fresh_games_and_no_replay(self):
        Engine.move='resign';Engine.failure=None;Engine.calls=[]
        Referee.result='ongoing';Referee.terminal_after=None
        starts=[dict(id='alternative',moves=['7g7f'],sfen='sfen')]
        plan=dict(starts=starts,games=m.first.previous.games(starts),settings=m.first.previous.SETTINGS,
                  engines=dict(baseline='base',candidate='projected'),referee='ref',limitation='test')
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);m.seal(output/'plan.json',plan)
            with patch.object(m,'output_path',side_effect=Path),patch.object(m,'load',return_value=plan), \
                 patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                report=m.run(output);self.assertEqual(report['completed_games'],2)
                self.assertEqual(len(Engine.calls),2);self.assertEqual(m.run(output),report)
                self.assertEqual(len(Engine.calls),2)


if __name__=='__main__':unittest.main()
