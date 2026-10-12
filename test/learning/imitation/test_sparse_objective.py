import unittest
import tempfile
from pathlib import Path
from tools.learning.imitation import sparse_objective as o

class SparseObjectiveTests(unittest.TestCase):
    def test_pair_gradient_and_sign(self):
        p=[{'base_gap':100,'factors':{'0:1:2:0':-1,'1:3:4:2':2}}]
        loss,g=o.objective(p,{})
        self.assertLess(g['0:1:2:0'],0)
        for k in g:
            h=.001
            a,_=o.objective(p,{k:h});b,_=o.objective(p,{k:-h})
            self.assertAlmostEqual((a-b)/(2*h),g[k],places=10)
        self.assertGreater(o.objective(p,{'1:3:4:2':.1})[0],loss)

    def test_large_gap_is_finite(self):
        import math
        for gap in (1e9,-1e9):self.assertTrue(math.isfinite(o.objective([dict(base_gap=gap,factors={})],{})[0]))

    def test_protected_lanes_and_cap(self):
        with tempfile.TemporaryDirectory(dir=o.ROOT/'results') as folder:
            for k,v in [('0:1:2:3',1),('1:3:4:1',1),('1:3:4:2',32769)]:
                with self.assertRaises(ValueError):o.write_delta(Path(folder)/'invalid.txt',{k:v})

    def test_native_protected_lane_rejected(self):
        import subprocess
        with tempfile.TemporaryDirectory(dir=o.ROOT/'results') as folder:
            path=Path(folder)/'bad.txt';path.write_text('0 0 0 3 1\n')
            with self.assertRaises(subprocess.CalledProcessError):
                o.native(['lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1'],path)

    def test_native_color_and_mirror(self):
        s='lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 1'
        f,m,r=o.native([s,o.transformed(s),o.transformed(s,True)])
        self.assertTrue(f['features'])
        self.assertEqual(f['features'],m['features'])
        self.assertEqual({tuple(x[:3]):x[3] for x in f['features']},{tuple(x[:3]):-x[3] for x in r['features']})

if __name__=='__main__':unittest.main()
