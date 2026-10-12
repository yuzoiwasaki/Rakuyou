
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
from unittest.mock import patch
from tools.learning.tempo.refreshed_tempo_pilot import DEFAULT_PLAN, validate_plan, choose, learn, cached_records
from tools.learning.core.tempo_updater import Config
from tools.learning.core.tempo_objective import FrozenLeaf


def saved(update,loss,changed):return dict(update=update,validation=dict(loss=loss,changed_integer_scores=changed))


class RefreshedRunnerTest(unittest.TestCase):
    def test_training_gate_and_untested_settings_rejected(self):
        reference=json.loads(DEFAULT_PLAN.read_bytes())
        validate_plan(reference,reference,False)
        with self.assertRaises(ValueError):validate_plan(reference,reference,True)
        enabled=copy.deepcopy(reference);enabled['real_data_training_enabled']=True
        validate_plan(enabled,reference,True)
        with self.assertRaises(ValueError):validate_plan(enabled,reference,False)
        enabled['optimizer']['max_updates']=21
        with self.assertRaises(ValueError):validate_plan(enabled,reference,True)

    def test_selection_requires_improvement_and_changed_val(self):
        self.assertEqual(choose([saved(0,1,0),saved(5,1,5),saved(10,.9,0),saved(20,1.1,5)]),0)
        self.assertEqual(choose([saved(0,1,0),saved(5,.99,2),saved(10,.99,3),saved(20,.995,4)]),5)
        self.assertEqual(choose([saved(0,1,0),saved(5,.99,2),saved(10,.98,3),saved(20,.97,4)]),20)

    def test_fixed_twenty_synthetic_updates_and_progress(self):
        snapshots=[];counts=[]
        state=learn([FrozenLeaf(0,200,.5,'black','black')],Config(),snapshots.append,lambda s:counts.append(s.updates))
        self.assertEqual([s.updates for s in snapshots],[0,5,10,20])
        self.assertEqual(counts,list(range(1,21)));self.assertEqual(state.updates,20)
        self.assertTrue(all(abs(x)<=5 for x in state.delta))

    def test_update_error_stops_without_retry(self):
        with patch('tools.learning.tempo.refreshed_tempo_pilot.advance',side_effect=ValueError('nonfinite')) as advance:
            saved_states=[]
            with self.assertRaises(ValueError):learn([FrozenLeaf(0,200,.5,'black','black')],Config(),saved_states.append)
            advance.assert_called_once();self.assertEqual(len(saved_states),1)

    def test_cache_binding_and_membership_rejected(self):
        with patch('tools.learning.tempo.refreshed_tempo_pilot.digest',return_value='wrong'):
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):cached_records(None,'train',[],'expected')


if __name__=='__main__':unittest.main()
