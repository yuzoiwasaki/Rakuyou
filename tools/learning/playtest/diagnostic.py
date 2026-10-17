"""Two saved match roots, two engines, two depths; diagnostic only."""
import argparse
import json
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.refresh_teachers import RecordedEngine
from tools.learning.hybrid.data import checked, output_path, write_json
from tools.learning.hybrid.runner import exclusive, seal, unseal
from tools.learning.playtest import match

OUTPUT = ROOT/'results/learning-pilot/2026-10-17-hybrid-diagnostic-v1'
ROOTS = ((7, 79), (4, 88))
SETTINGS = dict(depths=[15, 20], timeout=300, threads=1, hash_mb=64,
                multipv=1, shin_yonenaga_gyoku=True, own_book=False,
                fresh_engine_per_search=True, max_searches=8)


def dependencies():
    return {**match.dependencies(), 'tools/learning/playtest/diagnostic.py': digest(Path(__file__))}


def prepare(output=OUTPUT):
    output = output_path(output)
    parent = match.load(match.OUTPUT)
    games = match.saved(match.OUTPUT, parent)
    roots = []
    bindings = {str(match.OUTPUT/'plan.json'): digest(match.OUTPUT/'plan.json')}
    probe = Probe(parent['referee'])
    try:
        for number, ply in ROOTS:
            game = games[number]
            if game['status'] != 'completed':
                raise ValueError('Incomplete source game')
            moves = game['moves'][:ply-1]
            if len(moves) != ply-1:
                raise ValueError('Missing source history')
            state = match.replay(probe, moves)
            if state['result'] != 'ongoing':
                raise ValueError('Terminal diagnostic root')
            roots.append(dict(id=f'game{number:02d}-ply{ply}', game=number,
                              ply=ply, moves=moves, root=state['positions'][-1]))
            path = match.game_path(match.OUTPUT, game['game'])
            bindings[str(path)] = digest(path)
    finally:
        probe.close()
    plan = dict(schema='rakuyou-match-diagnostic-v1', settings=SETTINGS,
                roots=roots, inputs_sha256=bindings, code_sha256=dependencies(),
                engines=parent['engines'], referee=parent['referee'])
    output.mkdir(parents=True, exist_ok=False)
    seal(output/'plan.json', plan)
    return plan


def load(output):
    plan = unseal(output/'plan.json')
    parent = match.load(match.OUTPUT)
    if (plan['schema'] != 'rakuyou-match-diagnostic-v1' or plan['settings'] != SETTINGS
            or plan['code_sha256'] != dependencies()
            or plan['engines'] != parent['engines'] or plan['referee'] != parent['referee']):
        raise ValueError('Diagnostic binding differs')
    for path, sha in plan['inputs_sha256'].items():
        checked(path, sha)
    return plan


def jobs(plan):
    return [(f"{r['id']}-{v}-d{d}", r, v, d) for r in plan['roots']
            for d in plan['settings']['depths'] for v in ('baseline', 'candidate')]


def diagnose(result, row, depth, probe):
    if result['stopped_early']:
        raise ValueError('Stopped search')
    move = result['bestmove']
    if move in ('resign', 'win'):
        if move == 'win' and not row['root']['can_declare']:
            raise ValueError('Invalid declaration')
        return ['special_terminal']
    match.replay(probe, row['moves']+[move])
    candidates = result['candidates']
    if len(candidates) != 1:
        raise ValueError('Missing single PV')
    c = candidates[0]
    if not 1 <= c['depth'] <= depth or c['score_type'] not in ('cp', 'mate'):
        raise ValueError('Invalid reported depth/score')
    int(c['score'])
    if not c['pv']:
        raise ValueError('Missing PV')
    match.replay(probe, row['moves']+c['pv'])
    flags = []
    if c['depth'] < depth: flags.append('reported_depth_below_requested')
    if c['pv'][0] != move: flags.append('reported_pv_differs_from_bestmove')
    if c['score_type'] == 'mate': flags.append('mate')
    if any(t in c['raw'].split() for t in ('lowerbound', 'upperbound')):
        flags.append('bounded_score')
    return flags


def saved(output, plan):
    records = {}
    binding = digest(output/'plan.json')
    for name, _, _, _ in jobs(plan):
        path = output/'searches'/f'{name}.json'
        marker = path.with_suffix('.attempt.json')
        expected = dict(id=name, plan_sha256=binding)
        if not marker.exists():
            if path.exists(): raise ValueError('Missing attempt marker')
            continue
        if json.loads(marker.read_text()) != expected:
            raise ValueError('Attempt binding differs')
        if not path.exists(): raise ValueError('Interrupted attempt blocks retry: '+name)
        record = unseal(path)
        if any(record.get(k) != v for k, v in expected.items()) or record['status'] not in ('success', 'failed'):
            raise ValueError('Saved record binding differs')
        records[name] = record
    return records


def summarize(output, plan, records):
    lines = ['Saved-match diagnostic; scores are side-to-move, not strength gains.',
             'search                                status   bestmove reported-depth score flags']
    for name, _, _, _ in jobs(plan):
        r = records.get(name)
        if r is None: continue
        a = r.get('analysis', {})
        c = next(iter(a.get('candidates', [])), {})
        lines.append(f"{name:37} {r['status']:8} {a.get('bestmove', '-'):8} "
                     f"{c.get('depth', '-')} {c.get('score_type', '')} {c.get('score', '-')} "
                     f"{r.get('flags', r.get('failure', ''))}")
    success = sum(r['status'] == 'success' for r in records.values())
    lines.append(f'Attempted {len(records)}/8; successful {success}/8. No learning or deployment.')
    seal(output/'report.json', dict(plan_sha256=digest(output/'plan.json'), records=records,
                                    attempted=len(records), successful=success))
    (output/'summary.txt').write_text('\n'.join(lines)+'\n')


def run(output=OUTPUT):
    output = output_path(output)
    plan = load(output)
    with exclusive(output/'run.lock'):
        records = saved(output, plan)
        (output/'searches').mkdir(exist_ok=True)
        probe = Probe(plan['referee'])
        try:
            for name, row, variant, depth in jobs(plan):
                if name in records: continue  # Finished failures are retained, never retried.
                state = match.replay(probe, row['moves'])
                if state['positions'][-1] != row['root'] or state['result'] != 'ongoing':
                    raise ValueError('Root identity differs')
                print(f'Search {len(records)+1}/8: {name}', flush=True)
                path = output/'searches'/f'{name}.json'
                identity = dict(id=name, plan_sha256=digest(output/'plan.json'))
                write_json(path.with_suffix('.attempt.json'), identity, exclusive=True)
                record = dict(**identity, status='failed')
                engine = None
                try:
                    engine = RecordedEngine.__new__(RecordedEngine)
                    engine.__init__(Path(plan['engines'][variant]))
                    if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript):
                        raise ValueError('Engine loading error')
                    record['analysis'] = engine.analyze(row['moves'], depth, SETTINGS['timeout'])
                    if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript):
                        raise ValueError('Engine search error')
                    record['flags'] = diagnose(record['analysis'], row, depth, probe)
                    record['status'] = 'success'
                except Exception as error:
                    record['failure'] = f'{type(error).__name__}: {error}'
                finally:
                    if engine is not None:
                        try: engine.close()
                        except Exception as error:
                            record.update(status='failed', failure=f'Close: {error}')
                        record['commands'] = getattr(engine, 'commands', [])
                        record['transcript'] = getattr(engine, 'transcript', [])
                    seal(path, record)
                    records[name] = record
                    summarize(output, plan, records)
        finally:
            probe.close()
            load(output)
        summarize(output, plan, records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
        print('Prepared two roots / eight searches; no searches performed.')
    else:
        run()
        print((OUTPUT/'summary.txt').read_text(), end='')


if __name__ == '__main__': main()
