"""Fixed candidate on eight prospectively specified alternative opening roots."""
import argparse
import json
import re
from pathlib import Path
from tools.analysis.audit_white_positions import Board
from tools.learning.constraints import match as first
from tools.learning.constraints.match import (RecordedEngine,Probe,digest,checked,output_path,
    write_json,exclusive,seal,unseal,game_path,snapshots,play,saved,aggregate)

OUTPUT=first.behavior.ROOT/'results/learning-pilot/2026-10-18-projected-alternate-match-v1'
CONFIG=first.behavior.ROOT/'docs/experiments/configs/projected-alternate-starts-v1.json'


def normalized(sfen):return ' '.join(sfen.split()[:3])


def rotated(sfen):
    board,side,hand=sfen.split()[:3]
    rows=[]
    for row in board.split('/')[::-1]:
        tokens=re.findall(r'\+?[A-Za-z]|[1-9]',row)
        rows.append(''.join(t.swapcase() for t in tokens[::-1]))
    counts={piece.swapcase():int(count or '1') for count,piece in re.findall(r'(\d*)([A-Za-z])',hand)}
    newhand=''.join((str(counts[p]) if counts[p]>1 else '')+p for p in 'RBGSNLPrbgsnlp' if counts.get(p)) or '-'
    return '/'.join(rows)+' '+('w' if side=='b' else 'b')+' '+newhand


def keys(sfen):return {normalized(sfen),rotated(sfen)}


def corpus(parent):
    # Known saved positions only; no claim to cover every historical artifact.
    _,dataset=first.behavior.training.data.load_dataset(first.behavior.training.SOURCE)
    known=set();counts=dict(learning_histories=0,match_games=0)
    bindings={str(first.behavior.training.SOURCE/'dataset.json'):digest(first.behavior.training.SOURCE/'dataset.json')}
    for row in dataset['rows']:
        b=Board();known.update(keys(b.sfen()))
        for move in row['moves_before']:
            b.push(move);known.update(keys(b.sfen()))
        counts['learning_histories']+=1
    for output,plan in [(first.OUTPUT,parent),(first.previous.OUTPUT,first.previous.load(first.previous.OUTPUT))]:
        records=saved(output,plan)
        if len(records)!=16 or any(r['status']!='completed' for r in records.values()):
            raise ValueError('Expected complete prior match corpus')
        for game in records.values():
            path=game_path(output,game['game']);bindings[str(path)]=digest(path)
            for position in game['last_referee']['positions']:known.update(keys(position['sfen']))
            counts['match_games']+=1
    return known,counts,bindings


def dependencies():
    return {**first.bindings()[3],
            'tools/learning/constraints/alternate_match.py':digest(Path(__file__)),
            'tools/analysis/audit_white_positions.py':digest(first.behavior.ROOT/'tools/analysis/audit_white_positions.py')}


def prepare(output=OUTPUT):
    output=output_path(output);parent=first.load(first.OUTPUT)
    config=json.loads(CONFIG.read_text())
    if config['schema']!='projected-alternate-starts-v1' or len(config['starts'])!=8:raise ValueError('Invalid starts config')
    known,counts,bindings=corpus(parent);seen=set();roots=[]
    probe=Probe(parent['referee'])
    try:
        for row in config['starts']:
            if len(row['moves'])!=12:raise ValueError('Expected 12-ply prefix')
            state=first.previous.replay(probe,row['moves']);root=state['positions'][-1]
            identity=keys(root['sfen'])
            if state['result']!='ongoing' or any(p['occurrences']>1 for p in state['positions']):raise ValueError('Terminal/repeated start')
            if identity & (known|seen):raise ValueError('Duplicate or previously recorded root: '+row['id'])
            b=Board()
            for move in row['moves']:b.push(move)
            if normalized(root['sfen'])!=b.sfen():raise ValueError('Independent board differs')
            seen.update(identity);roots.append(dict(id=row['id'],moves=row['moves'],sfen=root['sfen']))
    finally:probe.close()
    if len({r['id'] for r in roots})!=8:raise ValueError('Duplicate IDs')
    bindings.update({str(CONFIG):digest(CONFIG),str(first.OUTPUT/'plan.json'):digest(first.OUTPUT/'plan.json')})
    plan=dict(schema='projected-alternate-match-v1',settings=parent['settings'],starts=roots,
              games=first.previous.games(roots),inputs_sha256=bindings,code_sha256=dependencies(),
              referee=parent['referee'],engines=parent['engines'],runtime_sha256=parent['runtime_sha256'],
              novelty_audit=counts,selection=config['selection'],
              limitation='Sixteen fixed-depth games on prospectively specified alternative starts; checked corpus only, not independent or equal-time strength proof. Max-ply endings unresolved.')
    output.mkdir(parents=True,exist_ok=False);seal(output/'plan.json',plan)
    return plan


def load(output):
    output=output_path(output);plan=unseal(output/'plan.json');parent=first.load(first.OUTPUT)
    config=json.loads(CONFIG.read_text())
    if (plan['schema']!='projected-alternate-match-v1' or plan['code_sha256']!=dependencies()
            or plan['settings']!=parent['settings'] or plan['engines']!=parent['engines']
            or plan['runtime_sha256']!=parent['runtime_sha256'] or plan['referee']!=parent['referee']
            or plan['games']!=first.previous.games(plan['starts'])
            or [{k:r[k] for k in ('id','moves')} for r in plan['starts']]!=config['starts']):
        raise ValueError('Alternate match binding differs')
    for name,sha in plan['inputs_sha256'].items():checked(name,sha)
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
        prepare();print('Prepared eight alternative starts / 16 games; no searches or games.')
    else:
        run();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':main()
