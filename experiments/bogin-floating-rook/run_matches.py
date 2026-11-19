#!/usr/bin/env python3
"""Ten controlled slots; checkpoints resume moves with fresh search tables."""
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
    for arm in ('baseline', 'candidate'):
        games = [g for g in data['games'] if g['arm'] == arm]
        wins = sum(g.get('winner') == 'shin' for g in games)
        losses = sum(g.get('winner') == 'normal' for g in games)
        print(arm, dict(statuses=dict(Counter(g['status'] for g in games)),
                        wins=wins, losses=losses,
                        resolved_score=wins / (wins + losses) if wins + losses else None), flush=True)


def run(output, smoke):
    for name in list(os.environ):
        if name.startswith('RAKUYOU'):
            del os.environ[name]
    config = dict(depth=1 if smoke else 15, byoyomi_ms=100 if smoke else 10000,
                  threads=1, hash_mb=64 if smoke else 512, book_max_ply=32,
                  added_plies=2 if smoke else 256, smoke=smoke,
                  black='ShinON/support10/D10', white='normalOFF/support0/D0',
                  normal_book=False)
    executable = ROOT / 'bin/match'
    inputs = [executable] + [ROOT / 'bin' / f for f in
                             ('params.bin', 'progress.bin', 'probability.bin')]
    inputs += [Path(__file__), Path(__file__).with_name('prepare.py'),
               Path(__file__).with_name('entries.json'), Path(__file__).with_name('starts.json'),
               ROOT / 'tools/analysis/paired_selfplay.py',
               ROOT / 'tools/books/build_operational_shin_book.py',
               ROOT / 'books/shin-yonenaga-book.json']
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    snapshot = output.with_suffix('.books')
    if output.exists():
        data = json.loads(output.read_text())
        if data['config'] != config or data['input_sha256'] != hashes:
            raise ValueError('Inputs/settings changed; use a different --output, do not mix runs')
        for arm, checksum in data['book_sha256'].items():
            if digest(snapshot / f'{arm}.txt') != checksum:
                raise ValueError('Frozen book changed')
    else:
        prepare_books()
        snapshot.mkdir(parents=True, exist_ok=False)
        for arm in ('baseline', 'candidate'):
            content = (ROOT / f'results/bogin-floating-rook/{arm}-book.txt').read_bytes()
            (snapshot / f'{arm}.txt').write_bytes(content)
        starts = json.loads(Path(__file__).with_name('starts.json').read_text())
        games = []
        for i, start in enumerate(starts['starts']):
            for arm in (('baseline', 'candidate') if i % 2 == 0 else ('candidate', 'baseline')):
                games.append(dict(id=f"{start['id']}-{arm}", arm=arm, start=start,
                                  moves=start['moves'].copy(), records=[], status='pending',
                                  winner=None, resumes=0))
        data = dict(config=config, input_sha256=hashes, description=starts['description'],
                    book_sha256={a: digest(snapshot / f'{a}.txt') for a in ('baseline', 'candidate')},
                    games=games, resume_policy='Continue saved moves with fresh engines; search tables reset. No automatic error retries.')
        save(output, data)
    for index, game in enumerate(data['games'], 1):
        if game['status'] in ('completed', 'unresolved'):
            continue
        if game['status'] == 'error':
            raise ValueError(f"{game['id']} has an error; inspect it before retrying")
        if game['status'] == 'running':
            game['resumes'] += 1
            print('Resuming saved moves with fresh search tables:', game['id'], flush=True)
        print(f"[{index}/10] {game['id']} starting at ply {len(game['moves'])}", flush=True)
        engines = []
        started = time.monotonic()
        game['status'] = 'running'
        save(output, data)
        try:
            for shin in (True, False):
                e = MatchEngine(executable, shin, shin, 1, config['hash_mb'], None, 32,
                                snapshot / f"{game['arm']}.txt" if shin else None)
                e.byoyomi = config['byoyomi_ms']
                e.new_game()
                engines.append(e)
            # Validate fixture history before spending time on its continuation.
            for n, move in enumerate(game['moves']):
                if move not in legal(engines[0], game['moves'][:n]):
                    raise ValueError(f'Illegal saved move at ply {n + 1}: {move}')
            limit = len(game['start']['moves']) + config['added_plies']
            while len(game['moves']) < limit:
                side = len(game['moves']) % 2
                player = 'shin' if side == 0 else 'normal'
                e = engines[side]
                move, analysis, source = e.choose_move(game['moves'], config['depth'], 40)
                record = dict(ply=len(game['moves']) + 1, player=player, move=move,
                              source=source, analysis=analysis)
                game['records'].append(record)
                if move in ('resign', 'win'):
                    game.update(status='completed', reason=move,
                                winner=player if move == 'win' else ('normal' if side == 0 else 'shin'))
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
        print(f"  {game['status']}: {game['reason']}; winner={game['winner']}; book={hits}", flush=True)
    print('Finished 10/10. Capped games remain unresolved; no strength/adoption claim.', flush=True)
    summary(data)
    print('Saved:', output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true', help='depth1, two added plies; separate output')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = (args.output or ROOT / ('results/floating-rook-smoke.json' if args.smoke
                                    else 'results/floating-rook-10games.json')).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run(output, args.smoke)


if __name__ == '__main__':
    main()
