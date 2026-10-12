import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.imitation import prepare_transfer_pilot as p
class TransferPreparationTests(unittest.TestCase):
    def test_changed_inputs_rejected(self):
        with patch.object(p,'digest',return_value='bad'),patch.object(p,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'Bound'):p.load()
            backup.assert_not_called()
    def test_existing_attempt_cannot_use_new_output(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            marker=Path(folder)/'marker';marker.write_text('{}')
            with patch.object(p,'MARKER',marker),patch.object(p,'load') as loader:
                with self.assertRaisesRegex(ValueError,'already'):p.prepare(Path(folder)/'new')
                loader.assert_not_called()
if __name__=='__main__':unittest.main()
