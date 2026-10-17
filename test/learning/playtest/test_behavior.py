import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.learning.playtest import behavior as b


def row(i=0,side='black',target=0):
    return dict(id=str(i),split='validation',side=side,target=target,run='run',game=i,
                moves_before=[],sfen='root',huffman_hex='hex',base_cp=i)


def result(depth=15,kind='cp',move='7g7f'):
    return dict(bestmove=move,stopped_early=False,candidates=[dict(depth=depth,score_type=kind,score='1',pv=['7g7f'],raw='info depth 15 score cp 1 pv 7g7f')])


class FakeProbe:
    def __init__(self,*args): pass
    def replay(self,moves):
        return dict(ok=True,positions=[dict(sfen='root',huffman_hex='hex',occurrences=1)]*(len(moves)+1))
    def close(self): pass


class FakeEngine:
    fail=False
    calls=0
    def __init__(self,path): self.commands=['usi']; self.transcript=['readyok']
    def analyze(self,*args,**kwargs):
        type(self).calls+=1
        if self.fail: raise TimeoutError('timeout')
        return result()
    def close(self): self.commands.append('quit')


class BehaviorTest(unittest.TestCase):
    def test_selection_balanced_and_score_blind(self):
        rows=[row(f'{s}:{t}:{i}',s,t) for s in ('black','white') for t in (0,1) for i in range(9)]
        selected=b.select(rows)
        self.assertEqual(len(selected),24)
        self.assertEqual({(s,t):sum(r['side']==s and r['target']==t for r in selected) for s in ('black','white') for t in (0,1)}, {(s,t):6 for s in ('black','white') for t in (0,1)})
        altered=copy.deepcopy(rows)
        for r in altered:r['base_cp']=99999
        self.assertEqual(selected,b.select(altered[::-1]))
        self.assertTrue(all('base_cp' not in r for r in selected))

    def test_regular_mate_terminal_and_failures(self):
        p=FakeProbe(); r=row()
        self.assertEqual(b.diagnose(result(),r,p)['kind'],'regular')
        self.assertIn('mate_early_depth',b.diagnose(result(3,'mate'),r,p)['flags'])
        malformed=result(3,'mate'); malformed['candidates'][0]['score']='+'
        with self.assertRaisesRegex(ValueError,'Malformed'): b.diagnose(malformed,r,p)
        self.assertEqual(b.diagnose(dict(bestmove='resign',stopped_early=False,candidates=[]),r,p)['kind'],'special_terminal')
        with self.assertRaisesRegex(ValueError,'Incomplete'): b.diagnose(result(3),r,p)
        with self.assertRaisesRegex(ValueError,'mismatch'): b.diagnose(result(move='2g2f'),r,p)
        broken=FakeProbe(); broken.replay=lambda moves:dict(ok=False)
        with self.assertRaisesRegex(ValueError,'Illegal'): b.diagnose(result(),r,broken)

    def test_repetition_bounded_diagnostics(self):
        p=FakeProbe()
        p.replay=lambda moves:dict(ok=True,positions=[dict(sfen='root',huffman_hex='hex',occurrences=2)])
        analysis=result(); analysis['candidates'][0]['raw']+=' lowerbound'
        self.assertEqual(set(b.diagnose(analysis,row(),p)['flags']),{'bounded','repetition'})

    def test_changed_binding_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp); plan=dict(schema='rakuyou-hybrid-behavior-v1',settings=b.SETTINGS,code_sha256={},inputs_sha256={'changed':'sha'},runtime_sha256={})
            b.seal(path/'plan.json',plan)
            with patch.object(b,'output_path',side_effect=lambda p:Path(p)),patch.object(b,'dependencies',return_value={}),patch.object(b,'checked',side_effect=ValueError('SHA mismatch')):
                with self.assertRaisesRegex(ValueError,'SHA'): b.load(path)

    def fixture(self,path):
        plan=dict(roots=[row()],settings=b.SETTINGS,engines=dict(baseline='base',candidate='candidate'),probe='probe')
        b.seal(path/'plan.json',plan)
        return plan

    def test_run_resume_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);plan=self.fixture(path);FakeEngine.fail=False;FakeEngine.calls=0
            with patch.object(b,'output_path',side_effect=lambda p:Path(p)),patch.object(b,'load',return_value=plan),patch.object(b,'Probe',FakeProbe),patch.object(b,'RecordedEngine',FakeEngine):
                report=b.run(path);b.run(path)
            self.assertEqual(FakeEngine.calls,2)
            self.assertEqual(report['valid_regular_pairs'],1)
            self.assertEqual(report['changed_bestmoves'],0)
            self.assertEqual(report['strata']['black_0']['valid_regular_pairs'],1)
            self.assertEqual(report['completed_searches'],2)
            self.assertFalse(report['completed'])
            self.assertNotIn('winrate',json.dumps(report))
            self.assertEqual(len(report['pairs'][0]['results']['candidate']['analysis']['candidates'][0]['pv']),1)

    def test_failed_attempt_saved_blocks_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);plan=self.fixture(path);FakeEngine.fail=True;FakeEngine.calls=0
            with patch.object(b,'output_path',side_effect=lambda p:Path(p)),patch.object(b,'load',return_value=plan),patch.object(b,'Probe',FakeProbe),patch.object(b,'RecordedEngine',FakeEngine):
                with self.assertRaises(TimeoutError): b.run(path)
                saved=b.saved(path,plan)
                record=next(iter(saved.values()))
                self.assertEqual(record['status'],'failed')
                self.assertEqual(record['commands'],['usi','quit'])
                self.assertEqual(record['transcript'],['readyok'])
                with self.assertRaisesRegex(ValueError,'Failed attempt'):b.run(path)
            self.assertEqual(FakeEngine.calls,1)
            FakeEngine.fail=False

    def test_orphan_attempt_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);plan=self.fixture(path);(path/'searches').mkdir()
            b.paths(path,row(),'baseline').with_suffix('.attempt.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'Interrupted attempt'):b.saved(path,plan)


if __name__=='__main__':unittest.main()
