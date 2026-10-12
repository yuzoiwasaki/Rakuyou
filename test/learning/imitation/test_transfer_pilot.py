import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.imitation import transfer_pilot as p
class TransferPilotTests(unittest.TestCase):
    def test_changed_preparation_rejected(self):
        with patch.object(p,'digest',return_value='bad'),patch.object(p,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'Transfer preparation'):p.load()
            backup.assert_not_called()
    def test_single_attempt(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            marker=Path(folder)/'marker';marker.write_text('{}')
            with patch.object(p,'MARKER',marker),patch.object(p,'load') as loader:
                with self.assertRaisesRegex(ValueError,'already'):p.run(Path(folder)/'new')
                loader.assert_not_called()
if __name__=='__main__':unittest.main()
