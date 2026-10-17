import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from tools.learning.constraints import behavior as b


def record(move,kind='regular'):
    return dict(status='success',diagnosis=dict(kind=kind),analysis=dict(bestmove=move))


class BehaviorTests(unittest.TestCase):
    def test_three_way_comparison_and_missing_result(self):
        plan=dict(roots=[dict(id='one'),dict(id='two')])
        old={(i,v):record('a' if v=='baseline' else 'b') for i in ('one','two') for v in ('baseline','candidate')}
        with patch.object(b,'digest',return_value='sha'):
            result=b.comparisons(plan,old,dict(one=record('b')))
        self.assertEqual(result['valid_triples'],1)
        self.assertEqual(result['changed_bestmoves'],dict(baseline=1,old_search=0))
        self.assertEqual(result['new_attempted'],1)

    def test_diagnostic_and_failure_not_counted_as_move_changes(self):
        plan=dict(roots=[dict(id='one')]);old={('one',v):record('a') for v in ('baseline','candidate')}
        with patch.object(b,'digest',return_value='sha'):
            for r in [record('b','diagnostic'),dict(status='failed')]:
                result=b.comparisons(plan,old,dict(one=r))
                self.assertEqual(result['valid_triples'],0)
                self.assertEqual(result['changed_bestmoves'],dict(baseline=0,old_search=0))

    def test_only_new_engine_runs_and_completed_attempts_are_not_retried(self):
        rows=[dict(id='one',moves_before=['ok']),dict(id='two',moves_before=['timeout'])]
        plan=dict(roots=rows,engine='/isolated/projected/release',probe='unused')
        old={(r['id'],v):record('old') for r in rows for v in ('baseline','candidate')}
        calls=[]
        class Engine:
            def __init__(self,path):
                calls.append(('engine',str(path)));self.commands=[];self.transcript=[]
            def analyze(self,moves,depth,timeout,multipv):
                calls.append(('search',moves,depth,timeout,multipv))
                if moves==['timeout']:raise TimeoutError('test')
                return dict(bestmove='new')
            def close(self):pass
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'OUTPUT',Path(tmp)):
            (Path(tmp)/'plan.json').write_text('{}')
            with patch.object(b,'load',return_value=(plan,old)),patch.object(b,'Probe',return_value=Mock()), \
                 patch.object(b,'RecordedEngine',Engine),patch.object(b.previous,'diagnose',return_value=dict(kind='regular')):
                b.run();b.run()
            self.assertEqual(len([x for x in calls if x[0]=='search']),2)
            self.assertEqual([x[1] for x in calls if x[0]=='engine'],[plan['engine']]*2)
            self.assertIn(('search',['ok'],15,30,1),calls)
            records=b.saved(plan)
            self.assertEqual(records['one']['status'],'success')
            self.assertEqual(records['two']['status'],'failed')

    def test_saved_failure_retained_and_missing_attempt_blocks(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(b,'OUTPUT',Path(tmp)):
            output=Path(tmp);(output/'searches').mkdir();(output/'plan.json').write_text('{}')
            row=dict(id='one');plan=dict(roots=[row]);path=b.path_for(row)
            identity=dict(id='one',plan_sha256=b.digest(output/'plan.json'))
            b.write_json(path.with_suffix('.attempt.json'),identity)
            with self.assertRaisesRegex(ValueError,'Interrupted'):b.saved(plan)
            b.common.seal(path,dict(**identity,status='failed'))
            self.assertEqual(b.saved(plan)['one']['status'],'failed')
            path.with_suffix('.attempt.json').unlink()
            with self.assertRaisesRegex(ValueError,'Missing attempt'):b.saved(plan)


if __name__=='__main__':unittest.main()
