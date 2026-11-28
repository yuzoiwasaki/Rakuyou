#!/usr/bin/env python3
"""Compare root alternatives, continuation searches, and experimental pressure traces."""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.analyze_positions import Engine, parse_info


def depth_trace(binary, moves, forced=None):
    engine = Engine(binary, 1, 512, 1, True)
    levels, stopped = {}, False
    started = time.monotonic()
    try:
        engine.send('usinewgame')
        engine.send('position startpos moves ' + ' '.join(moves))
        engine.send('go depth 22' + (' searchmoves ' + forced if forced else ''))
        while True:
            elapsed = time.monotonic() - started
            if elapsed > 35 and not stopped:
                engine.send('stop')
                stopped = True
            if elapsed > 45:
                raise TimeoutError('Engine did not finish the bounded search')
            try:
                line = engine.lines.get(timeout=1)
            except queue.Empty:
                continue
            if line.startswith('info '):
                info = parse_info(line)
                if info and 'lowerbound' not in line and 'upperbound' not in line:
                    levels[info['depth']] = info
            if line.startswith('bestmove '):
                break
    finally:
        engine.close()
    return dict(stopped=stopped, levels=levels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--rollouts', type=Path, default=ROOT/'test/analysis/defense_horizon_positions.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--mode', choices=['roots', 'continuations', 'trace', 'free'], required=True)
    args = parser.parse_args()
    games = json.loads(args.rollouts.read_text())
    selected = [next(g for g in games if g['weight'] == w) for w in (0, 20)]
    start = selected[0]['start_moves']
    assert len(start) == 49 and selected[1]['start_moves'] == start
    assert all(len(g['moves']) >= 61 and g['moves'][:49] == start for g in selected)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    def save(row):
        rows.append(row)
        (args.output_dir / (args.mode + '.json')).write_text(json.dumps(rows, indent=2) + '\n')
        print(row.get('label', row.get('weight')), flush=True)

    if args.mode == 'roots':
        for move in ['8e8f', 'P*6d', '5b4c']:
            save(dict(label=move, analysis=depth_trace(args.baseline, start, move)))
    elif args.mode in ('continuations', 'free'):
        for game in selected:
            for ply in ([49] if args.mode == 'free' else [53, 57, 61]):
                engine = Engine(args.candidate if args.mode == 'free' else args.baseline, 1, 512, 1, True)
                try:
                    if args.mode == 'free':
                        engine.send('setoption name ExperimentalGuardExchangePenalty value ' + str(game['weight']))
                    analysis = engine.analyze(game['moves'][:ply],
                                              24 if args.mode == 'free' else 20, 60,
                                              stop_after=35 if args.mode == 'free' else 20)
                finally:
                    engine.close()
                save(dict(weight=game['weight'], after_ply=ply, analysis=analysis))
    else:
        positions = [(g, ply) for g in selected for ply in range(49, 62)]
        content = ''.join('moves ' + ' '.join(g['moves'][:ply]) + '\n' for g, ply in positions)
        modes = {}
        for mode, extra in [('approach', []), ('exchange', ['exchange'])]:
            result = subprocess.run([str(ROOT/'results/king-approach-tools/native-test'),
                                     str(ROOT/'bin/params.bin')] + extra,
                                    input=content, text=True, capture_output=True, check=True, timeout=60)
            parsed = [list(map(int, row.split())) for row in result.stdout.splitlines()]
            assert len(parsed) == len(positions) * 4
            modes[mode] = parsed[::4]
        for i, (game, ply) in enumerate(positions):
            a, b = modes['approach'][i], modes['exchange'][i]
            save(dict(weight=game['weight'], after_ply=ply,
                      white_static=a[3] * (1 if ply % 2 else -1),
                      approach_black=a[1], approach_white=a[2],
                      exchange_black=b[1], exchange_white=b[2]))


if __name__ == '__main__':
    main()
