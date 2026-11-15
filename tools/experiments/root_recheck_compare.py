#!/usr/bin/env python3
"""Branch-only bounded search diagnostic; no strength/adoption inference."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.analyze_positions import Engine, parse_info


class BudgetEngine(Engine):
    node_budget = None
    milliseconds = None

    def __init__(self, *args):
        self.trace = []
        super().__init__(*args)

    def _read_output(self):
        for line in self.process.stdout:
            line = line.rstrip('\n')
            info = parse_info(line) if line.startswith('info ') else None
            if info and 'lowerbound' not in line and 'upperbound' not in line:
                self.trace.append(info)
            self.lines.put(line)

    def send(self, command):
        if command.startswith('go depth '):
            if self.milliseconds is not None:
                command = f'go btime 0 wtime 0 byoyomi {self.milliseconds}'
            elif self.node_budget is not None:
                command = f'go nodes {self.node_budget}'
        super().send(command)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'bin/match')
    parser.add_argument('--candidate', type=Path, default=ROOT / 'bin/match-root-recheck')
    parser.add_argument('--nodes', type=int, default=500000)
    parser.add_argument('--positions', type=Path,
                        default=Path(__file__).with_name('root_recheck_positions.json'))
    parser.add_argument('--milliseconds', type=int,
                        help='Compare fixed-time searches only, with ByoyomiMargin=0')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.nodes < 1 or (args.milliseconds is not None
                                                and not 1 <= args.milliseconds <= 5000):
        parser.error('Use a new output and a positive node budget')
    fixture = args.positions
    doc = dict(settings=dict(depth=15, nodes=args.nodes, hash_mb=512, threads=1,
                             own_book=False, fresh_process=True, stop_seconds=10,
                             milliseconds=args.milliseconds, style='ShinON/support10/D10',
                             byoyomi_margin=0 if args.milliseconds else None),
               hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (args.baseline, args.candidate, fixture,
                                 ROOT / 'bin/params.bin', ROOT / 'bin/progress.bin',
                                 ROOT / 'bin/probability.bin')}, rows=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for position in json.loads(fixture.read_text())['positions']:
        for mode in (('time',) if args.milliseconds else ('depth', 'nodes')):
            order = [('baseline', args.baseline), ('candidate', args.candidate)]
            if len(doc['rows']) // (2 if args.milliseconds else 4) % 2:
                order.reverse()
            for name, executable in order:
                engine = BudgetEngine(executable, 1, 512, 1, True)
                try:
                    engine.node_budget = args.nodes if mode == 'nodes' else None
                    engine.milliseconds = args.milliseconds
                    if args.milliseconds:
                        engine.send('setoption name ByoyomiMargin value 0')
                    result = engine.analyze(position['moves'], 15, 25, stop_after=10)
                    if mode == 'nodes':
                        # Native node limits can overshoot. Compare only exact PV
                        # reports already emitted within the requested budget.
                        reports = [c for c in engine.trace
                                   if c['nodes'] is not None and c['nodes'] <= args.nodes]
                        result['within_budget'] = reports[-1] if reports else None
                        result['exact_reports_within_budget'] = reports
                    engine.send('legalmoves')
                    engine.send('isready')
                    legal = set()
                    while True:
                        line = engine.lines.get(timeout=10)
                        if line == 'readyok':
                            break
                        legal.update(line.split())
                    if result['bestmove'] not in legal:
                        raise ValueError(f'Illegal bestmove: {result["bestmove"]}')
                finally:
                    engine.close()
                row = dict(id=position['id'], mode=mode, engine=name, analysis=result)
                doc['rows'].append(row)
                args.output.write_text(json.dumps(doc, indent=2) + '\n')
                c = result['candidates'][0]
                print(position['id'], mode, name, result['bestmove'], c['score'],
                      c['depth'], c['nodes'], flush=True)
                if mode == 'nodes':
                    c = result['within_budget']
                    print('  within budget:', None if c is None else
                          (c['pv'][0], c['score'], c['depth'], c['nodes']), flush=True)


if __name__ == '__main__':
    main()
