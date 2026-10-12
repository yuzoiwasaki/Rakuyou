import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools.learning.imitation import prepare_transfer_pilot as p

class TerminalResponseTests(unittest.TestCase):
    def test_forced_resignation_is_recorded_and_excluded(self):
        class FakeProbe:
            def __init__(self,*a,**kw):pass
            def close(self):pass
        class FakeEngine:
            commands=[];transcript=[]
            def __init__(self,*a):pass
            def close(self):pass
            def analyze(self,*a,**kw):return {'bestmove':'resign'}
        row=dict(id='fixture',moves_before=[],actual_move='5a6b')
        manifest=dict(accepted={'train':[row],'validation':[]},plan={'runtime_sha256':{}})
        with tempfile.TemporaryDirectory(dir=p.ROOT/'results') as folder:
            folder=Path(folder);output=folder/'out'
            with patch.object(p,'MARKER',folder/'marker'),patch.object(p,'load',return_value=(manifest,{})),\
                 patch.object(p,'Probe',FakeProbe),patch.object(p,'RecordedEngine',FakeEngine),\
                 patch.object(p,'classify',return_value=(None,'special_terminal')):
                with self.assertRaisesRegex(ValueError,'No usable'):p.prepare(output)
            report=json.loads((output/'report.json').read_bytes())
            self.assertEqual(len(report['comparisons']),2)
            self.assertEqual(report['comparisons'][1]['variant'],'forced-actual')
            self.assertEqual(report['comparisons'][1]['excluded'],'special_terminal')
            self.assertNotIn('Forced move mismatch',report['errors'])

if __name__=='__main__':unittest.main()
