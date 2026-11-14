"""Read-only audit of the saved eight-game comparison; referee only, no search."""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.learning.data.prepare_learning_data import Probe, digest
from tools.learning.hybrid.runner import unseal
from tools.learning.playtest import match as shared

CODE = Path(__file__).resolve().parent
OUT = ROOT/'results/teatsui-rank-counter-match-2026-11-14'
spec = importlib.util.spec_from_file_location('frozen_match', CODE/'match.py')
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)
plan = frozen.load()
frozen.checked_preflight()
saved = shared.saved(OUT, plan)
report = unseal(OUT/'report.json')
assert len(saved) == 8 and report['games'] == [saved[n] for n in sorted(saved)]
assert report['plan_sha256'] == digest(OUT/'plan.json')

games = []
clock = Counter()
diagnostics = Counter()
probe = Probe(Path(plan['referee']))
try:
    for number, record in sorted(saved.items()):
        game = plan['games'][number-1]
        assert record['game'] == game and record['status'] == 'completed'
        assert record == unseal(OUT/'games'/f'{number:02d}.partial.json')
        state = shared.replay(probe, record['moves'])
        assert state == record['last_referee']
        assert record['moves'][:12] == game['moves']
        history = list(game['moves'])
        for i, row in enumerate(record['records']):
            assert row['ply'] == len(history)+1 and row['additional_ply'] == i+1
            assert row['color'] == ('black' if len(history)%2 == 0 else 'white')
            assert row['player'] == ('candidate' if row['color'] == game['candidate_color'] else 'baseline')
            assert row['source'] == 'search'
            diagnostics.update(row.get('diagnostics', []))
            if row['move'] in ('resign', 'win'):
                assert i == len(record['records'])-1
            else:
                history.append(row['move'])
            timing = row['analysis']['go_timing']
            assert timing['usi_time_ms'] is not None and timing['usi_nodes'] is not None and timing['usi_nps'] is not None
            assert 0 <= timing['external_elapsed_ms'] < 30000
            assert frozen.check_clock(timing, require_info=True) == 'consistent'
            clock['timed_go'] += 1
            clock['max_wall_ms'] = max(clock['max_wall_ms'], timing['external_elapsed_ms'])
            clock['max_usi_ms'] = max(clock['max_usi_ms'], timing['usi_time_ms'])
        assert history == record['moves']
        final = record['records'][-1]
        if final['move'] == 'resign':
            assert record['reason'] == 'resign' and state['result'] == 'ongoing'
            assert record['result'] == ('white_win' if final['color'] == 'black' else 'black_win')
        elif final['move'] == 'win':
            assert record['reason'] == 'declaration' and state['positions'][-1]['can_declare']
            assert record['result'] == final['color']+'_win'
        elif record['result'] == 'unresolved':
            assert record['reason'] == 'max_additional_plies' and state['result'] == 'ongoing'
            assert len(record['records']) == plan['settings']['max_additional_plies']
        else:
            assert (record['result'], record['reason']) == (state['result'], state['reason'])
        if record['reason'] == 'repetition':
            assert state['positions'][-1]['occurrences'] == 4
        for player, role in (('candidate', game['candidate_role']), ('baseline', 'normal')):
            snapshot = record['engines'][player]
            commands, transcript = snapshot['commands'], snapshot['transcript']
            frozen.verify_options(commands, role)
            assert snapshot['role'] == role
            assert snapshot['env'][frozen.ENV_NAME] == str(frozen.ROLES[role]['rank_cp'])
            assert all(name.startswith('RAKUYOU_') for name in snapshot['env']['removed'])
            assert not any('error' in line.lower() or 'failed' in line.lower() for line in transcript)
            assert commands.count('usi') == commands.count('isready') == commands.count('usinewgame') == commands.count('quit') == 1
            assert 'stop' not in commands
            own = [r for r in record['records'] if r['player'] == player]
            assert [c for c in commands if c.startswith('go ')] == ['go depth 15 btime 0 wtime 0 byoyomi 10000']*len(own)
            assert [c for c in commands if c.startswith('position ')] == ['position startpos moves '+' '.join(record['moves'][:r['ply']-1]) for r in own]
            assert [line.split()[1] for line in transcript if line.startswith('bestmove ')] == [r['move'] for r in own]
        games.append(dict(number=number,pair=game['pair'],contact_deficit_cp=game['contact_deficit_cp'],
                          role=game['candidate_role'],support_bonus=game['support_bonus'],color=game['candidate_color'],result=record['result'],reason=record['reason'],
                          total_plies=len(history),terminal_referee_result=state['result'],
                          added_plies=len(record['records']),sha256=digest(OUT/'games'/f'{number:02d}.json')))
finally:
    probe.close()

arms = {role:dict(total=frozen.counts_and_rate(frozen.result_key(r) for r in saved.values() if r['game']['candidate_role']==role),
    by_color={color:frozen.counts_and_rate(frozen.result_key(r) for r in saved.values()
        if r['game']['candidate_role']==role and r['game']['candidate_color']==color)
        for color in ('black','white')}) for role in frozen.ARMS}
assert arms == report['arms']
contrasts={}
for name,(off,on) in {'rank_effect':('rank0','rank10')}.items():
    pairs=[]
    for pair in range(1,5):
        own={r['game']['candidate_role']:r for r in saved.values() if r['game']['pair']==pair}
        a,b=own[off],own[on]
        sa,sb=frozen.score(frozen.result_key(a)),frozen.score(frozen.result_key(b))
        delta=sb-sa if sa is not None and sb is not None else None
        assert delta == report['contrasts'][name]['pairs'][pair-1]['delta']
        divergence=next((dict(ply=x['ply'],color=x['color'],player=x['player'],off_move=x['move'],on_move=y['move'])
            for x,y in zip(a['records'],b['records']) if x['move']!=y['move']),None)
        pairs.append(dict(pair=pair,start_id=a['game']['start_id'],off_game=a['game']['number'],on_game=b['game']['number'],
            off=frozen.result_key(a),on=frozen.result_key(b),delta=delta,first_divergence=divergence))
    values=[p['delta'] for p in pairs if p['delta'] is not None]
    assert report['contrasts'][name]['comparable']==len(values)
    assert report['contrasts'][name]['mean_delta']==(sum(values)/len(values) if values else None)
    contrasts[name]=pairs
frozen.load()
out=dict(status='passed',searches_run=0,referee_only=True,plan_sha256=digest(OUT/'plan.json'),
    frozen_bindings_verified=len(plan['bindings']),report_sha256=digest(OUT/'report.json'),
    games=games,arms=arms,contrasts=contrasts,clock=dict(clock),diagnostics=dict(diagnostics))
with (OUT/'audit.json').open('x') as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('arms','diagnostics')},ensure_ascii=False,indent=2))
