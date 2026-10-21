import copy
from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.learning.constraints import guarded_behavior as b
from test.learning.playtest.test_behavior import row, FakeEngine, FakeProbe


class GuardedBehaviorTests(unittest.TestCase):
    def rows(self):
        return [dict(row(f'{c}:{s}:{t}:{i}',s,t),cohort=c,sfen=f'{c}:{s}:{t}:{i}',game=i//2)
                for c in ('original','additional') for s in ('black','white') for t in (0,1) for i in range(10)]

    def test_balanced_blind_distinct_games(self):
        rows=self.rows(); selected=b.select(rows)
        self.assertEqual(Counter((r['cohort'],r['side'],r['target']) for r in selected),
                         Counter({(c,s,t):3 for c in ('original','additional') for s in ('black','white') for t in (0,1)}))
        for c,s,t in {(r['cohort'],r['side'],r['target']) for r in selected}:
            self.assertEqual(len({r['game'] for r in selected if (r['cohort'],r['side'],r['target'])==(c,s,t)}),3)
        changed=copy.deepcopy(rows)
        for r in changed:r['base_cp']=99999;r['teacher_cp']=-99999
        self.assertEqual(selected,b.select(changed[::-1]))
        with self.assertRaises(ValueError):b.select(rows[:10])

    def test_duplicate_positions_rejected(self):
        rows=self.rows()
        for r in rows:r['sfen']='same'
        with self.assertRaisesRegex(ValueError,'Duplicate'):b.select(rows)

    def test_changed_plan_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);b.common.seal(path/'plan.json',{'version':1})
            with patch.object(b,'OUTPUT',path),patch.object(b,'specification',return_value={'version':2}):
                with self.assertRaisesRegex(ValueError,'Frozen'):b.load()

    def fixture(self,path):
        plan=dict(roots=[dict(row(),cohort='additional')],settings=b.SETTINGS,
                  engines=dict(baseline='base',candidate='candidate'),probe='probe')
        b.common.seal(path/'plan.json',plan)
        return plan

    def test_run_resume_cohort_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);plan=self.fixture(path);FakeEngine.fail=False;FakeEngine.calls=0
            with patch.object(b,'OUTPUT',path),patch.object(b,'load',return_value=plan),patch.object(b.previous,'Probe',FakeProbe),patch.object(b.previous,'RecordedEngine',FakeEngine):
                report=b.run();b.run()
            self.assertEqual(FakeEngine.calls,2)
            self.assertEqual(report['cohort_strata']['additional_black_0'],{'valid':1,'changed':0})

    def test_failure_preserved_and_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);plan=self.fixture(path);FakeEngine.fail=True;FakeEngine.calls=0
            try:
                with patch.object(b,'OUTPUT',path),patch.object(b,'load',return_value=plan),patch.object(b.previous,'Probe',FakeProbe),patch.object(b.previous,'RecordedEngine',FakeEngine):
                    with self.assertRaises(TimeoutError):b.run()
                    with self.assertRaisesRegex(ValueError,'Failed attempt'):b.run()
                self.assertEqual(FakeEngine.calls,1)
                self.assertEqual(next(iter(b.previous.saved(path,plan).values()))['status'],'failed')
            finally:FakeEngine.fail=False
