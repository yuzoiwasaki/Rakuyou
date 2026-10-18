import unittest
from tools.analysis.audit_white_positions import Board
from tools.learning.constraints.coverage import events,nearby


class CoverageTests(unittest.TestCase):
    def board(self):
        b=Board();b.pieces={'9i':'K','5c':'k','5d':'g','5e':'s','5f':'P','1g':'P','1c':'p'}
        return b

    def test_capture_guard_then_recapture(self):
        b=self.board()
        self.assertEqual(nearby(b,False),{'5d','5e'})
        result=events(b,['5f5e','5d5e'],False)
        self.assertEqual(result,dict(captures=2,gold_silver_captures=1,
                                    own_near_king_gs_captured=1,own_gs_immediate_recapture=1))

    def test_intervening_move_not_immediate_recapture(self):
        b=self.board()
        self.assertNotIn('own_gs_immediate_recapture',events(b,['5f5e','1c1d','1g1f','5d5e'],False))

    def test_promoted_silver_not_unpromoted_guard(self):
        b=self.board();b.pieces['5e']='+s'
        self.assertEqual(nearby(b,False),{'5d'})
        self.assertNotIn('gold_silver_captures',events(b,['5f5e'],False))


if __name__=='__main__':unittest.main()
