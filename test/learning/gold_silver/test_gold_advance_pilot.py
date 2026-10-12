import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.learning.gold_silver import gold_advance_pilot as pilot


class GoldAdvancePilotTest(unittest.TestCase):
    def test_changed_preparation_rejected_before_backup_or_native(self):
        with patch.object(pilot,'digest',return_value='changed'),patch.object(pilot,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'Preparation/audit SHA'):pilot.load_prepared()
            backup.assert_not_called()

    def test_l2_change_rejected_even_when_plan_has_no_quality_field(self):
        p=json.loads((pilot.PREPARATION/'report.json').read_text())
        a=json.loads((pilot.PREPARATION/'audit-v1.json').read_text())
        p['plan']['config']['l2']=1e-4
        with patch.object(pilot,'digest',side_effect=[pilot.REPORT_SHA,pilot.AUDIT_SHA]),\
             patch.object(pilot.json,'loads',side_effect=[p,a]),patch.object(pilot,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'fixed, audited'):pilot.load_prepared()
            backup.assert_not_called()

    def test_single_attempt_guard_is_independent_of_output_name(self):
        with tempfile.TemporaryDirectory(dir=pilot.ROOT/'results') as d:
            marker=Path(d)/'attempt.json';marker.write_text('{}')
            with patch.object(pilot,'MARKER',marker),patch.object(pilot,'load_prepared') as loader:
                with self.assertRaisesRegex(ValueError,'already closed/started'):
                    pilot.run(Path(d)/'new-output',True)
                loader.assert_not_called()
                self.assertFalse((Path(d)/'new-output').exists())

    def test_selection_requires_integer_change_and_bounded_improvement(self):
        def candidate(update,loss,changed=1,bounded=True):
            return dict(update=update,validation_loss_plus_l2=loss,within_total_limit=bounded,
                        summary={'validation':{'all':{'changed':changed}}})
        base=candidate(0,.5,0)
        self.assertEqual(pilot.choose([base,candidate(5,.4,0),candidate(10,.3,bounded=False)]),0)
        self.assertEqual(pilot.choose([base,candidate(5,.45),candidate(10,.45),candidate(20,.49)]),5)
        self.assertEqual(pilot.choose([base,candidate(5,.51)]),0)


if __name__=='__main__':unittest.main()
