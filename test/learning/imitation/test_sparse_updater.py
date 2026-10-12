import unittest,json
from tools.learning.imitation import sparse_updater as u
from tools.learning.core.king_safety_updater import Config,initial,step

class SparseUpdaterTests(unittest.TestCase):
    def test_matches_existing_rmsprop(self):
        keys=[str(i) for i in range(8)];a=u.initial(keys)
        c=Config(delta_limit_cp=.01,max_step_cp=.001,step_rate_cp=.001,l2=1e-6);b=initial(c)
        for _ in range(20):
            g=tuple((i+1)*1e-5*(-1 if i%2 else 1) for i in range(8))
            a=u.step(a,dict(zip(keys,g)));b=step(b,g,c)
            self.assertEqual(tuple(a['delta'][k] for k in keys),b.delta)
            self.assertEqual(tuple(u.average(a)[k] for k in keys),b.average())
        with self.assertRaises(ValueError):u.step(a,dict(zip(keys,g)))

    def test_wrong_key_and_nan_rejected(self):
        s=u.initial(['x'])
        for g in ({'y':1},{'x':float('nan')}):
            with self.assertRaises(ValueError):u.step(s,g)

    def test_checkpoint_roundtrip_and_tamper(self):
        s=u.step(u.initial(['x']),{'x':-.01});binding={'input':'test'}
        payload=json.loads(json.dumps(u.checkpoint(s,binding)))
        self.assertEqual(u.restore(payload,binding),s)
        with self.assertRaises(ValueError):u.restore(payload,{'input':'other'})
        payload['state']['delta']['x']=.009
        with self.assertRaises(ValueError):u.restore(payload,binding)

if __name__=='__main__':unittest.main()
