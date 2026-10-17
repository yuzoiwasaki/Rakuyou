import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.learning.playtest import diagnostic as d
from tools.learning.hybrid.runner import seal
from tools.learning.hybrid.data import write_json


class DiagnosticTests(unittest.TestCase):
    def result(self):
        return dict(bestmove='7g7f', stopped_early=False, candidates=[dict(
            depth=12, score_type='cp', score='10', pv=['2g2f'], raw='info depth 12')])

    def test_stale_printed_info_is_flagged_not_rejected(self):
        probe = Mock()
        probe.replay.return_value = dict(ok=True, result='ongoing')
        flags = d.diagnose(self.result(), dict(moves=[], root=dict(legal_moves=['7g7f'])), 20, probe)
        self.assertEqual(flags, ['reported_depth_below_requested', 'reported_pv_differs_from_bestmove'])
        self.assertEqual([c.args[0] for c in probe.replay.call_args_list], [['7g7f'], ['2g2f']])

    def test_stop_and_illegal_bestmove_rejected(self):
        r = self.result(); r['stopped_early'] = True
        with self.assertRaisesRegex(ValueError, 'Stopped'):
            d.diagnose(r, {}, 20, Mock())
        r['stopped_early'] = False
        probe=Mock(); probe.replay.return_value=dict(ok=False, error='illegal')
        with self.assertRaisesRegex(ValueError, 'Illegal history'):
            d.diagnose(r, dict(moves=[]), 20, probe)

    def test_timeout_saved_other_jobs_continue_and_no_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            root = dict(id='root', moves=[], root=dict(sfen='x'))
            plan = dict(roots=[root], settings=d.SETTINGS, referee='unused',
                        engines=dict(baseline='baseline', candidate='candidate'))
            seal(output/'plan.json', plan)
            class FakeEngine:
                commands=[]
                transcript=[]
                analyze=Mock(side_effect=TimeoutError('test timeout'))
                close=Mock()
                def __init__(self, *args): pass
            engine = FakeEngine()
            with patch.object(d, 'output_path', side_effect=Path), patch.object(d, 'load', return_value=plan), patch.object(d, 'Probe'), \
                 patch.object(d.match, 'replay', return_value=dict(result='ongoing', positions=[root['root']])), \
                 patch.object(d.RecordedEngine, '__new__', return_value=engine):
                d.run(output)
                self.assertEqual(engine.analyze.call_count, 4)
                engine.analyze.assert_any_call([], 20, 300)
                d.run(output)
                self.assertEqual(engine.analyze.call_count, 4)
            records = d.saved(output, plan)
            self.assertEqual(len(records), 4)
            self.assertTrue(all(r['status']=='failed' for r in records.values()))
            self.assertTrue(all('TimeoutError' in r['failure'] for r in records.values()))

    def test_interrupted_marker_blocks_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp); (output/'searches').mkdir()
            plan=dict(roots=[dict(id='root')], settings=d.SETTINGS)
            seal(output/'plan.json', plan)
            name=d.jobs(plan)[0][0]
            write_json(output/'searches'/f'{name}.attempt.json',
                       dict(id=name, plan_sha256=d.digest(output/'plan.json')))
            with self.assertRaisesRegex(ValueError, 'Interrupted'):
                d.saved(output, plan)


if __name__ == '__main__': unittest.main()
