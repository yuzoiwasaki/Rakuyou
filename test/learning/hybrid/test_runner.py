import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.learning.hybrid import runner


def rows():
    return [dict(id=f'{split}-{side}-{target}', split=split, side=side,
                 target=target, use_outcome_loss=True, base_cp=0.,
                 factors={f'{side}-{target}': 1.}, teacher_cp=100*(2*target-1))
            for split in ('train', 'validation')
            for side in ('black', 'white') for target in (0., 1.)]


class RunnerTests(unittest.TestCase):
    def test_shared_cohort_rejects_failed_missing_and_duplicate_teachers(self):
        data = dict(rows=rows())
        records = [dict(id=r['id'], status='accepted', teacher_cp=r['teacher_cp']) for r in data['rows']]
        parts, _, excluded = runner.cohort(data, dict(completed=True, records=records))
        self.assertEqual({s: len(r) for s, r in parts.items()}, dict(train=4, validation=4))
        self.assertEqual(excluded, [])
        for bad in (records[:-1], records[:-1]+records[:1],
                    [{**records[0], 'status': 'failed'}]+records[1:]):
            with self.assertRaises(ValueError):
                runner.cohort(data, dict(completed=True, records=bad))

    def test_draw_never_enters_any_arm(self):
        data = dict(rows=rows()+[dict(id='draw', split='train', target=None,
                                      use_outcome_loss=False, factors={'draw-only': 1.})])
        records = [dict(id=r['id'], status='accepted', teacher_cp=r['teacher_cp'])
                   for r in data['rows'] if r['use_outcome_loss']]
        parts, _, _ = runner.cohort(data, dict(completed=True, records=records))
        self.assertNotIn('draw-only', {k for r in parts['train'] for k in r['factors']})

    def test_exclusion_cannot_remove_side_result_stratum(self):
        data = dict(rows=rows())
        records = [dict(id=r['id'], status='accepted', teacher_cp=r['teacher_cp']) for r in data['rows']]
        records[0].update(status='excluded', teacher_cp=None)
        with self.assertRaises(ValueError):
            runner.cohort(data, dict(completed=True, records=records))

    def test_metrics_use_same_two_losses_and_preserve_white_perspective(self):
        selected = rows()[:4]
        predictions = {r['id']: 50*(2*r['target']-1) for r in selected}
        result = runner.split_metrics(selected, predictions)
        for side in ('black', 'white'):
            for measure in ('search_ce', 'outcome_ce'):
                self.assertGreater(result['side'][side][measure]['improvement_percent'], 0)
        self.assertEqual(result['all']['toward_winner'], 4)
        self.assertEqual(result['all']['away_from_winner'], 0)

    def test_training_resume_is_identical_and_rejects_binding_change(self):
        selected = rows()[:4]
        keys = sorted({k for r in selected for k in r['factors']})
        config = dict(max_updates=5, save_updates=[0, 2, 5], l2=1e-6,
                      step_cp=.02, delta_limit_cp=.5, train_position_limit_cp=100., max_backtracks=20)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)/'mixed'
            final = runner.train_arm(selected, keys, .5, config, {'arm': 'mixed'}, directory)
            # Replaying from a persisted intermediate arithmetic checkpoint is exact.
            intermediate = runner.unseal(directory/'checkpoint-002.json')
            runner.seal(directory/'checkpoint.json', intermediate)
            resumed = runner.train_arm(selected, keys, .5, config, {'arm': 'mixed'}, directory)
            self.assertEqual(final, resumed)
            self.assertTrue(all(r['loss_after'] < r['loss_before'] for r in final['trajectory']))
            with self.assertRaises(ValueError):
                runner.train_arm(selected, keys, .5, config, {'arm': 'search'}, directory)
            payload = json.loads((directory/'checkpoint.json').read_text())
            payload['delta'][keys[0]] = .4
            (directory/'checkpoint.json').write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                runner.unseal(directory/'checkpoint.json')

    def test_native_component_audit_rejects_protected_change(self):
        frame = dict(features=[[0, 1, 2, 1]], progress=.25, sfen='board b - 1',
                     eval_on=0, eval_off=0,
                     on_parts={'kp': [0]*4, 'others': [0]*4, 'tempo': [0]*4},
                     off_parts={'kp': [0]*4, 'others': [0]*4, 'tempo': [0]*4})
        row = dict(features=frame, side='black', base_cp=0, factors={'0:1:2:0': .5})
        after = copy.deepcopy(frame)
        for mode in ('on_parts', 'off_parts'):
            after[mode]['kp'][0] = 32768
        self.assertEqual(runner.check_frame(row, after, {'0:1:2:0': 32768}), 0)
        after['on_parts']['tempo'][1] = 1
        with self.assertRaises(ValueError):
            runner.check_frame(row, after, {'0:1:2:0': 32768})


if __name__ == '__main__':
    unittest.main()
