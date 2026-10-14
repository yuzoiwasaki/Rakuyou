import unittest
from tools.learning.outcome import prepare_outcome_expansion as p
class ExpansionTests(unittest.TestCase):
    def rows(self):
        return [dict(id=f'run{i}:{j}:24',run=f'run{i}',game=j,stratum=s,sfen=f'{i}-{j} b - 1',prefix24=f'p{i}-{j}',score=j) for i,s in enumerate(p.STRATA) for j in range(1,4)]
    def test_fixed_quality_independent_and_one_per_game(self):
        rows=self.rows();selected,missing=p.select(rows,2,10)
        self.assertFalse(missing);ids=[r['id'] for r in selected]
        for r in rows:r['score']=-999
        self.assertEqual(ids,[r['id'] for r in p.select(list(reversed(rows)),2,10)[0]])
        self.assertEqual(len(ids),len({p.game_key(x) for x in ids}))
    def test_shortages_remain_missing(self):
        rows=[r for r in self.rows() if r['stratum']!=p.STRATA[-1]]
        selected,missing=p.select(rows,2,10)
        self.assertEqual(missing,{p.STRATA[-1]:2});self.assertEqual(len(selected),10)
    def test_cross_split_prefix_rejected(self):
        rows=self.rows();selected,_=p.select(rows,2,10,forbidden_prefixes={r['prefix24'] for r in rows})
        self.assertEqual(selected,[])
if __name__=='__main__':unittest.main()
