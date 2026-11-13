"""Local checks for the eight-game schedule, role environment and stop rules."""
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
    names = ('black-shin-central-rook', 'black-shin-static-rook',
             'white-shin-fourth-rook', 'white-shin-third-rook')
    return [dict(id=name, moves=[name], sfen='sfen') for name in names]


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
        games=c.schedule(starts());self.assertEqual(len(games),8)
        for role in c.ARMS:
            own=[g for g in games if g['candidate_role']==role]
            self.assertEqual([g['candidate_color'] for g in own],['black']*2+['white']*2)
            self.assertEqual(sorted((g['number']-1)%2 for g in own),[0,0,1,1])
            self.assertTrue(all(g['support_bonus']==10 and g['contact_deficit_cp']==10 for g in own))
        bad=[dict(g) for g in games];bad[0]['rank_cp']=99
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
                                              c.ENV_NAME:'10'}):
                engine = c.RoleEngine(Path('/tmp')/role/'release')
                environment = popen.call_args.kwargs['env']
                self.assertEqual(environment[c.ENV_NAME], str(c.ROLES[role]['rank_cp']))
                self.assertTrue(all(name not in environment for name in c.REMOVED_ENVS))
                self.assertEqual(c.os.environ[c.ENV_NAME], '10')
                c.verify_options(engine.commands, role)
                engine.send('go depth 3')
                self.assertEqual(engine.commands[-1],
                                 'go depth 3 btime 0 wtime 0 byoyomi 10000')

    def test_clock_mismatch_detection(self):
        self.assertEqual(c.check_clock(dict(external_elapsed_ms=50,usi_time_ms=2)), 'consistent')
        self.assertEqual(c.check_clock(dict(external_elapsed_ms=4000,usi_time_ms=3500)), 'consistent')
        with self.assertRaisesRegex(ValueError, 'clock mismatch'):
            c.check_clock(dict(external_elapsed_ms=44000,usi_time_ms=515543))
        with self.assertRaisesRegex(ValueError, 'missing'):
            c.check_clock(dict(external_elapsed_ms=50,usi_time_ms=None), require_info=True)

    def test_aggregate_paired_denominator_and_unresolved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('plan')
            games=c.schedule(starts());plan=dict(games=games,starts=starts(),settings=c.SETTINGS,limitation='known')
            records={g['number']:dict(game=g,status='completed',result=g['candidate_color']+'_win' if g['candidate_role']=='rank10' else 'draw') for g in games}
            report=c.aggregate(output,plan,records)
            self.assertEqual(report['contrasts']['rank_effect']['mean_delta'],.5)
            records[1]['result']='unresolved';report=c.aggregate(output,plan,records)
            self.assertEqual(report['contrasts']['rank_effect']['comparable'],3)
            self.assertEqual(report['arms']['rank0']['total']['scored_games'],3)

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
                    patch.object(c,'RoleEngine',FakeEngine),patch.object(c.m,'play',side_effect=play):
                report = c.run()
                self.assertEqual(len(FakeEngine.instances),16)
                self.assertEqual(report['contrasts']['rank_effect']['comparable'],4)
                c.run()
                self.assertEqual(len(FakeEngine.instances),16)
                self.assertTrue(all(engine.closed for engine in FakeEngine.instances))
                self.assertTrue((output/'games/01.attempt.json').exists())
                self.assertTrue((output/'games/01.partial.json').exists())
            bad = c.m.unseal(output/'games/02.json')
            bad.update(status='failed',result='error')
            c.seal(output/'games/02.json',bad)
            with patch.object(c,'OUT',output),patch.object(c,'load',return_value=plan), \
                    patch.object(c,'checked_preflight'),patch.object(c,'RoleEngine',FakeEngine):
                with self.assertRaisesRegex(ValueError,'Failed game'): c.run()
                self.assertEqual(len(FakeEngine.instances),16)

    def test_graceful_stop_finishes_current_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);(output/'plan.json').write_text('plan')
            plan=dict(games=c.schedule(starts()),starts=starts(),settings=c.SETTINGS,engines={r:str(output/r/'release') for r in c.ROLES},referee='fake',limitation='known')
            def play(game,plan,probe,engines,record,persist):
                c.STOP_REQUESTED=True
                record.update(status='completed',result='draw',reason='test');persist()
            try:
                with patch.object(c,'OUT',output),patch.object(c,'load',return_value=plan),patch.object(c,'checked_preflight'),patch.object(c,'Probe',FakeProbe),patch.object(c,'RoleEngine',FakeEngine),patch.object(c.m,'play',side_effect=play):
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
