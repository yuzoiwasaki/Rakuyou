#!/usr/bin/env python3
"""Updater caps, input binding, deterministic resume, and invalid-state checks."""
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"tools"))
from tempo_updater import Config,initial,step,sample_batch,checkpoint,restore,validate_state
from check_tempo_updater import synthetic_check


class UpdaterTest(unittest.TestCase):
    def test_sign_zero_and_step_cap(self):
        c=Config();s=initial(c)
        self.assertEqual(step(s,(0,0,0),c).delta,(0,0,0))
        d=step(s,(1,-1,0),c).delta
        self.assertTrue(-.25<=d[0]<0 and 0<d[1]<=.25 and d[2]==0)

    def test_total_limit_projection_and_update_cap(self):
        c=Config(delta_limit_cp=.3);s=initial(c)
        for _ in range(20):s=step(s,(-1,-1,-1),c)
        self.assertEqual(s.delta,(.3,.3,.3))
        self.assertTrue(all(abs(v)<=.3 for v in s.average()))
        with self.assertRaises(ValueError):step(s,(-1,-1,-1),c)
        with self.assertRaises(ValueError):sample_batch(s,100,c)

    def test_sampler_is_bounded_and_without_replacement(self):
        c=Config();s=initial(c)
        ids,new=sample_batch(s,256,c)
        self.assertEqual(len(set(ids)),128)
        self.assertEqual(sample_batch(s,256,c),(ids,new))
        self.assertEqual(len(sample_batch(s,5,c)[0]),5)
        with self.assertRaises(ValueError):sample_batch(s,0,c)

    def test_checkpoint_config_input_and_content_binding(self):
        c=Config();binding={"input":"synthetic"}
        data=checkpoint(step(initial(c),(1,2,3),c),c,binding)
        self.assertEqual(restore(json.loads(json.dumps(data)),c,binding).updates,1)
        with self.assertRaises(ValueError):restore(data,replace(c,l2=0),binding)
        with self.assertRaises(ValueError):restore(data,c,{"input":"different"})
        corrupt=json.loads(json.dumps(data));corrupt["state"]["delta"][0]=0
        with self.assertRaises(ValueError):restore(corrupt,c,binding)

    def test_invalid_gradient_or_state_rejected_without_mutation(self):
        c=Config();s=initial(c)
        for g in ((float("nan"),0,0),(1e308,0,0),(False,0,0)):
            with self.assertRaises(ValueError):step(s,g,c)
        self.assertEqual(s,initial(c))
        with self.assertRaises(ValueError):validate_state(replace(s,squared_gradient=(-1,0,0)),c)
        with self.assertRaises(ValueError):validate_state(replace(s,average_mass=1),c)
        with self.assertRaises(ValueError):Config(max_updates=21).validate()

    def test_synthetic_loss_decreases_and_resume_is_exact(self):
        r=synthetic_check()
        self.assertEqual(r["synthetic_updates"],20)
        self.assertEqual(r["real_data_updates"],0)
        self.assertTrue(r["resume_identical"])
        self.assertLess(r["final_synthetic_loss"],r["initial_synthetic_loss"])


if __name__=="__main__":unittest.main()
