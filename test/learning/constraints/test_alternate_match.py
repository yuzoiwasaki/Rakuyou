import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from tools.analysis.audit_white_positions import Board
from tools.learning.constraints import alternate_match as m
from test.learning.playtest.test_match import Engine,Referee


class AlternateTests(unittest.TestCase):
    def test_rotation_involution_and_hands(self):
        s='4k4/9/9/9/4+p4/9/9/9/4K4 b 2R3p 43'
        rotated=m.rotated(s)
        self.assertEqual(rotated,'4k4/9/9/9/4+P4/9/9/9/4K4 w 3P2r')
        self.assertEqual(m.rotated(rotated),m.normalized(s))
        self.assertEqual(m.keys(s),m.keys(rotated))

    def test_move_order_equivalence(self):
        a=Board();b=Board()
        for move in ['7g7f','3c3d','2g2f','8c8d']:a.push(move)
        for move in ['2g2f','8c8d','7g7f','3c3d']:b.push(move)
        self.assertEqual(m.keys(a.sfen()),m.keys(b.sfen()))

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
