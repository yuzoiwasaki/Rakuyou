"""Fresh guarded-candidate games at the seven previously exposed book leaves."""
import argparse
from pathlib import Path
from tools.learning.constraints import guarded_behavior as behavior
from tools.learning.constraints import book_match as book
from tools.learning.playtest import match as rules
from tools.learning.playtest.match import (RecordedEngine, Probe, digest, checked,
    output_path, write_json, exclusive, seal, unseal, game_path, snapshots,
    play, saved, aggregate)

OUTPUT = behavior.ROOT/'results/learning-pilot/2026-10-24-guarded-book-match-v1'


def specification():
    parent = book.load(book.OUTPUT)
    candidate = behavior.load()
    records = behavior.previous.saved(behavior.OUTPUT, candidate)
    report = unseal(behavior.OUTPUT/'report.json')
    if (report['plan_sha256'] != digest(behavior.OUTPUT/'plan.json')
            or len(records) != 48 or report['completed_searches'] != 48
            or report['valid_regular_pairs'] != 24 or len(report['pairs']) != 24):
        raise ValueError('Expected complete guarded behavior comparison')
    inputs = {str(p):digest(p) for p in (book.OUTPUT/'plan.json', book.BOOK,
              behavior.OUTPUT/'plan.json', behavior.OUTPUT/'report.json')}
    for row, pair in zip(candidate['roots'], report['pairs']):
        if pair['root'] != row:
            raise ValueError('Behavior root mismatch')
        for variant in ('baseline', 'candidate'):
            record = records[row['id'], variant]
            if record != pair['results'][variant] or record['status'] != 'success' or record['diagnosis']['kind'] != 'regular':
                raise ValueError('Behavior record mismatch')
            path = behavior.previous.paths(behavior.OUTPUT, row, variant)
            for p in (path, path.with_suffix('.attempt.json')):
                inputs[str(p)] = digest(p)
    if candidate['engines']['baseline'] != parent['engines']['baseline']:
        raise ValueError('Baseline differs from previous book comparison')
    return dict(schema='guarded-book-match-v1',settings=parent['settings'],
                starts=parent['starts'],games=rules.games(parent['starts']),
                inputs_sha256=inputs,runtime_sha256=candidate['runtime_sha256'],
                code_sha256={**book.dependencies(),**candidate['code_sha256'],
                             str(Path(__file__).relative_to(behavior.ROOT)):digest(Path(__file__))},
                referee=parent['referee'],engines=candidate['engines'],
                selection='Same seven operational-book leaves; fresh games, fixed guarded candidate; no result-based selection.',
                limitation='Fourteen fresh fixed-depth guarded-candidate games on exposed book prefixes; not independent or equal-time strength proof. Max-ply endings unresolved.')


def prepare(output=OUTPUT):
    output = output_path(output)
    plan = specification()
    probe = Probe(plan['referee'])
    try:
        for row in plan['starts']:
            state = rules.replay(probe, row['moves'])
            if (state['result'] != 'ongoing' or state['positions'][-1]['sfen'] != row['sfen']
                    or any(p['occurrences'] > 1 for p in state['positions'])):
                raise ValueError('Start replay differs')
    finally:
        probe.close()
    output.mkdir(parents=True, exist_ok=False)
    seal(output/'plan.json', plan)
    return plan


def load(output=OUTPUT):
    output = output_path(output)
    plan = unseal(output/'plan.json')
    if plan != specification():
        raise ValueError('Frozen guarded match changed')
    return plan


def run(output=OUTPUT):
    output=output_path(output);load(output)
    with exclusive(output/'run.lock'):
        plan=load(output);records=saved(output,plan);report=aggregate(output,plan,records)
        if any(r['status']=='failed' for r in records.values()):raise ValueError('Failed game blocks automatic continuation/retry')
        if len(records)==len(plan['games']):return report
        (output/'games').mkdir(exist_ok=True);probe=Probe(plan['referee'])
        try:
            for game in plan['games']:
                if game['number'] in records:continue
                print(f"Game {game['number']}/{len(plan['games'])}: {game['start_id']}, candidate {game['candidate_color']}",flush=True)
                path=game_path(output,game);binding=digest(output/'plan.json')
                write_json(path.with_suffix('.attempt.json'),dict(number=game['number'],plan_sha256=binding),exclusive=True)
                record=dict(game=game,plan_sha256=binding,status='incomplete',result='unresolved',reason=None,moves=list(game['moves']),records=[],engines={})
                engines={};failure=None
                def persist():
                    record['engines']=snapshots(engines);seal(path.with_suffix('.partial.json'),record)
                try:
                    persist()
                    for name,executable in plan['engines'].items():
                        engine=RecordedEngine.__new__(RecordedEngine);engines[name]=engine;engine.__init__(executable);persist()
                        if any('error' in line.lower() or 'failed' in line.lower() for line in engine.snapshot()['transcript']):raise ValueError('Engine loading error')
                    play(game,plan,probe,engines,record,persist)
                except BaseException as error:
                    failure=error;record.update(status='failed',result='error',failure=dict(type=type(error).__name__,message=str(error)))
                finally:
                    for engine in engines.values():
                        try:engine.close()
                        except Exception as error:
                            record.update(status='failed',result='error',failure=dict(type=type(error).__name__,message=str(error)));failure=error
                    persist();seal(path,record);records[game['number']]=record;report=aggregate(output,plan,records)
                if failure is not None:raise failure
        finally:
            probe.close();load(output)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
        print('Prepared seven book starts /14 fresh guarded games; no games played.')
    else:
        run()
        print((OUTPUT/'summary.txt').read_text(), end='')


if __name__ == '__main__':
    main()
