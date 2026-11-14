"""Frozen two-game start-position review; no experimental correction."""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.analysis.paired_selfplay import UsiEngine
from tools.learning.data.prepare_learning_data import Probe, digest
from tools.learning.hybrid.data import write_json
from tools.learning.hybrid.runner import exclusive, seal, unseal
from tools.learning.playtest import match as m

CODE = Path(__file__).resolve().parent
OUT = ROOT / 'results/teatsui-startpos-pair-2026-11-14'
STARTS = CODE / 'starts.json'
ORIGIN = ROOT / 'results/thickness-dialogue/no-legal-moves-2026-11-01/fixed-engine'
OLD_MATCH_PLAN = ROOT / 'results/teatsui-vs-normal-2026-11-06/plan.json'
ADOPTED = ROOT / 'results/adopted-support-contact-2026-11-13'
TRIAL_ENGINE = ROOT / 'bin/teatsui-2026-11-13/release'
OLD_REFEREE = ROOT / 'results/teatsui-match-timed-2026-11-03/referee'
REFEREE = OUT / 'referee/match-referee'
ARMS = ('support10d10',)
ROLES = {'support10d10':dict(shin=True,support_bonus=10,contact_deficit_cp=10),
         'normal':dict(shin=False,support_bonus=0,contact_deficit_cp=0)}
SETTINGS = {**{k: v for k, v in m.SETTINGS.items() if k != 'shin_yonenaga_gyoku'},
            'timeout': 30, 'byoyomi_ms': 10000,
            'byoyomi_margin_ms': 100, 'depth_is_cap': True}
EXPECTED_ENGINE_SHA = '86680adf5f407ca33f3cb21ea66fa11bda150364c5a33ffee701bc3aa73f014f'
EXPECTED_REFEREE_SHA = '6da348eb57abae81c4912aefa8b99d2bbceb0ecd1b059609a9b842d823e00347'
DATA = ('params.bin', 'progress.bin', 'probability.bin', 'book.bin')
SELECTED_INDICES = (0, 1)
EXPECTED_ADOPTED_SHA = '2a7578002d985d5719016635c666df9e09fd3825369ded02350f2f50b3f30811'
TIME_RE = re.compile(r'\btime (\d+)')
NODES_RE = re.compile(r'\bnodes (\d+)')
NPS_RE = re.compile(r'\bnps (\d+)')


class RoleEngine(m.RecordedEngine):
    """Recorded USI engine with role options sent before the first isready."""
    def __init__(self, path):
        path = Path(path)
        self.role = path.parent.name
        role = ROLES[self.role]
        self.bonus = role['support_bonus']
        self.contact_cp = role['contact_deficit_cp']
        self.commands = []
        self.transcript = []
        self.capture_lock = threading.Lock()
        self.last_go_timing = None
        self._go_started = None
        self._go_transcript_offset = 0
        self.executable = path.resolve()
        self.shin_yonenaga_gyoku = role['shin']
        self.own_book = False
        self.lines = queue.Queue()
        environment = os.environ.copy()
        removed = sorted(name for name in environment if name.startswith('RAKUYOU_'))
        for name in removed: environment.pop(name, None)
        self.env_binding = {'removed': removed, 'experiment_variables_set': {}}
        self.process = subprocess.Popen([str(self.executable)],
                                        cwd=str(self.executable.parent),
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, bufsize=1,
                                        env=environment)
        threading.Thread(target=self._read_output, daemon=True).start()
        self.send('usi')
        self.wait_for('usiok', 10)
        for option in (f"setoption name ShinYonenagaGyoku value {str(role['shin']).lower()}",
                       'setoption name OwnBook value false',
                       'setoption name Threads value 1',
                       'setoption name USI_Hash value 64',
                       'setoption name USI_Ponder value false',
                       'setoption name BookMaxPly value 0',
                       'setoption name ByoyomiMargin value 100',
                       f"setoption name ExperimentalSupportChainBonus value {self.bonus}"):
            self.send(option)
        if self.role != 'normal':
            self.send(f'setoption name KingContactDeficitBonus value {self.contact_cp}')
        self.send('isready')
        self.wait_for('readyok', 30)
        expected_default = 0 if self.role == 'normal' else 10
        if not any(f'option name ExperimentalSupportChainBonus type spin default {expected_default} min 0 max 10' in line
                   for line in self.snapshot()['transcript']):
            raise ValueError('Experimental bonus option missing')
        verify_options(self.snapshot()['commands'], self.role)

    def send(self, command):
        if command.startswith('go depth '):
            command += ' btime 0 wtime 0 byoyomi 10000'
            self._go_started = time.monotonic()
            self._go_transcript_offset = len(self.snapshot()['transcript'])
        super().send(command)

    def choose_move(self, moves, depth, timeout):
        try:
            move, analysis, source = super().choose_move(moves, depth, timeout)
        except BaseException:
            self._save_go_timing()
            raise
        self._save_go_timing()
        if self.last_go_timing['usi_time_ms'] is not None:
            check_clock(self.last_go_timing)
        if analysis is not None:
            analysis = dict(analysis, go_timing=self.last_go_timing)
        return move, analysis, source

    def _save_go_timing(self):
        if self._go_started is None: return
        lines = self.snapshot()['transcript'][self._go_transcript_offset:]
        info = next((line for line in reversed(lines)
                     if line.startswith('info ') and TIME_RE.search(line)), None)
        def number(pattern):
            match = pattern.search(info) if info is not None else None
            return int(match.group(1)) if match else None
        self.last_go_timing = dict(external_elapsed_ms=round(
            (time.monotonic()-self._go_started)*1000), usi_time_ms=number(TIME_RE),
            usi_nodes=number(NODES_RE), usi_nps=number(NPS_RE))

    def snapshot(self):
        snapshot = super().snapshot()
        snapshot.update(role=getattr(self, 'role', None),
                        env=getattr(self, 'env_binding', None),
                        last_go_timing=getattr(self, 'last_go_timing', None))
        return snapshot


def verify_options(commands, role):
    shin = ROLES[role]['shin']
    bonus = ROLES[role]['support_bonus']
    ready = commands.index('isready')
    required = [f'setoption name ShinYonenagaGyoku value {str(shin).lower()}',
                f'setoption name ExperimentalSupportChainBonus value {bonus}',
                'setoption name Threads value 1', 'setoption name USI_Hash value 64',
                'setoption name OwnBook value false', 'setoption name USI_Ponder value false',
                'setoption name BookMaxPly value 0', 'setoption name ByoyomiMargin value 100']
    if role != 'normal': required.append('setoption name KingContactDeficitBonus value 10')
    if any(commands.count(option) != 1 or commands.index(option) >= ready for option in required):
        raise ValueError('Role options absent or after isready')


def check_clock(timing, require_info=False):
    external = timing['external_elapsed_ms']
    internal = timing['usi_time_ms']
    if internal is None:
        if require_info: raise ValueError('USI info time missing in timed preflight')
        return 'unavailable'
    if (external < 0 or internal < 0 or
            max(external, internal) >= 3000 and
            max(external, internal) > 3 * max(1, min(external, internal))):
        raise ValueError(f'USI/wall clock mismatch: {internal}ms vs {external}ms')
    return 'consistent'


def schedule(starts):
    expected=('startpos-shin-black','startpos-shin-white')
    if tuple(s['id'] for s in starts)!=expected:raise ValueError('Unexpected starts')
    return [dict(number=i+1,pair=i+1,start_id=start['id'],moves=start['moves'],candidate_color='black' if i==0 else 'white',contact_deficit_cp=10,support_bonus=10,candidate_role='support10d10',baseline_role='normal') for i,start in enumerate(starts)]


def validate_schedule(starts,games):
    if games!=schedule(starts):raise ValueError('Mismatched schedule')


def king_square(sfen, king):
    ranks = sfen.split()[0].split('/')
    found = []
    for rank, row in enumerate(ranks):
        file = 9
        for ch in row:
            if ch.isdigit(): file -= int(ch)
            elif ch == '+': continue
            else:
                if ch == king: found.append(f'{file}{chr(97+rank)}')
                file -= 1
    if len(found) != 1: raise ValueError('Missing or duplicate king')
    return found[0]


def validate_starts(probe):
    config=json.loads(STARTS.read_text())
    if config != {'schema':'rakuyou-startpos-pair-v1','starts':[{'id':'startpos-shin-black','moves':[]},{'id':'startpos-shin-white','moves':[]}]}:
        raise ValueError('Expected two empty initial histories')
    state=m.replay(probe,[]);root=state['positions'][-1]
    if state['result']!='ongoing' or len(state['positions'])!=1 or root['side']!='black':
        raise ValueError('Invalid initial position')
    starts=[dict(row,sfen=root['sfen']) for row in config['starts']]
    schedule(starts)
    return starts


def frozen_inputs():
    old = unseal(OLD_MATCH_PLAN)
    original239 = old['bindings']
    if len(original239) != 239:
        raise ValueError('Original frozen input count changed')
    for path, expected in original239.items():
        if digest(path) != expected:
            raise ValueError('Original frozen input changed: ' + path)
    installed=json.loads((ADOPTED/'installation.json').read_text())
    if installed['binary_sha256']!=digest(TRIAL_ENGINE):raise ValueError('Adopted binary identity changed')
    return original239


def bindings():
    files = [Path(__file__), CODE/'test_match.py', STARTS, ORIGIN, TRIAL_ENGINE, OLD_MATCH_PLAN,
             ADOPTED/'installation.json', OLD_REFEREE/'match-referee', OLD_REFEREE/'build.json',
             REFEREE, OUT/'referee/build.json', ROOT/'bin/release']
    files += list((ROOT/'tools').rglob('*.py'))
    files += list((ROOT/'src').glob('*.cc')) + list((ROOT/'src').glob('*.h'))
    files += [ROOT/'bin'/name for name in DATA]
    for role in ROLES:
        files += [OUT/'runtime'/role/'release', OUT/'runtime'/role/'shin-yonenaga-book-v1.txt']
        files += [OUT/'runtime'/role/name for name in DATA]
    return {str(path): digest(path) for path in files}


def load(output=OUT):
    if Path(output).resolve() != OUT: raise ValueError('Wrong output directory')
    plan = unseal(OUT/'plan.json')
    if (plan['schema'] != 'rakuyou-startpos-pair-v1' or plan['settings'] != SETTINGS
            or plan['roles'] != ROLES or plan['selected_config_indices'] != list(SELECTED_INDICES)
            or plan['games'] != schedule(plan['starts']) or plan['bindings'] != bindings()
            or plan['frozen239'] != frozen_inputs()
            or plan['referee'] != str(REFEREE)
            or plan['engines'] != {r: str(OUT/'runtime'/r/'release') for r in ROLES}):
        raise ValueError('Frozen plan, code, or inputs changed')
    return plan


def prepare():
    if (OUT/'plan.json').exists() or (OUT/'preflight.attempt.json').exists():
        raise ValueError('Preparation already started; do not overwrite')
    if (digest(ORIGIN) != EXPECTED_ENGINE_SHA or digest(TRIAL_ENGINE) != EXPECTED_ADOPTED_SHA
            or digest(OLD_REFEREE/'match-referee') != EXPECTED_REFEREE_SHA):
        raise ValueError('Unexpected engine or referee binary')
    original239 = frozen_inputs()
    (OUT/'referee').mkdir(exist_ok=False)
    shutil.copy2(OLD_REFEREE/'match-referee', REFEREE)
    shutil.copy2(OLD_REFEREE/'build.json', OUT/'referee/build.json')
    for role in ROLES:
        directory = OUT/'runtime'/role
        directory.mkdir(parents=True, exist_ok=False)
        shutil.copy2(ORIGIN if role == 'normal' else TRIAL_ENGINE, directory/'release')
        for name in DATA: (directory/name).symlink_to(ROOT/'bin'/name)
        shutil.copy2(ROOT/'books/shin-yonenaga-book-v1.txt', directory/'shin-yonenaga-book-v1.txt')
    probe = Probe(REFEREE)
    try: starts = validate_starts(probe)
    finally: probe.close()
    plan = dict(schema='rakuyou-startpos-pair-v1', settings=SETTINGS,
                roles=ROLES, selected_config_indices=list(SELECTED_INDICES), starts=starts,
                games=schedule(starts), bindings=bindings(), referee=str(REFEREE),
                frozen239=original239,
                referee_origin=str(OLD_REFEREE),
                engines={r: str(OUT/'runtime'/r/'release') for r in ROLES},
                limitation='Two start-position games, adopted ShinON/support10/D10 versus fixed normal Rakuyou ShinOFF/support0/D0, colors reversed. Both books OFF; adopted native first-move rule retained (Black K4h or White K6b), every subsequent move searched. Depth15cap,10s,256 total plies. Screen obvious opening/style defects regardless of result; not upstream Gikou2 identity or strength proof. No tuning, retries or pooling.')
    seal(OUT/'plan.json', plan)
    load()
    print('Prepared 2 initial-position games; no searches or games run', flush=True)


def expected_opening(role,history):
    if not ROLES[role]['shin']:return None
    if len(history)==0:return '5i4h'
    if len(history)==1:return '5a6b'
    return None


def play(game,plan,probe,engines,record,persist):
    moves=list(game['moves']); state=m.replay(probe,moves)
    for engine in engines.values():engine.new_game()
    record.update(moves=moves,records=[],status='incomplete',result='unresolved',reason=None)
    persist()
    for ply in range(plan['settings']['max_additional_plies']):
        if state['result']!='ongoing':
            record.update(status='completed',result=state['result'],reason=state['reason']);return
        color=state['positions'][-1]['side']
        if color not in ('black','white'):raise ValueError('Unknown side to move')
        player='candidate' if color==game['candidate_color'] else 'baseline'
        move,analysis,source=engines[player].choose_move(moves,plan['settings']['depth'],plan['settings']['timeout'])
        if any('error' in line.lower() or 'failed' in line.lower() for line in engines[player].snapshot()['transcript']):raise ValueError('Engine search error')
        record['records'].append(dict(ply=len(moves)+1,additional_ply=ply+1,color=color,player=player,move=move,analysis=analysis,source=source))
        persist()
        if move=='resign':
            record.update(status='completed',result='white_win' if color=='black' else 'black_win',reason='resign');return
        if move=='win':
            if state['positions'][-1]['can_declare'] is not True:raise ValueError('Invalid declaration')
            record.update(status='completed',result=color+'_win',reason='declaration');return
        opening=expected_opening(game['candidate_role'] if player=='candidate' else 'normal',moves)
        if opening:
            if (source,move,analysis)!=('fixed_opening',opening,None):raise ValueError('Native first move mismatch')
            flags=['native_fixed_opening']
        else:
            if source!='search' or analysis is None:raise ValueError('Missing regular search analysis')
            flags=[]
            if analysis['score_type']=='mate':
                if not str(analysis['score']).lstrip('+-').isdigit() or int(analysis['score'])==0 or not 1<=analysis['depth']<=15:raise ValueError('Invalid mate search analysis')
                if analysis['depth']<15:flags.append('mate_early_depth')
            elif analysis['score_type']!='cp' or not 1<=analysis['depth']<=15:raise ValueError('Invalid search analysis depth/type')
            else:
                int(analysis['score'])
                # IterativeDeepening suppresses some final info lines. choose_move
                # returns only on bestmove; timeout raises and sends stop instead.
                # The last displayed depth/score/PV need not describe the final move.
                if analysis['depth']<15:flags.append('reported_depth_below_requested')
            if analysis.get('pv') and analysis['pv'][0]!=move:flags.append('reported_pv_differs_from_bestmove')
            if any(token in analysis['raw'].split() for token in ('lowerbound','upperbound')):flags.append('bounded_score')
        record['records'][-1]['diagnostics']=flags
        # Replay before accepting any move into the authoritative history.
        updated=m.replay(probe,moves+[move]); moves.append(move);state=updated
        record['moves']=list(moves);record['last_referee']=state;persist()
        if (ply+1)%20==0:print(f"  game {game['number']}: {ply+1} additional plies",flush=True)
    if state['result']!='ongoing':record.update(status='completed',result=state['result'],reason=state['reason'])
    else:record.update(status='completed',result='unresolved',reason='max_additional_plies')


def preflight():
    plan = load()
    if (OUT/'preflight.attempt.json').exists() or (OUT/'preflight.json').exists():
        raise ValueError('Preflight already attempted; no automatic retry')
    write_json(OUT/'preflight.attempt.json', {'plan_sha256': digest(OUT/'plan.json')}, exclusive=True)
    partial = dict(plan_sha256=digest(OUT/'plan.json'),
                   purpose='Eight depth3 connection probes including two native first moves, not match games',
                   status='incomplete', records=[])
    seal(OUT/'preflight.partial.json', partial)
    probe = None
    try:
        probe = Probe(REFEREE)
        roots = [('black', []), ('white', ['7g7f']),
                 ('black', ['5i4h','3c3d']), ('white', ['7g7f','5a6b','2g2f'])]
        for color, history in roots:
            state = m.replay(probe, history)
            if state['result'] != 'ongoing' or state['positions'][-1]['side'] != color:
                raise ValueError('Preflight side or root mismatch')
            for role in ROLES:
                item = dict(color=color, role=role, history=history)
                engine = RoleEngine.__new__(RoleEngine)
                close_error = None
                try:
                    engine.__init__(plan['engines'][role])
                    engine.new_game()
                    move, analysis, source = engine.choose_move(history, 3, 30)
                    snapshot = engine.snapshot()
                    item['go_timing'] = snapshot['last_go_timing']
                    opening = expected_opening(role,history)
                    if opening:
                        if (source,move,analysis)!=('fixed_opening',opening,None):
                            raise ValueError('Native first move mismatch')
                        item['clock_status']='native_opening_no_search'
                    else:
                        if source!='search' or move in ('resign','win') or analysis is None:
                            raise ValueError('Missing searched move')
                        item['clock_status']=check_clock(item['go_timing'],require_info=True)
                    item['source']=source
                    if any('error' in line.lower() or 'failed' in line.lower() for line in snapshot['transcript']):
                        raise ValueError('Engine output error')
                    if [c for c in snapshot['commands'] if c.startswith('go ')] != [
                            'go depth 3 btime 0 wtime 0 byoyomi 10000']:
                        raise ValueError('Preflight go command changed')
                    m.replay(probe, history+[move])
                    item.update(move=move, analysis=analysis, status='passed')
                except BaseException as error:
                    item.update(status='failed', failure=dict(type=type(error).__name__, message=str(error)))
                    raise
                finally:
                    if hasattr(engine, 'commands'): item['engine'] = engine.snapshot()
                    if hasattr(engine, 'process'):
                        try: engine.close()
                        except Exception as error:
                            item.update(status='failed', failure=dict(type=type(error).__name__, message=str(error)))
                            close_error = error
                    partial['records'].append(item)
                    seal(OUT/'preflight.partial.json', partial)
                    if close_error is not None: raise close_error
        partial['status'] = 'passed'
    except BaseException as error:
        partial.update(status='failed', failure=dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if probe is not None: probe.close()
        seal(OUT/'preflight.partial.json', partial)
    seal(OUT/'preflight.json', dict(plan_sha256=digest(OUT/'plan.json'),
                                    purpose=partial['purpose'], records=partial['records']))
    load()
    print('Preflight passed: six depth3 searches and two native first moves', flush=True)


def checked_preflight():
    marker = json.loads((OUT/'preflight.attempt.json').read_text())
    result = unseal(OUT/'preflight.json')
    binding = digest(OUT/'plan.json')
    if (marker != {'plan_sha256': binding} or result['plan_sha256'] != binding
            or len(result['records']) != 8
            or sum(r['source']=='fixed_opening' for r in result['records'])!=2
            or any(r['status']!='passed' or
                   (r['source']=='fixed_opening' and r['clock_status']!='native_opening_no_search') or
                   (r['source']=='search' and (r['clock_status']!='consistent' or r['go_timing']['usi_time_ms'] is None))
                   for r in result['records'])):
        raise ValueError('Preflight binding or count mismatch')


KEYS = ('wins', 'losses', 'draws', 'unresolved', 'errors', 'unrun')


def result_key(record):
    if record is None: return 'unrun'
    if record['status'] == 'failed': return 'errors'
    if record['result'] == 'unresolved': return 'unresolved'
    if record['result'] == 'draw': return 'draws'
    return 'wins' if record['result'] == record['game']['candidate_color']+'_win' else 'losses'


def score(key):
    return {'wins': 1.0, 'draws': 0.5, 'losses': 0.0}.get(key)


def counts_and_rate(keys):
    counts = Counter(keys)
    denominator = sum(counts[k] for k in ('wins', 'losses', 'draws'))
    return {**{k: counts[k] for k in KEYS},
            'score_rate': (counts['wins']+0.5*counts['draws'])/denominator if denominator else None,
            'scored_games': denominator}


def aggregate(output, plan, records):
    rows = [dict(game=g, status=result_key(records.get(g['number']))) for g in plan['games']]
    arms = {role: dict(total=counts_and_rate(r['status'] for r in rows if r['game']['candidate_role']==role),
        by_color={color: counts_and_rate(r['status'] for r in rows
            if r['game']['candidate_role']==role and r['game']['candidate_color']==color)
            for color in ('black','white')}) for role in ARMS}
    report=dict(schema='rakuyou-startpos-pair-report-v1',plan_sha256=digest(output/'plan.json'),settings=plan['settings'],requested_games=2,arms=arms,games=[records[n] for n in sorted(records)],limitation=plan['limitation'])
    seal(output/'report.json',report)
    summary=f"Completed {sum(result_key(r) not in ('unrun','errors') for r in records.values())}/2.\n"
    summary+=''.join(f"{role}: {arms[role]['total']}\n" for role in ARMS)
    summary+=plan['limitation']+'\n'
    temporary=output/'summary.txt.tmp';temporary.write_text(summary);temporary.replace(output/'summary.txt')
    return report

STOP_REQUESTED=False

def run_with_graceful_stop():
    import signal
    global STOP_REQUESTED
    STOP_REQUESTED=False
    def stop(signum,frame):
        global STOP_REQUESTED
        if STOP_REQUESTED: raise KeyboardInterrupt('Second interrupt; incomplete game preserved')
        STOP_REQUESTED=True
        print('Stop requested: finishing current game before stopping. A second Ctrl-C aborts and blocks automatic retry.',flush=True)
    previous=signal.signal(signal.SIGINT,stop)
    try: return run()
    finally: signal.signal(signal.SIGINT,previous)


def run():
    plan = load()
    checked_preflight()
    with exclusive(OUT/'run.lock'):
        plan = load()
        checked_preflight()
        records = m.saved(OUT, plan)
        if any(r['status'] == 'failed' for r in records.values()):
            raise ValueError('Failed game blocks continuation')
        report = aggregate(OUT, plan, records)
        if len(records) == 2: return report
        (OUT/'games').mkdir(exist_ok=True)
        probe = Probe(REFEREE)
        try:
            for game in plan['games']:
                if STOP_REQUESTED: break
                if game['number'] in records: continue
                print(f"Game {game['number']}/2: {game['start_id']} {game['candidate_role']} {game['candidate_color']}", flush=True)
                path = m.game_path(OUT, game)
                binding = digest(OUT/'plan.json')
                write_json(path.with_suffix('.attempt.json'), dict(number=game['number'], plan_sha256=binding), exclusive=True)
                record = dict(game=game, plan_sha256=binding, status='incomplete', result='unresolved',
                              reason=None, moves=list(game['moves']), records=[], engines={})
                engines = {}
                failure = None
                def persist():
                    record['engines'] = m.snapshots(engines)
                    seal(path.with_suffix('.partial.json'), record)
                try:
                    persist()
                    for name, role in (('candidate', game['candidate_role']), ('baseline', 'normal')):
                        engine = RoleEngine.__new__(RoleEngine)
                        engines[name] = engine
                        engine.__init__(plan['engines'][role])
                        persist()
                        if any('error' in line.lower() or 'failed' in line.lower()
                               for line in engine.snapshot()['transcript']):
                            raise ValueError('Engine loading error')
                    play(game, plan, probe, engines, record, persist)
                except BaseException as error:
                    failure = error
                    record.update(status='failed', result='error',
                                  failure=dict(type=type(error).__name__, message=str(error)))
                finally:
                    for engine in engines.values():
                        try: engine.close()
                        except Exception as error:
                            failure = error
                            record.update(status='failed', result='error',
                                          failure=dict(type=type(error).__name__, message=str(error)))
                    persist()
                    seal(path, record)
                    records[game['number']] = record
                    report = aggregate(OUT, plan, records)
                if failure is not None: raise failure
        finally:
            probe.close()
            load()
        return report


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) == 2 else ''
    if command == 'prepare': prepare()
    elif command == 'preflight': preflight()
    elif command == 'run':
        run_with_graceful_stop()
        print((OUT/'summary.txt').read_text(), end='')
    elif command == 'status':
        plan = load()
        checked_preflight()
        with exclusive(OUT/'run.lock'):
            aggregate(OUT, plan, m.saved(OUT, plan))
        print((OUT/'summary.txt').read_text(), end='')
    else: raise SystemExit('Usage: match.py prepare|preflight|run|status')
