import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tools.learning.outcome import outcome_search_review as p
class OutcomeSearchTests(unittest.TestCase):
    def test_changed_candidate_rejected_before_output(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            out=Path(folder)/'new'
            with patch.object(p,'MARKER',Path(folder)/'unused-marker'),patch.object(p,'digest',return_value='bad'):
                with self.assertRaisesRegex(ValueError,'candidate changed'):p.run(out)
            self.assertFalse(out.exists())
    def test_single_attempt_guard(self):
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            marker=Path(folder)/'marker';marker.write_text('{}')
            with patch.object(p,'MARKER',marker),patch.object(p,'digest') as digest:
                with self.assertRaisesRegex(ValueError,'already'):p.run(Path(folder)/'new')
                digest.assert_not_called()
if __name__=='__main__':unittest.main()
