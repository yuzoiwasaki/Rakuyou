import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.constraints import guarded_match as m
from test.learning.playtest.test_match import Engine, Referee


class GuardedMatchTests(unittest.TestCase):
    def test_same_seven_starts_and_color_swaps(self):
        starts=m.book.book_starts();games=m.rules.games(starts)
        self.assertEqual(len(games),14)
        for i,start in enumerate(starts):
            pair=games[2*i:2*i+2]
            self.assertEqual([g['moves'] for g in pair],[start['moves']]*2)
            self.assertEqual([g['candidate_color'] for g in pair],['black','white'])

    def plan(self):
        starts=[dict(id='book',moves=['7g7f'],sfen='sfen')]
        return dict(starts=starts,games=m.rules.games(starts),settings=m.rules.SETTINGS,
                    engines=dict(baseline='base',candidate='guarded'),referee='ref',limitation='test')

    def test_fresh_games_then_reuse_completed(self):
        Engine.move='resign';Engine.failure=None;Engine.calls=[]
        Referee.result='ongoing';Referee.terminal_after=None
        plan=self.plan()
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);m.seal(output/'plan.json',plan)
            with patch.object(m,'output_path',side_effect=Path),patch.object(m,'load',return_value=plan),patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                report=m.run(output)
                self.assertEqual(report['completed_games'],2)
                self.assertEqual(report['completed_pairs'],1)
                self.assertEqual(len(Engine.calls),2)
                self.assertEqual(report,m.run(output))
                self.assertEqual(len(Engine.calls),2)

    def test_failed_game_not_retried(self):
        Engine.failure=TimeoutError('timeout');Engine.calls=[]
        Referee.result='ongoing';Referee.terminal_after=None
        plan=self.plan()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp);m.seal(output/'plan.json',plan)
                with patch.object(m,'output_path',side_effect=Path),patch.object(m,'load',return_value=plan),patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                    with self.assertRaises(TimeoutError):m.run(output)
                    with self.assertRaisesRegex(ValueError,'Failed game'):m.run(output)
                self.assertEqual(len(Engine.calls),1)
                self.assertEqual(m.saved(output,plan)[1]['result'],'error')
        finally:Engine.failure=None

    def test_plan_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);m.seal(output/'plan.json',{'candidate':'old'})
            with patch.object(m,'output_path',side_effect=Path),patch.object(m,'specification',return_value={'candidate':'new'}):
                with self.assertRaisesRegex(ValueError,'Frozen'):m.load(output)
