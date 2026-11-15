#!/usr/bin/env python3
"""Branch-only equal-time paired games; user runs the long batch."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.paired_selfplay import UsiEngine

STARTS = Path(__file__).with_name('root_recheck_match_starts.json')
MOVE = re.compile(r'(?:[1-9][a-i][1-9][a-i]\+?|[PLNSGBR]\*[1-9][a-i])')


class TimedEngine(UsiEngine):
    milliseconds = 2000

    def send(self, command):
        if command.startswith('go depth '):
            command = f'go btime 0 wtime 0 byoyomi {self.milliseconds}'
        super().send(command)


def position(engine, moves):
    engine.send('position startpos' + (' moves ' + ' '.join(moves) if moves else ''))
    engine.send('legalmoves')
    engine.send('d')
    legal, sfens = set(), []
    while True:
        line = engine.lines.get(timeout=10)
        if line.startswith('move: '):
            break
        words = line.split()
        if words and all(MOVE.fullmatch(w) for w in words):
            legal.update(words)
        if len(words) == 4 and '/' in words[0] and words[1] in ('b', 'w'):
            sfens.append(' '.join(words[:3]))
    if len(sfens) != 1:
        raise ValueError('Missing or ambiguous native SFEN')
    return sfens[0], legal


def bindings():
    paths = ['bin/match', 'bin/match-root-recheck', 'bin/params.bin',
             'bin/progress.bin', 'bin/probability.bin',
             'lib/libomp-x86_64/lib/libomp.dylib',
             'tools/analysis/paired_selfplay.py',
             'tools/experiments/root_recheck_match.py',
             'tools/experiments/root_recheck_match_starts.json']
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}


def save(doc, output):
    temp = output.with_suffix(output.suffix + '.tmp')
    temp.write_text(json.dumps(doc, indent=2) + '\n')
    temp.replace(output)


def play(g, settings, checkpoint):
    engines = []
    try:
        for name in (g['black'], g['white']):
            binary = ROOT / ('bin/match' if name == 'baseline' else 'bin/match-root-recheck')
            e = TimedEngine(binary, True, False, 1, 512, None, 0)
            engines.append(e)
            e.milliseconds = settings['milliseconds']
            e.send('setoption name ByoyomiMargin value 0')
            e.new_game()
        if g['status'] == 'interrupted':
            g['resumes'].append(dict(ply=len(g['moves']), search_state='fresh'))
        g['status'] = 'running'
        while True:
            ply = len(g['moves'])
            e = engines[ply % 2]
            sf, legal = position(e, g['moves'])
            if str(ply) in g['positions'] and g['positions'][str(ply)] != sf:
                raise ValueError('Saved position differs from native replay')
            g['positions'][str(ply)] = sf
            if not legal:
                g.update(status='completed', reason='no_legal_moves',
                         winner=g['white'] if ply % 2 == 0 else g['black'])
                break
            if Counter(g['positions'].values())[sf] >= 4:
                g.update(status='unresolved', reason='fourfold_unadjudicated')
                break
            if ply >= settings['max_plies']:
                g.update(status='unresolved', reason='max_plies')
                break
            if ply < len(g['prefix']):
                move, analysis, source, elapsed = g['prefix'][ply], None, 'fixed_start', 0
            else:
                start = time.monotonic()
                move, analysis, source = e.choose_move(g['moves'], 1, 30)
                elapsed = time.monotonic() - start
            g['records'].append(dict(ply=ply+1, player=g['black'] if ply%2 == 0 else g['white'],
                                     move=move, analysis=analysis, source=source,
                                     elapsed_seconds=elapsed))
            if move == 'resign':
                g.update(status='completed', reason='resign',
                         winner=g['white'] if ply%2 == 0 else g['black'])
                break
            if move == 'win':
                g.update(status='unresolved', reason='declaration_unverified')
                break
            if move not in legal:
                raise ValueError(f'Illegal move {move}')
            g['moves'].append(move)
            checkpoint()
            if len(g['moves']) % 10 == 0:
                print(g['id'], 'ply', len(g['moves']), flush=True)
    finally:
        for e in engines:
            e.close()
    checkpoint()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--resume', type=Path)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    if args.resume and args.preflight:
        parser.error('--resume uses saved conditions')
    output = (args.resume or args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(output.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.resume:
            doc = json.loads(output.read_text())
            if doc.get('experiment') != 'root-recheck-time-pairs-v1' or doc['bindings'] != bindings():
                raise SystemExit('Inputs changed or wrong batch; do not resume')
        else:
            if output.exists():
                raise SystemExit('Output exists; choose a new output')
            jobs = []
            for start in json.loads(STARTS.read_text())['positions']:
                for side in ('black', 'white'):
                    jobs.append(dict(id=start['id']+'-candidate-'+side,
                                     black='candidate' if side=='black' else 'baseline',
                                     white='candidate' if side=='white' else 'baseline',
                                     prefix=start['moves'], moves=[], positions={}, records=[],
                                     resumes=[], status='pending'))
            doc = dict(experiment='root-recheck-time-pairs-v1', bindings=bindings(),
                       settings=dict(milliseconds=20 if args.preflight else 2000,
                                     max_plies=16 if args.preflight else 256,
                                     preflight=args.preflight, both='ShinON/support10/D10',
                                     books=False, threads=1, hash_mb=512, byoyomi_margin=0), games=jobs)
        save(doc, output)
        for g in doc['games']:
            if g['status'] not in ('pending', 'interrupted', 'running'):
                continue
            if bindings() != doc['bindings']:
                raise SystemExit('Inputs changed during batch')
            print('Starting', g['id'], flush=True)
            if g['status'] == 'running':
                g['status'] = 'interrupted'
            try:
                play(g, doc['settings'], lambda: save(doc, output))
            except KeyboardInterrupt:
                g['status'] = 'interrupted'
                save(doc, output)
                print('Interrupted; resume with --resume', output)
                return
            except Exception as error:
                g.update(status='error', reason=str(error))
                save(doc, output)
                raise
            print(g['status'], g['reason'], g.get('winner'), flush=True)
        wins = Counter(g.get('winner') for g in doc['games'] if g['status']=='completed')
        statuses = Counter(g['status'] for g in doc['games'])
        print('Finished:', dict(statuses), 'resolved wins:', dict(wins))
        print('Saved:', output)


if __name__ == '__main__':
    main()
