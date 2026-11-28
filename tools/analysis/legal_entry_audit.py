#!/usr/bin/env python3
"""Offline entry/capture diagnostic; no evaluation or search changes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.analyze_positions import Engine


def entries(fixtures):
    content = ''.join('moves '+' '.join(f['moves'])+'\n' for f in fixtures)
    run = subprocess.run([str(ROOT/'results/legal-entry-tools/native-test'), str(ROOT/'bin/params.bin')],
                         input=content, text=True, capture_output=True, check=True, timeout=60)
    output = [{} for _ in fixtures]
    for row in run.stdout.splitlines():
        index, move, see, check, distance, *captures = row.split()
        output[int(index)][move] = dict(see=int(see), check=bool(int(check)), distance=int(distance),
                                       captures={m:int(v) for m,v in (c.split(':') for c in captures)})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True, help='Frozen adopted evaluation engine')
    parser.add_argument('--fixtures', type=Path, default=ROOT/'test/analysis/legal_entry_positions.json')
    parser.add_argument('--depth', type=int, default=18)
    parser.add_argument('--mode', choices=['entries', 'parent-comparison'], default='entries')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text())
    native = entries(fixtures) if args.mode == 'entries' else None
    output = dict(depth=args.depth, engine=str(args.engine), fixtures=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def search(moves, restricted=None):
        e = Engine(args.engine, 1, 512, 1, True)
        try:
            a = e.analyze(moves, args.depth, 60, searchmoves=restricted)
        finally:
            e.close()
        assert not a['stopped_early']
        return a

    if args.mode == 'parent-comparison':
        for fixture in fixtures:
            for move in fixture.get('parent_alternatives', []):
                a = search(fixture['moves'][:-1], [move])
                output['fixtures'].append(dict(id=fixture['id'], move=move, analysis=a))
                args.output.write_text(json.dumps(output, indent=2)+'\n')
                print(move, a['candidates'][0]['score'], flush=True)
        return

    for fixture, entry_map in zip(fixtures, native):
        row = dict(id=fixture['id'], moves=fixture['moves'], entries=entry_map,
                   unrestricted_before=search(fixture['moves']), watched={})
        for move in fixture['watch']:
            if move not in entry_map:
                row['watched'][move] = dict(status='not-an-eligible-entry')
                continue
            response = dict(status='analyzed', unrestricted=search(fixture['moves']+[move]))
            captures = list(entry_map[move]['captures'])
            if captures:
                response['immediate_capture'] = search(fixture['moves']+[move], captures)
            row['watched'][move] = response
            print(fixture['id'], move, 'SEE', entry_map[move]['see'], 'captures', entry_map[move]['captures'],
                  [(k,v['candidates'][0]['score'],v['candidates'][0]['pv'][:5])
                   for k,v in response.items() if isinstance(v,dict)], flush=True)
        output['fixtures'].append(row)
        args.output.write_text(json.dumps(output, indent=2)+'\n')


if __name__ == '__main__':
    main()
