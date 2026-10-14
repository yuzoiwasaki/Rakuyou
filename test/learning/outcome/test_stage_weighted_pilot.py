import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.outcome import stage_weighted_pilot as p
class StageWeightedPilotTests(unittest.TestCase):
    def test_changed_preparation_rejected(self):
        with patch.object(p,'load_baseline',side_effect=ValueError('preparation/audit')),patch.object(p,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'preparation/audit'):p.load()
            backup.assert_not_called()
    def test_single_attempt(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            marker=Path(folder)/'marker';marker.write_text('{}')
            with patch.object(p,'MARKER',marker),patch.object(p,'load') as loader:
                with self.assertRaisesRegex(ValueError,'already'):p.run(Path(folder)/'new')
                loader.assert_not_called()
    def test_draw_summary_has_no_outcome_loss(self):
        x=dict(target=None,use_outcome_loss=False,side='white',base_cp=0,candidate_cp=-1,smooth_cp=-.2,change=-1)
        summary=p.summarize([x]);self.assertEqual(summary['all'],{'supervised':0})
        self.assertEqual(summary['draw']['side']['white']['mean_cp_change'],-1)
        self.assertNotIn('loss',summary['draw']['all'])
if __name__=='__main__':unittest.main()
