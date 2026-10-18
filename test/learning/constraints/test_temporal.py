import unittest
from tools.learning.constraints.temporal import proposals


class TemporalTests(unittest.TestCase):
    def test_fixed_offsets_same_side_even_if_game_short(self):
        row={'moves_before':['7g7f','3c3d']}
        self.assertEqual(proposals(row,{'moves':['7g7f','3c3d']}),[(24,26),(48,50)])
        # Availability is checked later: do not silently move a proposal earlier.
        self.assertTrue(all(n%2==len(row['moves_before'])%2 for _,n in proposals(row,{'moves':row['moves_before']})))

    def test_wrong_original_history_rejected(self):
        with self.assertRaisesRegex(ValueError,'history'):
            proposals({'moves_before':['7g7f']},{'moves':['2g2f']})

    def test_scores_and_results_do_not_change_offsets(self):
        row={'moves_before':['7g7f']}
        a={'moves':['7g7f'],'result':'black_win','score':9999}
        b={'moves':['7g7f'],'result':'white_win','score':-9999}
        self.assertEqual(proposals(row,a),proposals(row,b))


if __name__=='__main__':unittest.main()
