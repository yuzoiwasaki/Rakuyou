import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.learning.playtest import match as m


class Referee:
    result='ongoing';reason=None;terminal_after=None;declare=False
    def __init__(self,*args):pass
    def close(self):pass
    def replay(self,moves):
        if 'illegal' in moves:return dict(ok=False,error='illegal_history')
        terminal=self.terminal_after is not None and len(moves)>=self.terminal_after
        return dict(ok=True,result=self.result if terminal else 'ongoing',reason=self.reason if terminal else None,
                    positions=[dict(sfen='sfen',occurrences=1,in_check=False,side='black' if i%2==0 else 'white',can_declare=self.declare,legal_moves=4) for i in range(len(moves)+1)])


class Engine:
    move='resign';failure=None;calls=[]
    def __init__(self,path):self.commands=[];self.transcript=[];self.path=path
    def snapshot(self):return dict(commands=list(self.commands),transcript=list(self.transcript))
    def new_game(self):self.commands.append('usinewgame')
    def choose_move(self,moves,*args):
        self.calls.append((self.path,list(moves)));self.commands.append('go depth 15');self.transcript.append('info searching')
        if self.failure:raise self.failure
        return self.move,dict(depth=15,score_type='cp',score='10',raw='info depth 15 score cp 10 pv '+self.move),'search'
    def close(self):self.commands.append('quit')


class MatchTest(unittest.TestCase):
    def setUp(self):
        Engine.move='resign';Engine.failure=None;Engine.calls=[]
        Referee.result='ongoing';Referee.reason=None;Referee.terminal_after=None;Referee.declare=False
    def plan(self):
        starts=[dict(id='start',moves=['7g7f'],sfen='sfen')]
        return dict(starts=starts,games=m.games(starts),settings={**m.SETTINGS,'max_additional_plies':3},engines=dict(baseline='base',candidate='cand'),referee='ref',limitation='Fixed depth pilot')
    def play(self,game=None,ref=None):
        plan=self.plan();record={};engines={v:Engine(v) for v in ('baseline','candidate')}
        m.play(game or plan['games'][0],plan,ref or Referee(),engines,record,lambda:None)
        return record
    def test_swap_and_prefix_turn(self):
        plan=self.plan()
        self.assertEqual([g['candidate_color'] for g in plan['games']],['black','white'])
        a=self.play(plan['games'][0]);b=self.play(plan['games'][1])
        self.assertEqual(a['records'][0]['player'],'baseline')
        self.assertEqual(b['records'][0]['player'],'candidate')
        self.assertEqual(a['result'],'black_win')
        self.assertEqual(Engine.calls[0][1],['7g7f'])
    def test_formal_results_and_maxplies(self):
        Engine.move='3c3d'
        for result,reason in [('draw','repetition'),('white_win','perpetual_check'),('black_win','checkmate')]:
            Referee.result=result;Referee.reason=reason;Referee.terminal_after=2
            record=self.play()
            self.assertEqual((record['result'],record['reason']),(result,reason))
            self.assertEqual(len(record['records']),1)
        Referee.terminal_after=None
        record=self.play()
        self.assertEqual(record['result'],'unresolved')
        self.assertEqual(record['reason'],'max_additional_plies')
        self.assertEqual(len(record['records']),3)
    def test_declaration_and_illegal(self):
        Engine.move='win'
        with self.assertRaisesRegex(ValueError,'Invalid declaration'):self.play()
        Referee.declare=True
        self.assertEqual(self.play()['result'],'white_win')
        Engine.move='illegal'
        with self.assertRaisesRegex(ValueError,'Illegal'):self.play()
    def test_search_completion_and_early_mate(self):
        plan=self.plan();plan['settings']['max_additional_plies']=1;game=plan['games'][0]
        engines={v:Engine(v) for v in ('baseline','candidate')}
        for analysis,source,expected in [(None,'search','Missing'),(dict(depth=16,score_type='cp',score='1',raw='info'),'search','Invalid'),(dict(depth=15,score_type='cp',score='1',raw='info'),'book','Missing')]:
            engines['baseline'].choose_move=lambda *args,a=analysis,s=source:("3c3d",a,s)
            with self.assertRaisesRegex(ValueError,expected):m.play(game,plan,Referee(),engines,{},lambda:None)
        engines['baseline'].choose_move=lambda *args:('3c3d',dict(depth=4,score_type='mate',score='3',raw='info lowerbound'),'search')
        record={};m.play(game,plan,Referee(),engines,record,lambda:None)
        self.assertEqual(record['records'][0]['diagnostics'],['mate_early_depth','bounded_score'])

    def test_normal_bestmove_with_throttled_info(self):
        plan=self.plan();game=plan['games'][0]
        engines={v:Engine(v) for v in ('baseline','candidate')}
        engines['baseline'].choose_move=lambda *args:('8f8g',dict(depth=12,
            score_type='cp',score='9559',raw='info depth 12 score cp 9559',
            pv=['8f8g']),'search')
        record={};m.play(game,plan,Referee(),engines,record,lambda:None)
        self.assertIn('reported_depth_below_requested',record['records'][0]['diagnostics'])
        self.assertEqual(record['records'][0]['analysis']['depth'],12)
        self.assertEqual(record['records'][0]['move'],'8f8g')
        engines['baseline'].choose_move=lambda *args:('8f8g',dict(depth=12,
            score_type='cp',score='9559',raw='info',pv=['other']),'search')
        record={};m.play(game,plan,Referee(),engines,record,lambda:None)
        self.assertIn('reported_pv_differs_from_bestmove',record['records'][0]['diagnostics'])

    def test_plan_timeout_is_used_for_each_player(self):
        plan=self.plan();plan['settings']['timeout']=300
        engines={v:Engine(v) for v in ('baseline','candidate')}
        for game in plan['games']:
            player='candidate' if game['candidate_color']=='white' else 'baseline'
            with patch.object(engines[player], 'choose_move', wraps=engines[player].choose_move) as choose:
                m.play(game,plan,Referee(),engines,{},lambda:None)
                self.assertEqual(choose.call_args.args[1:], (15,300))

    def test_run_resume_and_failure_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);plan=self.plan();m.seal(output/'plan.json',plan)
            with patch.object(m,'output_path',side_effect=lambda p:Path(p)),patch.object(m,'load',return_value=plan),patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                report=m.run(output);m.run(output)
            self.assertEqual(len(Engine.calls),2)
            self.assertEqual(report['completed_pairs'],1)
            self.assertEqual(report['candidate']['wins'],1)
            self.assertEqual(report['candidate']['losses'],1)
            self.assertEqual(report['candidate']['errors'],0)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);plan=self.plan();m.seal(output/'plan.json',plan);Engine.failure=TimeoutError('timeout')
            with patch.object(m,'output_path',side_effect=lambda p:Path(p)),patch.object(m,'load',return_value=plan),patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                with self.assertRaises(TimeoutError):m.run(output)
                with self.assertRaisesRegex(ValueError,'Failed game'):m.run(output)
            record=m.unseal(m.game_path(output,plan['games'][0]))
            self.assertEqual(record['status'],'failed')
            self.assertEqual(record['engines']['baseline']['transcript'],['info searching'])
            self.assertTrue(m.game_path(output,plan['games'][0]).with_suffix('.partial.json').exists())
            report=m.unseal(output/'report.json')
            self.assertEqual(report['candidate']['errors'],1)
            self.assertEqual(report['candidate']['losses'],0)
            self.assertEqual(report['incomplete_pairs'],1)
    def test_interrupt_persists_and_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);plan=self.plan();m.seal(output/'plan.json',plan);Engine.failure=KeyboardInterrupt()
            with patch.object(m,'output_path',side_effect=lambda p:Path(p)),patch.object(m,'load',return_value=plan),patch.object(m,'Probe',Referee),patch.object(m,'RecordedEngine',Engine):
                with self.assertRaises(KeyboardInterrupt):m.run(output)
                with self.assertRaisesRegex(ValueError,'Failed game'):m.run(output)
            self.assertEqual(m.unseal(m.game_path(output,plan['games'][0]))['failure']['type'],'KeyboardInterrupt')
    def test_prepare_freezes_eight_and_rejects_old_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'starts.json';output=root/'prepared'
            rows=[dict(id=str(i),moves=[str(i)]) for i in range(8)]
            m.write_json(config,dict(schema='rakuyou-hybrid-match-starts-v1',starts=rows))
            class StartsReferee(Referee):
                def replay(self,moves):
                    state=super().replay(moves)
                    state['positions'][-1]['sfen']='position'+moves[-1]+' b - 13'
                    return state
            with patch.object(m,'output_path',side_effect=lambda p:Path(p)),patch.object(m.behavior,'inputs',return_value=([],{}, {},'')),patch.object(m,'load_dataset',return_value=({},dict(rows=[]))),patch.object(m,'referee_bindings',return_value={}),patch.object(m,'Probe',StartsReferee),patch.object(m,'dependencies',return_value={}),patch.object(m,'digest',return_value='sha'):
                plan=m.prepare(root/'source',output,config)
                self.assertEqual(len(plan['games']),16)
                self.assertEqual(len(plan['starts']),8)
                with self.assertRaises(FileExistsError):m.prepare(root/'source',output,config)
                with patch.object(m,'load_dataset',return_value=({},dict(rows=[dict(sfen='position0 b - 1')]))):
                    with self.assertRaisesRegex(ValueError,'historical'):m.prepare(root/'source',root/'rejected',config)

    def test_orphan_attempt_and_binding_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);plan=self.plan();m.seal(output/'plan.json',plan);(output/'games').mkdir()
            path=m.game_path(output,plan['games'][0]);m.write_json(path.with_suffix('.attempt.json'),dict(number=1,plan_sha256=m.digest(output/'plan.json')))
            with self.assertRaisesRegex(ValueError,'Incomplete game'):m.saved(output,plan)
            plan['schema']='rakuyou-hybrid-match-v1';plan['settings']=m.SETTINGS;plan['code_sha256']={};plan['inputs_sha256']={'changed':'sha'};plan['runtime_sha256']={}
            m.seal(output/'plan.json',plan)
            with patch.object(m,'output_path',side_effect=lambda p:Path(p)),patch.object(m,'dependencies',return_value={}),patch.object(m,'checked',side_effect=ValueError('SHA mismatch')):
                with self.assertRaisesRegex(ValueError,'SHA'):m.load(output)


if __name__=='__main__':unittest.main()
