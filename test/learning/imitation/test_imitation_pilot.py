import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.imitation import imitation_pilot as p
class ImitationPilotTests(unittest.TestCase):
    def test_changed_preparation_rejected(self):
        with patch.object(p,'digest',return_value='bad'),patch.object(p,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'Preparation/audit'):p.verify_inputs()
            backup.assert_not_called()
    def test_attempt_marker_prevents_different_output(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            marker=Path(folder)/'marker';marker.write_text('{}')
            with patch.object(p,'MARKER',marker),patch.object(p,'verify_inputs') as loader:
                with self.assertRaisesRegex(ValueError,'already'):p.run(Path(folder)/'new',True)
                loader.assert_not_called()
if __name__=='__main__':unittest.main()
