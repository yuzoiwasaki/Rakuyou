import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.learning.constraints import temporal_mixed as m
from tools.learning.constraints.weighted_objective import objective
from test.learning.constraints.test_weighted import row


class MixedTests(unittest.TestCase):
    def test_mix_is_half_each_loss_and_gradient(self):
        rows=[row(1),row(1,100,-500),row(2,-100,500)];delta={'a':.1,'b':-.2}
        a,ga=objective(rows,delta,0);b,gb=objective(rows,delta,1);c,gc=objective(rows,delta,.5)
        self.assertAlmostEqual(c,(a+b)/2,places=14)
        for k in delta:self.assertAlmostEqual(gc[k],(ga[k]+gb[k])/2,places=14)

    def test_train_only_one_mixed_arm_reuses_controls(self):
        groups={g:dict(outcome=dict(improvement_percent=1.),search=dict(improvement_percent=2.),max_abs_change_cp=3)
                for g in ('original','additional','all','loss')}
        report=dict(integer={s:groups for s in ('train','validation')})
        plan=dict(keys=['a'],training={},projected={})
        control=dict(reports={'old-search':report,'temporal-search':report})
        rows=[dict(id='train')];parts={'train':rows,'validation':[dict(id='validation')]}
        def train(*args):
            self.assertIs(args[0],rows);self.assertEqual(args[2],.5)
            self.assertEqual(args[4]['arm'],'mixed');self.assertEqual(args[4]['alpha'],.5)
            args[5].mkdir();(args[5]/'checkpoint.json').write_text('{}')
            return dict(delta={'a':.1},updates=200,stopping_reason='update_budget')
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);(output/'plan.json').write_text('{}')
            with patch.object(m,'load',return_value=(plan,{},[],parts,control)), \
                 patch.object(m.base,'train_arm',side_effect=train) as training, \
                 patch.object(m.base,'evaluate',return_value=report) as evaluate:
                result=m.train(output)
                self.assertEqual(training.call_count,1);self.assertEqual(evaluate.call_count,1)
                self.assertIs(result['old-search'],control['reports']['old-search'])
                self.assertIn('temporal-mixed',result)

    def test_mixed_checkpoint_cannot_resume_search(self):
        rows=[row(1)];keys=['a','b'];config=dict(max_updates=1,save_updates=[0,1],step_cp=.02,
            delta_limit_cp=.5,train_position_limit_cp=100.,max_backtracks=20,l2=1e-6)
        binding=dict(plan_sha256='test',method='projected',arm='mixed',alpha=.5)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'mixed'
            state=m.base.train_arm(rows,keys,.5,config,binding,folder,'projected',m.base.optimizer.OPTIONS)
            self.assertEqual(state,m.base.train_arm(rows,keys,.5,config,binding,folder,'projected',m.base.optimizer.OPTIONS))
            with self.assertRaises(ValueError):
                m.base.train_arm(rows,keys,0,config,dict(binding,arm='search',alpha=0),folder,'projected',m.base.optimizer.OPTIONS)
