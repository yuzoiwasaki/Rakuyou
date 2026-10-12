import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pair_teacher_generation import DEFAULT_PLAN,check_plan

class PairGenerationPlanTest(unittest.TestCase):
    def test_only_teacher_flag_can_change(self):
        ref=json.loads(DEFAULT_PLAN.read_bytes());enabled=copy.deepcopy(ref);enabled['teacher_search_enabled']=True
        check_plan(enabled,ref,True)
        for key in ('real_data_training_enabled','deployment_enabled'):
            wrong=copy.deepcopy(enabled);wrong[key]=True
            with self.assertRaises(ValueError):check_plan(wrong,ref,True)
        for key,value in [('depth',16),('timeout_seconds',31),('max_searches',181)]:
            wrong=copy.deepcopy(enabled);wrong['search'][key]=value
            with self.assertRaises(ValueError):check_plan(wrong,ref,True)
        with self.assertRaises(ValueError):check_plan(enabled,ref,False)

if __name__=='__main__':unittest.main()
