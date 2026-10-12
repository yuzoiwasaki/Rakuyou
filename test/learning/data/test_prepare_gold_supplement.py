import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.learning.data import prepare_gold_supplement as prep
from tools.learning.gold_silver.gold_advance_features import gold_advance_details,scores,bucket


class GoldSupplementTests(unittest.TestCase):
    def test_worked_and_fragile_support_and_color_mirror(self):
        pieces={'6g':'G','5f':'S'}
        self.assertEqual(scores(gold_advance_details(pieces)),{'black':1,'white':0})
        mirror={str(10-int(s[0]))+chr(ord('a')+ord('i')-ord(s[1])):p.swapcase() for s,p in pieces.items()}
        self.assertEqual(scores(gold_advance_details(mirror)),{'black':0,'white':1})
        chain={'4e':'G','5f':'G'}
        d=gold_advance_details(chain)
        self.assertEqual(scores(d)['black'],3)
        self.assertEqual(next(x for x in d if x['square']=='5f')['score'],0)
        self.assertEqual(scores(gold_advance_details({'4e':'G'}))['black'],0)
        self.assertEqual(scores(gold_advance_details({'6g':'G','5f':'+S'}))['black'],0)

    def test_buckets_target_own_deepest_gold_not_opponent(self):
        d=gold_advance_details({'6d':'g','7e':'s','5i':'G'})
        self.assertEqual(bucket(d,'white'),'white:rank4:supported')
        self.assertIsNone(bucket(d,'black'))
        d=gold_advance_details({'5f':'G','4g':'S','4e':'G'})
        self.assertEqual(bucket(d,'black'),'black:rank5plus:supported')
        self.assertIsNone(bucket(gold_advance_details({'6g':'G','5f':'S'}),'black'))

    def test_order_is_independent_of_outcome_and_score(self):
        rows=[]
        for i,group in enumerate(prep.BUCKETS):
            for game in range(1,4):
                rows.append(dict(id=f'run{i}:{game}:90',run=f'run{i}',game=game,bucket=group,
                    sfen=f'position{i}-{game} b - 1',prefix24=f'prefix{i}-{game}',teacher_cp=100, stratum='black:black_win'))
        first,missing=prep.choose(rows,2,4)
        altered=copy.deepcopy(rows)
        for row in altered:row['teacher_cp']=-5000;row['stratum']='white:white_win'
        second,other=prep.choose(altered,2,4)
        self.assertEqual([r['id'] for r in first],[r['id'] for r in second])
        self.assertFalse(missing);self.assertFalse(other);self.assertEqual(len(first),16)

    def test_fixed_run_cap_and_cross_prefix_exclusion_report_shortage(self):
        rows=[dict(id=f'one:{i+1}:90',run='one',game=i+1,bucket=g,sfen=f'p{i} b - 1',prefix24=f'prefix{i}') for i,g in enumerate(prep.BUCKETS)]
        chosen,missing=prep.choose(rows,1,2)
        self.assertEqual(len(chosen),2);self.assertEqual(len(missing),6)
        chosen,missing=prep.choose(rows,1,2,forbidden_prefixes={'prefix0'})
        self.assertNotIn('one:1:90',[r['id'] for r in chosen])
        self.assertIn(prep.BUCKETS[0],[x['bucket'] for x in missing])

    def test_modified_manifest_stops_before_native_or_output(self):
        with tempfile.TemporaryDirectory(dir=prep.ROOT/'results') as d:
            target=Path(d)/'new'
            with patch.object(prep,'digest',return_value='changed'),patch.object(prep,'Probe') as native:
                with self.assertRaisesRegex(ValueError,'manifest, audited parent or probe'):prep.prepare(target)
                native.assert_not_called();self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
