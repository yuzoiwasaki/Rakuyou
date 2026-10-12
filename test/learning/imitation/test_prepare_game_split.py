import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.imitation import prepare_game_split as p
class GameSplitTests(unittest.TestCase):
    def test_uniform_positions_without_quality(self):
        rows=[dict(ply=22+2*i,score=(-1)**i*i) for i in range(32)]
        expected=[22,26,32,38,44,50,54,60,66,72,78,84]
        self.assertEqual([r['ply'] for r in p.choose(rows)],expected)
        for r in rows:r['score']=9999
        self.assertEqual([r['ply'] for r in p.choose(list(reversed(rows)))],expected)
    def test_short_pool_is_not_refilled(self):
        with self.assertRaises(ValueError):p.choose([dict(ply=i) for i in range(11)])
    def test_changed_input_rejected_before_output(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            output=Path(folder)/'new'
            with patch.object(p,'digest',return_value='changed'):
                with self.assertRaisesRegex(ValueError,'Input/probe'):p.prepare(output)
            self.assertFalse(output.exists())
if __name__=='__main__':unittest.main()
