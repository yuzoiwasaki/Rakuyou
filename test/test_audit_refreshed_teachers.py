import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_refreshed_teachers import audit_record
from analyze_positions import parse_info


class TeacherAuditTest(unittest.TestCase):
    def inputs(self):
        pending=dict(schema='pending',teacher_status='not-generated',teacher_cp=None,id='id',split='train',side_to_move='white',sfen='board w hands 1',huffman_hex='h',moves_before=['7g7f'],outcome_loss_enabled=False)
        raw='info depth 15 score cp -40 multipv 1 nodes 10 time 1 pv 3c3d'
        record={**pending,'schema':'rakuyou-refreshed-teacher-v1','teacher_status':'accepted','teacher_cp':-40,'excluded':None,'perspective':'root-side-to-move',
                'analysis':dict(stopped_early=False,bestmove='3c3d',candidates=[parse_info(raw)]),
                'commands':['usi','setoption name ShinYonenagaGyoku value true','setoption name OwnBook value false','setoption name Threads value 1','setoption name USI_Hash value 64','setoption name USI_Ponder value false','setoption name MultiPV value 1','isready','usinewgame','position startpos moves 7g7f','go depth 15','quit'],
                'transcript':['readyok',raw,'bestmove 3c3d']}
        probe=Mock();probe.replay.return_value=dict(ok=True,positions=[dict(occurrences=1),dict(sfen=pending['sfen'],huffman_hex='h',occurrences=1),dict(occurrences=1)])
        return record,pending,probe

    def test_white_cp_stays_in_root_perspective(self):
        record,pending,probe=self.inputs()
        self.assertIsNone(audit_record(record,pending,probe))
        record['teacher_cp']=40
        with self.assertRaises(ValueError):audit_record(record,pending,probe)

    def test_changed_command_or_source_rejected(self):
        for field in ('command','source'):
            record,pending,probe=self.inputs()
            if field=='command':record['commands'][-2]='go depth 16'
            else:record['sfen']='different'
            with self.assertRaises(ValueError):audit_record(record,pending,probe)

    def test_transcript_and_result_must_match(self):
        record,pending,probe=self.inputs();record['analysis']['candidates'][0]['score']='5'
        with self.assertRaises(ValueError):audit_record(record,pending,probe)
        record,pending,probe=self.inputs();record['transcript'][-1]='bestmove 2c2d'
        with self.assertRaises(ValueError):audit_record(record,pending,probe)

    def test_illegal_pv_or_wrong_side_rejected(self):
        record,pending,probe=self.inputs();probe.replay.return_value={'ok':False}
        with self.assertRaises(ValueError):audit_record(record,pending,probe)
        record,pending,probe=self.inputs();probe.replay.return_value['positions'][1]['sfen']='board b hands 1'
        with self.assertRaises(ValueError):audit_record(record,pending,probe)

    def test_repetition_must_be_excluded(self):
        record,pending,probe=self.inputs();probe.replay.return_value['positions'][-1]['occurrences']=2
        with self.assertRaises(ValueError):audit_record(record,pending,probe)
        record.update(teacher_cp=None,teacher_status='excluded',excluded='repeated_root_or_pv_history')
        self.assertEqual(audit_record(record,pending,probe),'repeated_root_or_pv_history')


if __name__=='__main__':unittest.main()
