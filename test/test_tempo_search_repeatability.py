import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from check_tempo_search_repeatability import select_controls,summarize


def record(name,cp,switched=False):
    return dict(position={'id':name},comparison={'cp_change':cp,'bestmove_changed':switched})


def analysis(cp,move='7g7f',pv=None,kind='cp'):
    return dict(bestmove=move,candidates=[dict(score_type=kind,score=str(cp),pv=pv or [move])])


class RepeatabilityTest(unittest.TestCase):
    def test_largest_absolute_difference_and_switches_selected(self):
        rows=[record('small',1),record('switch1',5,True),record('largest',-500),record('switch2',-3,True)]
        self.assertEqual([r['position']['id'] for r in select_controls(rows)],['largest','switch1','switch2'])

    def test_unexpected_number_rejected(self):
        with self.assertRaises(ValueError):select_controls([record('only',1)])

    def test_baseline_spread_keeps_original_and_does_not_include_candidate(self):
        s=summarize(analysis(10),[analysis(-20,'2g2f'),analysis(30,pv=['7g7f','3c3d'])],analysis(100))
        self.assertEqual((s['baseline_cp_min'],s['baseline_cp_max']),(-20,30))
        self.assertEqual(s['distinct_baseline_bestmoves'],2)
        self.assertEqual(s['distinct_baseline_pvs'],3)

    def test_mate_disables_cp_range(self):
        s=summarize(analysis(10),[analysis(2,kind='mate')],analysis(1))
        self.assertIsNone(s['baseline_cp_min'])
        self.assertIsNone(s['baseline_cp_max'])


if __name__=='__main__':unittest.main()
