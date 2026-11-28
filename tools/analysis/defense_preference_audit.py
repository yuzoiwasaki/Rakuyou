#!/usr/bin/env python3
"""Offline comparison only; defense includes formation; one equal-depth comparison, no confirmation search."""
import argparse
import json
from pathlib import Path
import queue
import sys
import time
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.analyze_positions import Engine, parse_info
from tools.analysis.king_approach_experiment import snapshot


def select(candidates, defense, attacks, eligible=True, threshold=50):
    """Use only complete, equal-depth cp scores. Unknown best-move roles stay unchanged."""
    if not candidates:
        return dict(selected=None, reason='no-complete-scores')
    if len({c['depth'] for c in candidates}) != 1 or any(
            c['score_type'] != 'cp' or 'lowerbound' in c.get('raw','')
            or 'upperbound' in c.get('raw','') for c in candidates):
        return dict(selected=None, reason='incomparable-scores')
    ranked = sorted(candidates, key=lambda c: -int(c['score']))
    best = ranked[0]
    result = dict(best=best['pv'][0], selected=best['pv'][0], reason='unchanged')
    if not eligible:
        result['reason'] = 'ineligible'
        return result
    if best['pv'][0] not in attacks:
        return result
    receiver = next((c for c in ranked if c['pv'][0] in defense), None)
    if receiver is None:
        return result
    result['gap'] = int(best['score'])-int(receiver['score'])
    if result['gap'] <= threshold:
        result.update(selected=receiver['pv'][0], reason='defense-within-threshold')
    return result


def analyze(binary, fixture, depth):
    pool = fixture['pool']
    engine = Engine(binary, 1, 512, len(pool), True)
    levels, stopped = {}, False
    started = time.monotonic()
    try:
        legal, _ = snapshot(engine, fixture['moves'])
        assert len(set(pool)) == len(pool) and set(pool) <= legal
        engine.send('usinewgame')
        engine.send('position startpos moves '+' '.join(fixture['moves']))
        engine.send('go depth '+str(depth)+' searchmoves '+' '.join(pool))
        while True:
            elapsed = time.monotonic()-started
            if elapsed > 55 and not stopped:
                engine.send('stop'); stopped = True
            if elapsed > 65:
                raise TimeoutError('bounded comparison did not finish')
            try:
                line = engine.lines.get(timeout=1)
            except queue.Empty:
                continue
            if line.startswith('info '):
                c = parse_info(line)
                if c and 'lowerbound' not in line and 'upperbound' not in line:
                    levels.setdefault(c['depth'], {})[c['multipv']] = c
            elif line.startswith('bestmove '):
                break
    finally:
        engine.close()
    completed = {}
    for d, rows in levels.items():
        if len(rows) != len(pool):
            continue
        candidates = sorted(rows.values(), key=lambda c: -int(c['score']) if c['score_type']=='cp' else 0)
        if {c['pv'][0] for c in candidates} != set(pool):
            continue
        completed[d] = dict(candidates=candidates,
            decision=select(candidates, fixture['direct_defense']+fixture['formation'],
                            fixture['attack'], fixture['eligible']))
    return dict(id=fixture['id'], requested_depth=depth, stopped=stopped,
                elapsed_seconds=time.monotonic()-started, levels=completed)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--fixtures',type=Path,default=ROOT/'test/analysis/defense_preference_positions.json')
    p.add_argument('--depth',type=int,default=20)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); results=[]
    for f in json.loads(args.fixtures.read_text()):
        r=analyze(args.engine,f,args.depth);results.append(r)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(results,indent=2)+'\n')
        for d,row in r['levels'].items():
            if d>=16:
                print(f['id'],d,[(c['pv'][0],c['score']) for c in row['candidates']],row['decision'],flush=True)


if __name__=='__main__': main()
