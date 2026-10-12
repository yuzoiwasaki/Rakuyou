
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import copy
import json
import sys
import unittest
from pathlib import Path
from tools.learning.data.pair_teacher_generation import DEFAULT_PLAN, check_plan

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
