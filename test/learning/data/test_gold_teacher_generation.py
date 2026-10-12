import unittest
from unittest.mock import patch
from tools.learning.data import gold_teacher_generation as gen


class GoldTeacherGuardTests(unittest.TestCase):
    def test_changed_selection_stops_before_search(self):
        with patch.object(gen,'digest',return_value='changed'),patch.object(gen,'RecordedEngine') as engine:
            with self.assertRaisesRegex(ValueError,'preparation/audit changed'):
                gen.load_binding(gen.PREP,gen.DEFAULT_PLAN,True)
            engine.assert_not_called()

    def test_disabled_plan_cannot_search(self):
        with patch.object(gen,'RecordedEngine') as engine:
            with self.assertRaisesRegex(ValueError,'teacher-search flag'):
                gen.load_binding(gen.PREP,gen.DEFAULT_PLAN,True)
            engine.assert_not_called()

    def test_readiness_only_scope_is_exactly_sixteen_eight(self):
        plan,_,rows,entries,_,_=gen.load_binding(gen.PREP,gen.DEFAULT_PLAN,False)
        self.assertEqual({s:len(v) for s,v in rows.items()},{'train':16,'validation':8})
        self.assertEqual(plan['search']['max_searches'],24)
        self.assertFalse(plan['real_data_training_enabled']);self.assertFalse(plan['deployment_enabled'])
        self.assertEqual(len(entries),7)


if __name__=='__main__':unittest.main()
