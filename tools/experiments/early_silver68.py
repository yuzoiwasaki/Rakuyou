#!/usr/bin/env python3
"""Six bounded development games; this runner stays on the experiment branch."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.paired_selfplay import UsiEngine

BOOK = ROOT / 'books/shin-yonenaga-book-v1.txt'
MOVE = re.compile(r'(?:[1-9][a-i][1-9][a-i]\+?|[PLNSGBR]\*[1-9][a-i])\Z')


def timestamp():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def bindings():
    paths = ['bin/match', 'bin/params.bin', 'bin/progress.bin',
             'bin/probability.bin', 'bin/book.bin', str(BOOK.relative_to(ROOT)),
             str(Path(__file__).relative_to(ROOT)), 'tools/analysis/paired_selfplay.py']
    paths += [str(p.relative_to(ROOT)) for p in (ROOT / 'lib').rglob('*.dylib') if not p.is_symlink()]
    return {p: sha(ROOT / p) for p in paths}


def jobs():
    return [dict(id=f'{opening}-{arm}', opening=opening, arm=arm,
                 prefix=['5i4h', '3c3d', third, reply], moves=[], records=[],
                 positions={}, resumes=[], status='pending')
            for opening, reply in [('fourth', '8b4b'), ('static84', '8c8d'), ('static62', '7a6b')]
            for arm, third in [('baseline76', '7g7f'), ('trial68', '7i6h')]]


def summary(games):
    result = {}
    for arm in dict.fromkeys(g['arm'] for g in games):
        subset = [g for g in games if g['arm'] == arm]
        counts = Counter(g['status'] for g in subset)
        wins = sum(g.get('winner') == 'shin' for g in subset)
        losses = sum(g.get('winner') == 'normal' for g in subset)
        result[arm] = dict(statuses=dict(counts), wins=wins, losses=losses,
                           score_rate=wins / (wins + losses) if wins + losses else None)
    return result


def save(doc, output):
    doc['updated_at'] = timestamp()
    doc['summary'] = summary(doc['games'])
    temp = output.with_suffix('.tmp')
    temp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')
    temp.replace(output)


def position(engine, moves):
    """Use native SFEN and legal moves, without any search or Python board model."""
    engine.send('position startpos' + (' moves ' + ' '.join(moves) if moves else ''))
    engine.send('legalmoves')
    engine.send('d')
    lines = []
    deadline = time.monotonic() + 30
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('native position query timed out')
        line = engine.lines.get(timeout=remaining)
        if line.startswith('move: '):
            break
        lines.append(line)
    sfens = [line.split() for line in lines if len(line.split()) == 4
             and line.split()[1] in ('b', 'w') and '/' in line.split()[0]]
    if len(sfens) != 1:
        raise ValueError('missing native SFEN')
    # legalmoves prints one line, including a blank line for terminal positions.
    legal = set()
    for line in lines:
        words = line.split()
        if words and all(MOVE.fullmatch(w) for w in words):
            legal.update(words)
    return ' '.join(sfens[0][:3]), legal


def play(g, settings, checkpoint):
    engines = []
    try:
        for shin in (True, False):
            book = ROOT / g.get('shin_book', str(BOOK.relative_to(ROOT)))
            engines.append(UsiEngine(ROOT / 'bin/match', shin, True, 1, settings['hash'],
                                     ROOT / 'bin/book.bin', settings.get('shin_book_max_ply', 20) if shin else 20,
                                     book if shin else None,
                                     support=10 if shin else 0, contact=10 if shin else 0))
        for e in engines:
            e.new_game()
        if g['moves']:
            g['resumes'].append(dict(at=timestamp(), ply=len(g['moves']), hash_table='fresh'))
        g['status'] = 'running'
        checkpoint()
        while True:
            ply = len(g['moves'])
            side = ply % 2
            e = engines[side]
            sfen, legal = position(e, g['moves'])
            key = str(ply)
            if key in g['positions'] and g['positions'][key] != sfen:
                raise ValueError('saved position differs from native replay')
            g['positions'][key] = sfen
            if not legal:
                g.update(status='completed', winner='normal' if side == 0 else 'shin', reason='no_legal_moves')
                break
            if Counter(g['positions'].values())[sfen] >= 4:
                # Do not label this a draw: continuous-check responsibility is not adjudicated.
                g.update(status='unresolved', reason='fourfold_position_unadjudicated')
                break
            if ply >= settings['max_plies']:
                g.update(status='unresolved', reason='max_plies')
                break
            if ply < len(g['prefix']):
                move, analysis, source = g['prefix'][ply], None, 'fixed_start'
            else:
                move, analysis, source = e.choose_move(g['moves'], settings['depth'], 300)
            record = dict(ply=ply + 1, color='black' if side == 0 else 'white',
                          player='shin' if side == 0 else 'normal', move=move,
                          source=source, analysis=analysis)
            if move == 'resign':
                g['records'].append(record)
                g.update(status='completed', winner='normal' if side == 0 else 'shin', reason='resign')
                break
            if move == 'win':
                g['records'].append(record)
                g.update(status='unresolved', reason='declaration_unverified')
                break
            if move not in legal:
                raise ValueError(f'illegal move at ply {ply + 1}: {move}')
            g['moves'].append(move)
            g['records'].append(record)
            checkpoint()
            if len(g['moves']) % 10 == 0:
                print(f"  {g['id']}: {len(g['moves'])} plies", flush=True)
        checkpoint()
    finally:
        for e in engines:
            e.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--output', type=Path)
    choice.add_argument('--resume', type=Path)
    parser.add_argument('--preflight', action='store_true', help='depth3,8 total plies; never pool with full run')
    args = parser.parse_args()
    output = (args.output or args.resume).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    current = bindings()
    if args.resume:
        if args.preflight:
            parser.error('--resume uses the saved settings')
        doc = json.loads(output.read_text())
        if doc['bindings'] != current:
            parser.error('binary/data/book/runner changed; do not resume this batch')
    else:
        if output.exists():
            parser.error('output already exists; use --resume or a new filename')
        doc = dict(created_at=timestamp(), git_commit=subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), bindings=current,
            settings=dict(depth=3 if args.preflight else 15, hash=64 if args.preflight else 512,
                          max_plies=8 if args.preflight else 256, preflight=args.preflight,
                          threads=1, book_max_ply=20, black='ShinON/support10/D10',
                          white='ShinOFF/support0/D0', both_books=True),
            games=jobs(), errors=[])
    save(doc, output)
    print(f'Results: {output}', flush=True)
    for index, g in enumerate(doc['games'], 1):
        if g['status'] not in ('pending', 'running', 'interrupted'):
            continue
        print(f"Game {index}/6: {g['id']} ({len(g['moves'])} saved plies)", flush=True)
        try:
            if bindings() != doc['bindings']:
                raise ValueError('inputs changed during batch')
            play(g, doc['settings'], lambda: save(doc, output))
        except KeyboardInterrupt:
            g['status'] = 'interrupted'
            save(doc, output)
            print('Interrupted; saved moves can be continued with --resume (fresh search hash).')
            return
        except Exception as error:
            g.update(status='error', reason=str(error))
            doc['errors'].append(dict(at=timestamp(), game=g['id'], message=str(error)))
            save(doc, output)
            raise
        print(f"  {g['status']}: {g['reason']}; winner={g.get('winner', '-')}", flush=True)
    print('Finished 6-slot batch.', flush=True)
    print(json.dumps(doc['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
