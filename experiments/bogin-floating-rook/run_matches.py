#!/usr/bin/env python3
"""Known-start comparison or twenty start-position games, with checkpoints."""
import argparse
from collections import Counter
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.paired_selfplay import UsiEngine
from prepare import legal, main as prepare_books


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    data['updated_at'] = datetime.now().astimezone().isoformat()
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


class MatchEngine(UsiEngine):
    def send(self, command):
        if command.startswith('go depth '):
            command += f' btime 0 wtime 0 byoyomi {self.byoyomi}'
        super().send(command)


def summary(data):
    groups = ('black', 'white') if data['config'].get('startpos') else ('baseline', 'candidate')
    for arm in groups:
        games = [g for g in data['games'] if g.get('shin_color', g['arm']) == arm]
        wins = sum(g.get('winner') == 'shin' for g in games)
        losses = sum(g.get('winner') == 'normal' for g in games)
        print(arm, dict(statuses=dict(Counter(g['status'] for g in games)),
                        wins=wins, losses=losses,
                        resolved_score=wins / (wins + losses) if wins + losses else None,
                        trial_book_games=sum(bool(g.get('trial_book_hits')) for g in games)), flush=True)


def position_key(engine, moves):
    engine.send('position startpos' + (' moves ' + ' '.join(moves) if moves else ''))
    engine.send('d')
    key = None
    while True:
        line = engine.lines.get(timeout=10)
        words = line.split()
        if len(words) == 4 and '/' in words[0] and words[1] in ('b', 'w'):
            key = ' '.join(words[:3])
        if line.startswith('move: '):
            if key is None:
                raise ValueError('Missing native SFEN')
            return key


def run(output, smoke, startpos=False):
    for name in list(os.environ):
        if name.startswith('RAKUYOU'):
            del os.environ[name]
    config = dict(depth=1 if smoke else 15, byoyomi_ms=100 if smoke else 10000,
                  threads=1, hash_mb=64 if smoke else 512, book_max_ply=32,
                  added_plies=2 if smoke else 256, smoke=smoke,
                  shin='ShinON/support10/D10', normal='normalOFF/support0/D0',
                  normal_book=startpos, normal_book_max_ply=20, startpos=startpos)
    executable = ROOT / 'bin/match'
    inputs = [executable] + [ROOT / 'bin' / f for f in
                             ('params.bin', 'progress.bin', 'probability.bin')]
    inputs += [Path(__file__), Path(__file__).with_name('prepare.py'),
               Path(__file__).with_name('entries.json'), Path(__file__).with_name('starts.json'),
               ROOT / 'tools/analysis/paired_selfplay.py',
               ROOT / 'tools/books/build_operational_shin_book.py',
               ROOT / 'books/shin-yonenaga-book.json']
    if startpos:
        inputs.append(ROOT / 'bin/book.bin')
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    snapshot = output.with_suffix('.books')
    if output.exists():
        data = json.loads(output.read_text())
        if data['config'] != config or data['input_sha256'] != hashes:
            raise ValueError('Inputs/settings changed; use a different --output, do not mix runs')
        for arm, checksum in data['book_sha256'].items():
            if digest(snapshot / f'{arm}.txt') != checksum:
                raise ValueError('Frozen book changed')
        if startpos and digest(snapshot / 'normal.bin') != data['normal_book_sha256']:
            raise ValueError('Frozen normal book changed')
    else:
        prepare_books()
        snapshot.mkdir(parents=True, exist_ok=False)
        for arm in ('baseline', 'candidate'):
            content = (ROOT / f'results/bogin-floating-rook/{arm}-book.txt').read_bytes()
            (snapshot / f'{arm}.txt').write_bytes(content)
        if startpos:
            (snapshot / 'normal.bin').write_bytes((ROOT / 'bin/book.bin').read_bytes())
        starts = json.loads(Path(__file__).with_name('starts.json').read_text())
        games = []
        for i, start in enumerate(starts['starts']):
            for arm in (('baseline', 'candidate') if i % 2 == 0 else ('candidate', 'baseline')):
                games.append(dict(id=f"{start['id']}-{arm}", arm=arm, start=start,
                                  moves=start['moves'].copy(), records=[], status='pending',
                                  winner=None, resumes=0))
        if startpos:
            games = [dict(id=f"startpos-{i+1:02d}-{'black' if i%2==0 else 'white'}",
                          arm='candidate', shin_color='black' if i%2==0 else 'white',
                          start={'id':'startpos', 'moves':[]}, moves=[], records=[],
                          status='pending', winner=None, resumes=0) for i in range(20)]
            starts['description'] = ('Twenty start-position games, candidate Shin10/10 vs normal0/0; '
                'ten per color, normal book ON through20 with native random/default filters; '
                'Shin book ON through32, native first-move rule retained. '
                'Screen natural openings/style, not controlled strength proof. No pooling or automatic adoption.')
        data = dict(config=config, input_sha256=hashes, description=starts['description'],
                    book_sha256={a: digest(snapshot / f'{a}.txt') for a in ('baseline', 'candidate')},
                    games=games, resume_policy='Continue saved moves with fresh engines; search tables reset. No automatic error retries.')
        if startpos:
            data['normal_book_sha256'] = digest(snapshot / 'normal.bin')
        save(output, data)
    for index, game in enumerate(data['games'], 1):
        if game['status'] in ('completed', 'unresolved'):
            continue
        if game['status'] == 'error':
            raise ValueError(f"{game['id']} has an error; inspect it before retrying")
        if game['status'] == 'running':
            game['resumes'] += 1
            print('Resuming saved moves with fresh search tables:', game['id'], flush=True)
        print(f"[{index}/{len(data['games'])}] {game['id']} starting at ply {len(game['moves'])}", flush=True)
        engines = []
        started = time.monotonic()
        game['status'] = 'running'
        save(output, data)
        try:
            shin_side = 0 if game.get('shin_color', 'black') == 'black' else 1
            for side in (0, 1):
                shin = side == shin_side
                e = MatchEngine(executable, shin, shin or startpos, 1, config['hash_mb'],
                                snapshot / 'normal.bin' if startpos and not shin else None,
                                32 if shin else (20 if startpos else 32),
                                snapshot / f"{game['arm']}.txt" if shin else None)
                e.byoyomi = config['byoyomi_ms']
                e.new_game()
                engines.append(e)
            delta = json.loads(Path(__file__).with_name('entries.json').read_text())['entries']
            trial_keys = {position_key(engines[shin_side], e['moves']): e['id'] for e in delta}
            game.setdefault('trial_book_hits', [])
            # Validate fixture history before spending time on its continuation.
            for n, move in enumerate(game['moves']):
                if move not in legal(engines[0], game['moves'][:n]):
                    raise ValueError(f'Illegal saved move at ply {n + 1}: {move}')
            limit = len(game['start']['moves']) + config['added_plies']
            while len(game['moves']) < limit:
                side = len(game['moves']) % 2
                player = 'shin' if side == shin_side else 'normal'
                e = engines[side]
                move, analysis, source = e.choose_move(game['moves'], config['depth'], 40)
                record = dict(ply=len(game['moves']) + 1, player=player, move=move,
                              source=source, analysis=analysis)
                game['records'].append(record)
                if source == 'dedicated_book' and player == 'shin' and game['arm'] == 'candidate':
                    trial_id = trial_keys.get(position_key(e, game['moves']))
                    if trial_id is not None:
                        record['trial_entry'] = trial_id
                        game['trial_book_hits'].append({'ply':record['ply'], 'id':trial_id})
                if move in ('resign', 'win'):
                    game.update(status='completed', reason=move,
                                winner=player if move == 'win' else ('normal' if player == 'shin' else 'shin'))
                    break
                if move not in legal(e, game['moves']):
                    raise ValueError(f'Illegal engine move: {move}')
                game['moves'].append(move)
                save(output, data)
                if len(game['records']) % 20 == 0:
                    print(f"  ply {len(game['moves'])}, {time.monotonic() - started:.0f}s this session", flush=True)
            if game['status'] == 'running':
                game.update(status='unresolved', reason='max_plies')
        except KeyboardInterrupt:
            save(output, data)
            raise
        except Exception as error:
            game.update(status='error', error=str(error))
            save(output, data)
            raise
        finally:
            for e in engines:
                e.close()
        save(output, data)
        hits = [r['ply'] for r in game['records'] if r['source'] == 'dedicated_book']
        print(f"  {game['status']}: {game['reason']}; winner={game['winner']}; book={hits}; trial={game['trial_book_hits']}", flush=True)
    print(f"Finished {len(data['games'])}/{len(data['games'])}. Capped games remain unresolved; no strength/adoption claim.", flush=True)
    summary(data)
    print('Saved:', output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true', help='depth1, two added plies; separate output')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--startpos', action='store_true', help='candidate vs normal, startpos, ten games per color')
    args = parser.parse_args()
    name = 'floating-rook-startpos20' if args.startpos else 'floating-rook-10games'
    if args.smoke:
        name += '-smoke'
    output = (args.output or ROOT / f'results/{name}.json').resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(output, args.smoke, args.startpos)


if __name__ == '__main__':
    main()
