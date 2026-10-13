import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.outcome import prepare_outcome_pilot as p
class OutcomePreparationTests(unittest.TestCase):
    def test_changed_parent_rejected(self):
        with patch.object(p,'digest',return_value='bad'),patch.object(p,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'Prepared input'):p.load()
            backup.assert_not_called()
    def test_runtime_output_forbidden(self):
        with self.assertRaisesRegex(ValueError,'New ignored'):p.prepare(p.ROOT/'bin/outcome')
if __name__=='__main__':unittest.main()
