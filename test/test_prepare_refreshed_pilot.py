import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_refreshed_pilot import validate_teacher,frozen_record,load_refreshed


def teacher():
    return dict(schema='rakuyou-refreshed-teacher-v1',split='train',id='id',teacher_status='accepted',teacher_cp=42,
                perspective='root-side-to-move',outcome_loss_enabled=False,excluded=None,source={'run':'run'},
                analysis={'candidates':[{'score':'42'}]},archived_reference={'teacher_cp':-999},sfen='root',side_to_move='white')


def frame():
    return dict(ok=True,root_sfen='root',root_side='white',pv=['7g7f'],leaf_side='black',leaf_eval_cached=0,leaf_eval_full=0,
                qscore=0,leaf_repetition=False,leaf_in_check=False,leaf_progress=.25,leaf_sfen='leaf',
                leaf_parts={k:[0,0,0,0] for k in ('kp','others','tempo')})


class RefreshedPilotTest(unittest.TestCase):
    def test_new_cp_connected_and_archive_preserved(self):
        row=validate_teacher(teacher(),'train');record,reason=frozen_record(row,frame())
        self.assertIsNone(reason)
        self.assertEqual(record['sample'].teacher_root_cp,42)
        self.assertEqual(record['row']['archived_reference']['teacher_cp'],-999)
        self.assertEqual(record['row']['run'],'run')
        self.assertTrue(all(x<=0 for x in record['sample'].factors()))

    def test_pending_excluded_wrong_split_or_outcome_rejected(self):
        for key,value in (('teacher_cp',None),('teacher_status','excluded'),('split','test'),('outcome_loss_enabled',True),('perspective','black')):
            row=teacher();row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_teacher(row,'train')

    def test_analysis_mismatch_rejected(self):
        row=teacher();row['analysis']['candidates'][0]['score']='-42'
        with self.assertRaises(ValueError):validate_teacher(row,'train')

    def test_frozen_root_mismatch_and_special_exclusion(self):
        row=validate_teacher(teacher(),'train');f=frame();f['root_sfen']='other'
        with self.assertRaises(ValueError):frozen_record(row,f)
        f=frame();f['qscore']=32000
        record,reason=frozen_record(row,f)
        self.assertIsNone(record);self.assertEqual(reason,'known_win_or_mate')

    def test_unbound_generation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.json';p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'Generation/audit SHA mismatch'):load_refreshed(p,p)


if __name__=='__main__':unittest.main()
