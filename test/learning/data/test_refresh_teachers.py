
# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

import tools.learning.data.refresh_teachers as rt


def analysis(score='10',kind='cp',depth=15,raw='info depth 15 score cp 10 pv 7g7f'):
    return dict(stopped_early=False,bestmove='7g7f',candidates=[dict(score_type=kind,score=score,depth=depth,pv=['7g7f'],raw=raw)])


class RefreshTeachersTest(unittest.TestCase):
    def probe(self,ok=True,repeated=False):
        p=Mock();p.replay.return_value=dict(ok=ok,positions=[dict(occurrences=2 if repeated else 1)])
        return p

    def test_run_requires_exact_enabled_plan(self):
        plan=json.loads(rt.DEFAULT_PLAN.read_bytes())
        with self.assertRaises(ValueError):rt.check_plan(plan,plan,True)
        enabled=copy.deepcopy(plan);enabled['teacher_search_enabled']=True
        rt.check_plan(enabled,plan,True)
        with self.assertRaises(ValueError):rt.check_plan(enabled,plan,False)
        enabled['search']['depth']=16
        with self.assertRaises(ValueError):rt.check_plan(enabled,plan,True)

    def test_complete_legal_cp_accepted(self):
        self.assertEqual(rt.classify(analysis(),{'moves_before':[]},self.probe()),(10,None))

    def test_special_scores_preserved_but_not_cp_teachers(self):
        row={'moves_before':[]}
        self.assertEqual(rt.classify(analysis(kind='mate',score='3'),row,self.probe()),(None,'mate_score'))
        self.assertEqual(rt.classify(analysis(score='31000'),row,self.probe()),(None,'known_win_score'))
        self.assertEqual(rt.classify(analysis(raw='info score cp 10 lowerbound pv 7g7f'),row,self.probe()),(None,'bounded_score'))
        self.assertEqual(rt.classify(dict(bestmove='win',stopped_early=False,candidates=[]),row,self.probe()),(None,'special_terminal'))

    def test_invalid_completion_and_pv_abort(self):
        row={'moves_before':[]}
        for a,p in ((analysis(depth=14),self.probe()),(analysis(),self.probe(ok=False))):
            with self.assertRaises(ValueError):rt.classify(a,row,p)
        a=analysis();a['stopped_early']=True
        with self.assertRaises(ValueError):rt.classify(a,row,self.probe())
        a=analysis();a['bestmove']='2g2f'
        with self.assertRaises(ValueError):rt.classify(a,row,self.probe())

    def test_repeated_history_excluded(self):
        self.assertEqual(rt.classify(analysis(),{'moves_before':[]},self.probe(repeated=True)),(None,'repeated_root_or_pv_history'))

    def test_dry_run_never_calls_search_and_writes_null_teachers(self):
        plan=json.loads(rt.DEFAULT_PLAN.read_bytes())
        row=dict(schema='pending',id='id',split='train',sfen='root',huffman_hex='h',moves_before=[],teacher_cp=None,outcome_loss_enabled=False)
        rows={'train':[row],'validation':[{**row,'split':'validation','id':'val'}]}
        probe=Mock();probe.replay.return_value=dict(ok=True,positions=[dict(sfen='root',huffman_hex='h',occurrences=1)])
        engine=Mock();engine.transcript=['readyok'];engine.commands=['usi','isready','quit']
        binding=(plan,{},rows,[],[],rt.ROOT/'results/learning-tools/learning-data-probe')
        with tempfile.TemporaryDirectory(dir=rt.ROOT/'results') as d, \
                patch.object(rt,'load_binding',return_value=binding),patch.object(rt,'Probe',return_value=probe), \
                patch.object(rt,'RecordedEngine',return_value=engine):
            output=Path(d)/'dry'
            r=rt.run(Path(d)/'input',rt.DEFAULT_PLAN,output)
            engine.analyze.assert_not_called()
            self.assertEqual(r['attempted_searches'],0);self.assertFalse(r['teacher_generation_complete'])
            self.assertTrue(all(x['teacher_cp'] is None for x in r['records']))
            with self.assertRaises(FileExistsError):rt.run(Path(d)/'input',rt.DEFAULT_PLAN,output)

    def test_partial_result_saved_on_timeout_without_retry(self):
        plan=json.loads(rt.DEFAULT_PLAN.read_bytes())
        row=dict(id='id',split='train',sfen='root',huffman_hex='h',moves_before=[],teacher_cp=None,outcome_loss_enabled=False)
        probe=Mock();probe.replay.return_value=dict(ok=True,positions=[dict(sfen='root',huffman_hex='h',occurrences=1)])
        engine=Mock();engine.transcript=['readyok'];engine.commands=['go depth 15','stop','quit']
        engine.analyze.side_effect=TimeoutError('search timed out')
        binding=(plan,{}, {'train':[row],'validation':[]},[],[],rt.ROOT/'results/learning-tools/learning-data-probe')
        with tempfile.TemporaryDirectory(dir=rt.ROOT/'results') as d, \
                patch.object(rt,'load_binding',return_value=binding),patch.object(rt,'Probe',return_value=probe), \
                patch.object(rt,'RecordedEngine',return_value=engine):
            preparation=Path(d)/'input.json';output=Path(d)/'failed'
            with self.assertRaises(TimeoutError):rt.run(preparation,rt.DEFAULT_PLAN,output,execute=True)
            r=json.loads((output/'report.json').read_bytes())
            self.assertEqual(r['attempted_searches'],1);self.assertEqual(r['completed_searches'],0)
            self.assertEqual(r['records'][0]['teacher_status'],'failed')
            self.assertIsNone(r['records'][0]['teacher_cp']);self.assertFalse(r['training_ready'])
            engine.analyze.assert_called_once()
            self.assertTrue((Path(d)/'teacher-generation-attempt-v1.json').exists())


if __name__=='__main__':unittest.main()
