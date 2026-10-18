import tempfile
import unittest
from pathlib import Path
from tools.learning.hybrid.objective import objective as original
from tools.learning.constraints.weighted_objective import objective
from tools.learning.constraints import weighted_projected as step
from tools.learning.constraints import projected
from tools.learning.constraints import temporal_runner as runner


def row(game,cp=0,teacher=300):
    return dict(run='r',game=game,base_cp=cp,teacher_cp=teacher,target=1,
                factors={'a':2.,'b':-1.})


class WeightedTests(unittest.TestCase):
    def test_one_root_per_game_matches_original(self):
        rows=[row(1),row(2,200,-500)];delta={'a':.1,'b':-.2}
        for alpha in (0,.5,1):
            a,g=objective(rows,delta,alpha);b,h=original(rows,delta,alpha)
            self.assertAlmostEqual(a,b,places=14)
            for k in g:self.assertAlmostEqual(g[k],h[k],places=14)

    def test_replicating_same_game_does_not_increase_weight(self):
        rows=[row(1),row(2,200,-500)];delta={'a':.1,'b':-.2}
        a,g=objective(rows,delta,0);b,h=objective([rows[0]]*3+[rows[1]],delta,0)
        self.assertAlmostEqual(a,b,places=14)
        for k in g:self.assertAlmostEqual(g[k],h[k],places=14)

    def test_finite_difference_gradient_with_l2(self):
        rows=[row(1),row(1,150,-700),row(2,200,-500)];delta={'a':.1,'b':-.2}
        _,g=objective(rows,delta,.5,.01)
        for k in delta:
            plus=dict(delta);minus=dict(delta);plus[k]+=1e-5;minus[k]-=1e-5
            numerical=(objective(rows,plus,.5,.01)[0]-objective(rows,minus,.5,.01)[0])/2e-5
            self.assertAlmostEqual(g[k],numerical,places=9)

    def test_same_objective_same_step_and_all_roots_capped(self):
        rows=[row(1),row(2,200,-500)];delta={'a':0.,'b':0.}
        a=step.propose_step(rows,delta,0);b=projected.propose_step(rows,delta,0)
        self.assertEqual(a['delta'],b['delta'])
        rows=[row(1),row(1),row(2)];rows[-1]['factors']={'a':100.,'b':-100.}
        p=step.propose_step(rows,delta,0,train_position_limit_cp=.1)
        self.assertTrue(p['accepted'])
        self.assertLess(p['loss_after'],p['loss_before'])
        for r in rows:self.assertLessEqual(abs(step.dot(r['factors'],p['delta'])),.1)

    def test_resume_and_caps(self):
        rows=[row(1),row(1,20),row(2)];keys=['a','b']
        config=dict(max_updates=2,save_updates=[0,1,2],step_cp=.02,delta_limit_cp=.5,
                    train_position_limit_cp=100.,max_backtracks=20,l2=1e-6)
        binding=dict(plan_sha256='test',method='projected',arm='search',alpha=0.)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'search'
            a=runner.train_arm(rows,keys,0,config,binding,folder,'projected',step.OPTIONS)
            b=runner.train_arm(rows,keys,0,config,binding,folder,'projected',step.OPTIONS)
            self.assertEqual(a,b);self.assertEqual(a['updates'],2)
            a['delta']['a']=1.
            with self.assertRaises(ValueError):runner.validate(a,keys,binding,config,rows)

    def test_reporting_reweights_within_group(self):
        rs=[dict(row(1),id='a'),dict(row(1),id='b'),dict(row(2),id='c')]
        pred={'a':10,'b':10,'c':-10}
        m=runner.metrics(rs,pred)
        self.assertEqual(m['games'],2)
        expected=objective([dict(r,base_cp=pred[r['id']],factors={}) for r in rs],{},0,0)[0]
        self.assertEqual(m['search']['candidate'],expected)
