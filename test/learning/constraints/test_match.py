import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.learning.constraints import match as m
from test.learning.playtest.test_match import Engine,Referee


class ProjectedMatchTests(unittest.TestCase):
    def setUp(self):
        Engine.move='resign';Engine.failure=None;Engine.calls=[]
        Referee.result='ongoing';Referee.reason=None;Referee.terminal_after=None;Referee.declare=False

    def plan(self):
        starts=[dict(id='start',moves=['7g7f'],sfen='sfen')]
        return dict(starts=starts,games=m.previous.games(starts),settings=m.previous.SETTINGS,
                    engines=dict(baseline='baseline',candidate='projected'),referee='ref',limitation='test')

    def test_both_games_fresh_and_completed_not_replayed(self):
        plan=self.plan()
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);m.seal(output/'plan.json',plan)
            with patch.object(m,'output_path',side_effect=Path),patch.object(m,'load',return_value=plan), \
                 patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                report=m.run(output)
                self.assertEqual(report['completed_games'],2)
                self.assertEqual([c[0] for c in Engine.calls],['baseline','projected'])
                self.assertTrue(all(c[1]==['7g7f'] for c in Engine.calls))
                self.assertEqual(m.run(output),report)
                self.assertEqual(len(Engine.calls),2)

    def test_timeout_is_failure_not_loss_and_blocks_retry(self):
        Engine.failure=TimeoutError('test');plan=self.plan()
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);m.seal(output/'plan.json',plan)
            with patch.object(m,'output_path',side_effect=Path),patch.object(m,'load',return_value=plan), \
                 patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                with self.assertRaises(TimeoutError):m.run(output)
                report=m.unseal(output/'report.json')
                self.assertEqual(report['candidate']['errors'],1)
                self.assertEqual(report['candidate']['losses'],0)
                with self.assertRaisesRegex(ValueError,'Failed game'):m.run(output)
                self.assertEqual(len(Engine.calls),1)


if __name__=='__main__':unittest.main()
