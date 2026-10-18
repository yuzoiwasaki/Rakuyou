import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.learning.constraints import temporal_teachers as data
from test.learning.hybrid.test_data import FakeProbe,FakeEngine


class TemporalTeacherTests(unittest.TestCase):
    def test_timeout_is_persisted_and_never_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('{}')
            rows=[dict(id='root1',split='train',use_outcome_loss=True,moves_before=[])]
            plan=dict(dataset_sha256='fixture',referee='unused',engine='unused',search=dict(timeout=300))
            FakeEngine.calls=0
            with patch.object(data,'output_path',side_effect=lambda p:Path(p)), \
                 patch.object(data,'load',return_value=(plan,dict(rows=rows))), \
                 patch.object(data,'Probe',FakeProbe),patch.object(data,'RecordedEngine',FakeEngine), \
                 patch.object(data,'check_root'):
                result=data.teachers(output)
                self.assertFalse(result['completed'])
                self.assertEqual(result['counts'],dict(failed=1))
                record=json.loads(data.record_path(output,'root1').read_text())
                self.assertEqual(record['transcript'],['readyok','partial info'])
                self.assertIn('quit',record['commands'])
                data.teachers(output)
                self.assertEqual(FakeEngine.calls,1)

    def test_native_referee_check_does_not_require_huffman(self):
        class Probe:
            def replay(self,moves):
                return dict(ok=True,result='ongoing',positions=[dict(sfen='x',occurrences=1)])
        data.check_root(dict(moves_before=[],sfen='x'),Probe())
        with self.assertRaisesRegex(ValueError,'history'):
            data.check_root(dict(moves_before=[],sfen='wrong'),Probe())


    def test_success_and_watchdog_forwarded_without_second_search(self):
        class Engine:
            calls=[]
            def __init__(self,*args):
                self.commands=['usi'];self.transcript=['info depth 15 score cp 12 pv 7g7f']
            def analyze(self,moves,depth,timeout,multipv):
                self.calls.append((depth,timeout,multipv))
                return dict(stopped_early=False,bestmove='7g7f',candidates=[dict(depth=15,
                    score_type='cp',score='12',pv=['7g7f'],raw=self.transcript[0])])
            def close(self):pass
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);(output/'plan.json').write_text('{}')
            plan=dict(dataset_sha256='fixture',referee='unused',engine='unused',search=dict(timeout=300))
            rows=[dict(id='x',split='train',use_outcome_loss=True,moves_before=[])]
            with patch.object(data,'output_path',side_effect=Path),patch.object(data,'load',return_value=(plan,dict(rows=rows))), \
                 patch.object(data,'Probe',FakeProbe),patch.object(data,'RecordedEngine',Engine), \
                 patch.object(data,'check_root'),patch.object(data,'classify',return_value=(12,None)):
                result=data.teachers(output)
                self.assertTrue(result['completed'])
                self.assertEqual(result['counts'],dict(accepted=1))
                self.assertEqual(data.teachers(output),result)
                self.assertEqual(Engine.calls,[(15,300,1)])
