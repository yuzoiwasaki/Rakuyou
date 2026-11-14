"""Local checks for the two-game schedule, role environment and stop rules."""
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('contact_match', Path(__file__).with_name('match.py'))
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def starts():
    return [dict(id=n,moves=[],sfen='sfen') for n in ('startpos-shin-black','startpos-shin-white')]


class FakeProbe:
    def __init__(self, path): self.closed = False
    def close(self): self.closed = True


class FakeEngine:
    instances = []
    def __init__(self, path):
        self.path = str(path)
        self.commands = ['usi', 'isready']
        self.transcript = []
        self.closed = False
        FakeEngine.instances.append(self)
    def snapshot(self): return dict(commands=self.commands[:], transcript=self.transcript[:])
    def new_game(self): self.commands.append('usinewgame')
    def close(self): self.closed = True


class ComparisonTest(unittest.TestCase):
    def setUp(self): FakeEngine.instances = []

    def test_schedule_roles_and_balance(self):
        games=c.schedule(starts());self.assertEqual(len(games),2)
        for role in c.ARMS:
            own=[g for g in games if g['candidate_role']==role]
            self.assertEqual([g['candidate_color'] for g in own],['black','white'])
            self.assertTrue(all(g['support_bonus']==10 and g['contact_deficit_cp']==10 for g in own))
        bad=[dict(g) for g in games];bad[0]['support_bonus']=99
        with self.assertRaises(ValueError):c.validate_schedule(starts(),bad)

    def test_role_process_env_and_options_before_ready(self):
        class FakeProcess:
            def __init__(self):
                self.stdin = io.StringIO()
                self.stdout = ['option name ExperimentalSupportChainBonus type spin default '+str(0 if role=='normal' else 10)+' min 0 max 10\n']
            def poll(self): return None
        class ImmediateThread:
            def __init__(self, target, daemon): self.target = target
            def start(self): self.target()
        for role in c.ROLES:
            process = FakeProcess()
            with patch.object(c.subprocess, 'Popen', return_value=process) as popen, \
                    patch.object(c.threading, 'Thread', ImmediateThread), \
                    patch.object(c.UsiEngine, 'wait_for', return_value='ready'), \
                    patch.dict(c.os.environ, {'RAKUYOU_NEAR_GS_CP':'10',
                                              'RAKUYOU_REAR_PARTICIPATION_CP':'10',
                                              'RAKUYOU_RANK_COMMITMENT_CP':'10'}):
                engine = c.RoleEngine(Path('/tmp')/role/'release')
                environment = popen.call_args.kwargs['env']
                self.assertFalse(any(name.startswith('RAKUYOU_') for name in environment))
                self.assertEqual(c.os.environ['RAKUYOU_RANK_COMMITMENT_CP'], '10')
                c.verify_options(engine.commands, role)
                engine.send('go depth 3')
                self.assertEqual(engine.commands[-1],
                                 'go depth 3 btime 0 wtime 0 byoyomi 10000')

    def test_native_opening_then_regular_search_for_both_colors(self):
        def replay(probe,moves):
            return dict(result='ongoing',positions=[dict(side='black' if len(moves)%2==0 else 'white')])
        for game in c.schedule(starts()):
            class Engine(FakeEngine):
                def choose_move(self,moves,depth,timeout):
                    role=Path(self.path).parent.name
                    opening=c.expected_opening(role,moves)
                    if opening:return opening,None,'fixed_opening'
                    return '7g7f',dict(score_type='cp',score='0',depth=15,pv=['7g7f'],raw='info score cp 0'),'search'
            engines={player:Engine('/tmp/'+role+'/release') for player,role in [('candidate','support10d10'),('baseline','normal')]}
            record={}
            with patch.object(c.m,'replay',side_effect=replay):
                c.play(game,dict(settings={**c.SETTINGS,'max_additional_plies':4}),None,engines,record,lambda:None)
            self.assertEqual(sum(r['source']=='fixed_opening' for r in record['records']),1)
            opening=record['records'][0 if game['candidate_color']=='black' else 1]
            self.assertEqual(opening['move'],'5i4h' if game['candidate_color']=='black' else '5a6b')
            self.assertTrue(all(r['source']=='search' for r in record['records'][2:]))

    def test_normal_cannot_use_fixed_opening(self):
        class Engine(FakeEngine):
            def choose_move(self,*args):return '5i4h',None,'fixed_opening'
        game=c.schedule(starts())[1]
        engines={p:Engine('/tmp/normal/release') for p in ('candidate','baseline')}
        with patch.object(c.m,'replay',return_value=dict(result='ongoing',positions=[dict(side='black')])):
            with self.assertRaisesRegex(ValueError,'Missing regular search'):
                c.play(game,dict(settings=c.SETTINGS),None,engines,{},lambda:None)

    def test_clock_mismatch_detection(self):
        self.assertEqual(c.check_clock(dict(external_elapsed_ms=50,usi_time_ms=2)), 'consistent')
        self.assertEqual(c.check_clock(dict(external_elapsed_ms=4000,usi_time_ms=3500)), 'consistent')
        with self.assertRaisesRegex(ValueError, 'clock mismatch'):
            c.check_clock(dict(external_elapsed_ms=44000,usi_time_ms=515543))
        with self.assertRaisesRegex(ValueError, 'missing'):
            c.check_clock(dict(external_elapsed_ms=50,usi_time_ms=None), require_info=True)

    def test_aggregate_excludes_unresolved_and_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('plan')
            games=c.schedule(starts());plan=dict(games=games,starts=starts(),settings=c.SETTINGS,limitation='known')
            records={g['number']:dict(game=g,status='completed',result='draw') for g in games}
            records[1]['result']='black_win';records[2]['result']='unresolved'
            r=c.aggregate(output,plan,records)['arms']['support10d10']['total']
            self.assertEqual(r['scored_games'],1);self.assertEqual(r['score_rate'],1)
            self.assertEqual(r['unresolved'],1)
            records[2].update(status='failed',result='error')
            r=c.aggregate(output,plan,records)['arms']['support10d10']['total']
            self.assertEqual(r['scored_games'],1);self.assertEqual(r['errors'],1)


    def test_run_fresh_roles_resume_and_failure_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            games = c.schedule(starts())
            plan = dict(games=games, starts=starts(), settings=c.SETTINGS,
                        engines={r:str(output/r/'release') for r in c.ROLES},
                        referee='fake', limitation='known starts')
            (output/'plan.json').write_text('plan')
            def play(game, plan, probe, engines, record, persist):
                self.assertEqual(engines['candidate'].path,
                                 plan['engines'][game['candidate_role']])
                self.assertEqual(engines['baseline'].path, plan['engines']['normal'])
                record.update(status='completed', result=game['candidate_color']+'_win', reason='resign')
                persist()
            with patch.object(c,'OUT',output),patch.object(c,'load',return_value=plan), \
                    patch.object(c,'checked_preflight'),patch.object(c,'Probe',FakeProbe), \
                    patch.object(c,'RoleEngine',FakeEngine),patch.object(c,'play',side_effect=play):
                report = c.run()
                self.assertEqual(len(FakeEngine.instances),4)
                self.assertEqual(report['arms']['support10d10']['total']['scored_games'],2)
                c.run()
                self.assertEqual(len(FakeEngine.instances),4)
                self.assertTrue(all(engine.closed for engine in FakeEngine.instances))
                self.assertTrue((output/'games/01.attempt.json').exists())
                self.assertTrue((output/'games/01.partial.json').exists())
            bad = c.m.unseal(output/'games/02.json')
            bad.update(status='failed',result='error')
            c.seal(output/'games/02.json',bad)
            with patch.object(c,'OUT',output),patch.object(c,'load',return_value=plan), \
                    patch.object(c,'checked_preflight'),patch.object(c,'RoleEngine',FakeEngine):
                with self.assertRaisesRegex(ValueError,'Failed game'): c.run()
                self.assertEqual(len(FakeEngine.instances),4)

    def test_graceful_stop_finishes_current_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('plan')
            plan=dict(games=c.schedule(starts()),starts=starts(),settings=c.SETTINGS,engines={r:str(output/r/'release') for r in c.ROLES},referee='fake',limitation='known')
            def play(game,plan,probe,engines,record,persist):
                c.STOP_REQUESTED=True
                record.update(status='completed',result='draw',reason='test');persist()
            try:
                with patch.object(c,'OUT',output),patch.object(c,'load',return_value=plan),patch.object(c,'checked_preflight'),patch.object(c,'Probe',FakeProbe),patch.object(c,'RoleEngine',FakeEngine),patch.object(c,'play',side_effect=play):
                    report=c.run()
                    self.assertEqual(len(report['games']),1)
                    self.assertFalse((output/'games/02.attempt.json').exists())
            finally:c.STOP_REQUESTED=False

    def test_orphan_attempt_blocks_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            game = c.schedule(starts())[0]
            plan = dict(games=[game], starts=starts(), settings=c.SETTINGS,
                        engines={}, referee='fake', limitation='known starts')
            (output/'plan.json').write_text('plan')
            (output/'games').mkdir()
            c.write_json(output/'games/01.attempt.json',
                         dict(number=1,plan_sha256=c.digest(output/'plan.json')))
            with patch.object(c,'OUT',output),patch.object(c,'load',return_value=plan), \
                    patch.object(c,'checked_preflight'):
                with self.assertRaisesRegex(ValueError,'Incomplete game'): c.run()


if __name__ == '__main__': unittest.main()
