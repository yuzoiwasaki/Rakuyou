
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from tools.learning.data.prepare_pair_expansion import BASE, HISTORY, choose, used_validation_games

class ExpansionPreparationTest(unittest.TestCase):
    def test_freshness_excludes_whole_game_not_just_root(self):
        rows=[dict(id='a',run='r',game=1),dict(id='b',run='r',game=1),dict(id='c',run='r',game=2)]
        used=used_validation_games(rows,[dict(frames=[dict(id='a')])])
        self.assertEqual([r['id'] for r in rows if (r['run'],r['game']) not in used],['c'])

    def test_unrecognized_prior_validation_rejected(self):
        with self.assertRaises(ValueError):used_validation_games([], [dict(frames=[dict(id='unknown')])])

    def test_real_pool_deterministic_strata_caps_and_disjointness(self):
        parts={s:[json.loads(x) for x in (BASE.parent/(s+'.provisional.jsonl')).read_text().splitlines()] for s in ('train','validation')}
        history=[json.loads(p.read_bytes()) for p in HISTORY]
        chosen,used=choose(parts,history)
        reversed_chosen,_=choose({s:list(reversed(rows)) for s,rows in parts.items()},history)
        self.assertEqual(chosen,reversed_chosen)
        for s,count,cap in (('train',144,8),('validation',36,12)):
            rows=chosen[s];self.assertEqual(len(rows),count)
            self.assertEqual(set(Counter(r['stratum'] for r in rows).values()),{count//6})
            self.assertEqual(len({(r['run'],r['game']) for r in rows}),count)
            self.assertLessEqual(max(Counter(r['run'] for r in rows).values()),cap)
        self.assertTrue(all((r['run'],r['game']) not in used for r in chosen['validation']))
        self.assertFalse({r['run'] for r in chosen['train']}&{r['run'] for r in chosen['validation']})

if __name__=='__main__':unittest.main()
