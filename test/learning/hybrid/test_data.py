"""Teacher persistence tests use fake engines only."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.learning.hybrid import data


class FakeProbe:
    def __init__(self,*args):pass
    def close(self):pass


class FakeEngine:
    calls=0
    def __init__(self,*args):
        self.commands=['usi','go depth 15'];self.transcript=['readyok','partial info']
    def analyze(self,*args,**kwargs):
        FakeEngine.calls+=1
        raise TimeoutError('fixture timeout')
    def close(self):self.commands.append('quit')


class DataTests(unittest.TestCase):
    def test_timeout_is_persisted_and_never_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('{}')
            rows=[dict(id='root1',split='train',use_outcome_loss=True,moves_before=[])]
            plan=dict(dataset_sha256='fixture',probes=dict(replay=dict(path='unused')))
            FakeEngine.calls=0
            with patch.object(data,'output_path',side_effect=lambda p:Path(p)), \
                 patch.object(data,'load_dataset',return_value=(plan,dict(rows=rows))), \
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

    def test_orphan_attempt_blocks_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'teachers').mkdir();(output/'plan.json').write_text('{}')
            data.record_path(output,'x').with_suffix('.attempt.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Orphan'):
                data.aggregate(output,dict(dataset_sha256='fixture'),[dict(id='x')])

    def test_missing_records_not_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('{}')
            result=data.aggregate(output,dict(dataset_sha256='fixture'),[dict(id='x')])
            self.assertFalse(result['completed'])
            self.assertEqual(result['records'],[])

    def test_accepted_raw_score_and_bound_guards(self):
        row=dict(id='x',split='train')
        raw='info depth 15 score cp 42 pv 7g7f'
        record=dict(schema='rakuyou-hybrid-teacher-v1',id='x',split='train',plan_sha256='p',
            status='accepted',teacher_cp=42,commands=[],transcript=[raw],analysis=dict(
            stopped_early=False,bestmove='7g7f',candidates=[dict(depth=15,score_type='cp',
            score='42',pv=['7g7f'],raw=raw)]))
        data.validate_teacher(record,row,'p')
        record['teacher_cp']=43
        with self.assertRaises(ValueError):data.validate_teacher(record,row,'p')
        record['teacher_cp']=42
        record['analysis']['candidates'][0]['raw']=raw.replace(' pv ',' lowerbound pv ')
        with self.assertRaises(ValueError):data.validate_teacher(record,row,'p')

    def test_record_checksum_and_aggregate_are_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'teachers').mkdir();(output/'plan.json').write_text('{}')
            plan=dict(dataset_sha256='fixture');row=dict(id='x',split='train')
            path=data.record_path(output,'x');sha=data.digest(output/'plan.json')
            record=dict(schema='rakuyou-hybrid-teacher-v1',id='x',split='train',plan_sha256=sha,
                        status='failed',teacher_cp=None,commands=[],transcript=[])
            data.write_json(path,record,exclusive=True)
            path.with_suffix('.sha256').write_text(data.digest(path))
            data.write_json(path.with_suffix('.attempt.json'),dict(id='x',plan_sha256=sha),exclusive=True)
            data.aggregate(output,plan,[row])
            self.assertEqual(data.load_teachers(output,plan,[row])['counts'],dict(failed=1))
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):data.load_teachers(output,plan,[row])

    def test_incomplete_dataset_rejected(self):
        with self.assertRaisesRegex(ValueError,'469'):data.validate_rows([])

    def test_masked_draw_target_rejected(self):
        frame=dict(sfen='board b - 1',progress=.2,features=[],eval_on=0)
        rows=[]
        for split,count,decisive in [('train',383,256),('validation',80,64),('diagnostic',6,0)]:
            for i in range(count):
                rows.append(dict(id=f'{split}{i}',run=split,game=i,split=split,side='black',
                    moves_before=[],sfen=frame['sfen'],features=frame,base_cp=0,factors={},
                    target=1. if i<decisive else None,use_outcome_loss=i<decisive))
        data.validate_rows(rows)
        rows[-1]['target']=.5
        with self.assertRaisesRegex(ValueError,'Masked'):data.validate_rows(rows)


if __name__=='__main__':unittest.main()
