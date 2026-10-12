import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import expanded_pair_pilot as pilot

class ExpandedPairGuardTest(unittest.TestCase):
    def test_modified_leaf_or_audit_rejected_before_native(self):
        with patch.object(pilot,'digest',return_value='changed'),patch.object(pilot,'PairProbe') as native:
            with self.assertRaises(ValueError):pilot.load_records()
            native.assert_not_called()

    def test_l2_change_rejected_before_native(self):
        prep=json.loads((pilot.PREP/'report.json').read_bytes());audit=json.loads((pilot.PREP/'audit-v1.json').read_bytes())
        prep['config']['l2']=1e-5
        digests=[pilot.LEAF_SHA,pilot.AUDIT_SHA]
        with patch.object(pilot,'digest',side_effect=digests),patch.object(pilot.json,'loads',side_effect=[prep,audit]),patch.object(pilot,'load_generation',return_value=({}, {}, {}, None)),patch.object(pilot,'PairProbe') as native:
            with self.assertRaises(ValueError):pilot.load_records()
            native.assert_not_called()

if __name__=='__main__':unittest.main()
