import unittest
from unittest.mock import patch
from tools.learning.outcome import prepare_expanded_outcome as p
class ExpandedOutcomeTests(unittest.TestCase):
    def test_changed_selection_rejected_before_backup(self):
        with patch.object(p,'digest',return_value='bad'),patch.object(p,'verify_backup') as backup:
            with self.assertRaisesRegex(ValueError,'selection/old diagnostic'):p.load()
            backup.assert_not_called()
    def test_runtime_output_forbidden(self):
        with self.assertRaisesRegex(ValueError,'New ignored'):p.prepare(p.ROOT/'bin/expanded')
if __name__=='__main__':unittest.main()
