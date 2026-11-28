#!/usr/bin/env python3
"""Bounded, book-free diagnostics for the experimental king-approach term."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.analyze_positions import Engine, parse_info
from tools.analysis.paired_selfplay import UsiEngine
from tools.books.build_operational_shin_book import MOVE


def snapshot(engine, moves):
    engine.send('position startpos moves ' + ' '.join(moves))
    engine.send('legalmoves')
    engine.send('d')
    legal, key = set(), None
    while True:
        line = engine.lines.get(timeout=15)
        words = line.split()
        if len(words) == 4 and '/' in words[0] and words[1] in ('b', 'w'):
            key = ' '.join(words[:3])
        if words and all(MOVE.fullmatch(w) for w in words):
            legal.update(words)
        if line.startswith('move: '):
            assert key is not None
            return legal, key


class TimedEngine(UsiEngine):
    def send(self, command):
        if command.startswith('go depth '):
            command = 'go btime 0 wtime 0 byoyomi 2000'
        super().send(command)


def rollout(binary, fixture, weight):
    engines = []
    moves, records = fixture['moves'].copy(), []
    result = dict(weight=weight, start_moves=moves.copy(), moves=moves,
                  records=records, reason='12-ply-cap', strength_claim=False)
    try:
        for shin in (False, True):
            e = TimedEngine(binary, shin, False, 1, 512, None, 44)
            engines.append(e)
            e.send(f'setoption name ExperimentalKingApproachPenalty value {weight if shin else 0}')
            e.send('setoption name ByoyomiMargin value 0')
            e.new_game()
        seen = {}
        for n in range(len(moves)+1):
            legal, key = snapshot(engines[0], moves[:n])
            if n < len(moves):
                assert moves[n] in legal
            seen[key] = seen.get(key, 0) + 1
        for _ in range(12):
            e = engines[len(moves) % 2]
            legal, _ = snapshot(e, moves)
            move, analysis, source = e.choose_move(moves, None, 30)
            records.append(dict(ply=len(moves)+1, move=move, analysis=analysis, source=source))
            if move in ('resign', 'win'):
                result['reason'] = move + '-not-adjudicated'
                break
            assert move in legal
            moves.append(move)
            _, key = snapshot(e, moves)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] >= 4:
                result['reason'] = 'fourfold-not-adjudicated'
                break
    finally:
        for e in engines:
            e.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['scan', 'fixed', 'baseline', 'speed', 'rollout', 'native-input'], required=True)
    parser.add_argument('--engine', type=Path, default=ROOT/'results/king-approach-experiment/runtime/bin/match')
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((ROOT/'test/analysis/king_approach_positions.json').read_text())
    fixtures = data['search']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == 'native-input':
        content = ''.join('moves ' + ' '.join(x['moves']) + '\n' for x in data['static'])
        args.output.write_text(content + (ROOT/'test/analysis/evaluation_positions.txt').read_text())
        return
    if args.mode == 'baseline' and args.baseline is None:
        parser.error('--baseline is required for baseline comparison')
    results = []
    if args.mode == 'rollout':
        for weight in [0, 20, 40]:
            r = rollout(args.engine.resolve(), fixtures[0], weight)
            results.append(r)
            args.output.write_text(json.dumps(results, indent=2)+'\n')
            print(weight, [(x['ply'], x['move']) for x in r['records']], flush=True)
        return
    for f in (fixtures[:1] if args.mode in ('fixed', 'speed') else fixtures):
        weights = ([0,20,20,0,0,20] if args.mode=='speed' else
                   [0,0] if args.mode=='baseline' else
                   [0,10,20,40] if f['id']=='defense50' else [0,20,40])
        previous = None
        for index, weight in enumerate(weights):
            binary = args.baseline if args.mode=='baseline' and index==0 else args.engine
            multipv = 3 if args.mode in ('scan','fixed') and f['id']=='defense50' else 1
            e = Engine(binary, 1, 512, multipv, True)
            try:
                if 'ExperimentalKingApproachPenalty' in e.option_names:
                    e.send(f'setoption name ExperimentalKingApproachPenalty value {weight}')
                else:
                    assert args.mode=='baseline' and index==0
                if args.mode=='speed':
                    e.send('usinewgame'); e.send('position startpos moves '+' '.join(f['moves']))
                    e.send('go nodes 1000000'); last = None
                    while True:
                        line = e.lines.get(timeout=30)
                        if line.startswith('info '):
                            last = parse_info(line) or last
                        if line.startswith('bestmove '):
                            break
                    a = dict(nodes=last['nodes'], time_ms=last['time_ms'])
                else:
                    depth = 12 if args.mode=='baseline' else 18 if args.mode=='fixed' else 19 if multipv==3 else 16
                    stop = (6 if multipv==3 else 3) if args.mode=='scan' else None
                    a = e.analyze(f['moves'], depth, 45, stop_after=stop, multipv=multipv)
                    if args.mode=='baseline':
                        c = a['candidates'][0]
                        stable = {k:c[k] for k in ('depth','score_type','score','pv')}
                        if previous is not None:
                            assert stable == previous, f['id']
                        previous = stable
            finally:
                e.close()
            results.append(dict(id=f['id'], weight=weight, analysis=a))
            args.output.write_text(json.dumps(results, indent=2)+'\n')
            print(f['id'], weight, a if args.mode=='speed' else
                  [(c['depth'], c['score'], c['pv'][0]) for c in a['candidates']], flush=True)


if __name__ == '__main__':
    main()
