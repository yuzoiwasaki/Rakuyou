"""Fresh 16-game projected-search pilot using the previously audited match rules."""
import argparse
from pathlib import Path

from tools.learning.constraints import behavior
from tools.learning.playtest import match as previous
from tools.learning.playtest.match import (RecordedEngine, Probe, digest, checked,
    output_path, write_json, exclusive, seal, unseal, game_path, snapshots,
    play, saved, aggregate)

OUTPUT=behavior.ROOT/'results/learning-pilot/2026-10-17-projected-match-v1'


def bindings():
    parent=previous.load(previous.OUTPUT)
    bp,old=behavior.load()
    new=behavior.saved(bp)
    report=unseal(behavior.OUTPUT/'report.json')
    if report!=behavior.comparisons(bp,old,new) or report['new_successful']!=24 or report['valid_triples']!=24:
        raise ValueError('Expected completed 24-root behavior review')
    inputs={str(previous.OUTPUT/'plan.json'):digest(previous.OUTPUT/'plan.json'),
            str(behavior.OUTPUT/'plan.json'):digest(behavior.OUTPUT/'plan.json'),
            str(behavior.OUTPUT/'report.json'):digest(behavior.OUTPUT/'report.json')}
    runtime=dict(parent['runtime_sha256'])
    runtime.update({str(behavior.SOURCE/behavior.ARM/'runtime'/p):sha for p,sha in bp['runtime_sha256'].items()})
    code={**previous.dependencies(),**behavior.dependencies(),
          'tools/learning/constraints/match.py':digest(Path(__file__))}
    engines=dict(baseline=parent['engines']['baseline'],candidate=bp['engine'])
    return parent,inputs,runtime,code,engines


def prepare(output=OUTPUT):
    output=output_path(output)
    parent,inputs,runtime,code,engines=bindings()
    probe=Probe(parent['referee'])
    try:
        for row in parent['starts']:
            state=previous.replay(probe,row['moves'])
            if (state['result']!='ongoing' or state['positions'][-1]['sfen']!=row['sfen']
                    or any(p['occurrences']>1 for p in state['positions'])):
                raise ValueError('Start history differs')
    finally:probe.close()
    plan=dict(schema='projected-match-v1',settings=parent['settings'],starts=parent['starts'],
              games=previous.games(parent['starts']),inputs_sha256=inputs,runtime_sha256=runtime,
              code_sha256=code,referee=parent['referee'],engines=engines,
              limitation='Sixteen fresh fixed-depth games on previously exposed starts; not an equal-time or independent strength estimate. Max-ply endings unresolved.')
    output.mkdir(parents=True,exist_ok=False);seal(output/'plan.json',plan)
    return plan


def load(output):
    output=output_path(output);plan=unseal(output/'plan.json')
    parent,inputs,runtime,code,engines=bindings()
    if (plan['schema']!='projected-match-v1' or plan['settings']!=parent['settings']
            or plan['starts']!=parent['starts'] or plan['games']!=previous.games(parent['starts'])
            or plan['inputs_sha256']!=inputs or plan['runtime_sha256']!=runtime
            or plan['code_sha256']!=code or plan['engines']!=engines
            or plan['referee']!=parent['referee']):
        raise ValueError('Projected match binding differs')
    for path,sha in runtime.items():checked(path,sha)
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
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'))
    args=parser.parse_args()
    if args.command=='prepare':
        prepare();print('Prepared 16 fresh projected-search games; no games played.')
    else:
        run();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':main()
