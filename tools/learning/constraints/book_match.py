"""Fixed candidate comparison after all canonical operational-book leaf prefixes."""
import argparse
from pathlib import Path
from tools.analysis.audit_white_positions import Board
from tools.learning.constraints import match as first
from tools.learning.constraints.alternate_match import keys, normalized
from tools.learning.constraints.match import (RecordedEngine,Probe,digest,checked,output_path,
    write_json,exclusive,seal,unseal,game_path,snapshots,play,saved,aggregate)

OUTPUT=first.behavior.ROOT/'results/learning-pilot/2026-10-18-projected-book-match-v1'
BOOK=first.behavior.ROOT/'books/shin-yonenaga-book-v1.txt'


def book_starts(book=BOOK):
    entries=[]
    for line in book.read_text().splitlines():
        if line and not line.startswith('#'):
            parent,move=line.split(' | ')
            entries.append((parent.split(),move))
    if len(entries)!=17:raise ValueError('Expected 17 operational book entries')
    leaves=[a+[b] for a,b in entries
            if not any(a+[b]==c[:len(a)+1] and len(c)>len(a) for c,d in entries)]
    if len(leaves)!=7:raise ValueError('Expected seven canonical leaves')
    return [dict(id=('black' if moves[0]=='5i4h' else 'white')+'-shin-book-'+str(i+1),moves=moves)
            for i,moves in enumerate(leaves)]


def dependencies():
    return {**first.bindings()[3],
            'tools/learning/constraints/book_match.py':digest(Path(__file__)),
            'tools/learning/constraints/alternate_match.py':digest(Path(__file__).with_name('alternate_match.py')),
            'tools/analysis/audit_white_positions.py':digest(first.behavior.ROOT/'tools/analysis/audit_white_positions.py')}


def prepare(output=OUTPUT):
    output=output_path(output);parent=first.load(first.OUTPUT)
    starts=book_starts();seen=set();roots=[]
    registered=set()
    for line in BOOK.read_text().splitlines():
        if line and not line.startswith('#'):
            board=Board()
            for move in line.split(' | ')[0].split():board.push(move)
            registered.add(board.sfen())
    probe=Probe(parent['referee'])
    try:
        for row in starts:
            state=first.previous.replay(probe,row['moves']);root=state['positions'][-1]
            identity=keys(root['sfen'])
            if state['result']!='ongoing' or any(p['occurrences']>1 for p in state['positions']):raise ValueError('Terminal/repeated start')
            if identity & seen:raise ValueError('Duplicate book root')
            board=Board()
            for move in row['moves']:board.push(move)
            if normalized(root['sfen'])!=board.sfen():raise ValueError('Independent board differs')
            if board.sfen() in registered:raise ValueError('Leaf re-enters registered book position')
            seen.update(identity);roots.append(dict(**row,sfen=root['sfen']))
    finally:probe.close()
    plan=dict(schema='projected-book-match-v1',settings=parent['settings'],starts=roots,
              games=first.previous.games(roots),
              inputs_sha256={str(BOOK):digest(BOOK),str(first.OUTPUT/'plan.json'):digest(first.OUTPUT/'plan.json')},
              code_sha256=dependencies(),referee=parent['referee'],engines=parent['engines'],
              runtime_sha256=parent['runtime_sha256'],
              selection='All seven canonical operational-book leaves, without score or result filtering; related and previously exposed branches.',
              limitation='Fourteen fixed-depth games after operational-book prefixes; related branches, not independent or equal-time strength proof. Max-ply endings unresolved.')
    output.mkdir(parents=True,exist_ok=False);seal(output/'plan.json',plan)
    return plan


def load(output):
    output=output_path(output);plan=unseal(output/'plan.json');parent=first.load(first.OUTPUT)
    if (plan['schema']!='projected-book-match-v1' or plan['code_sha256']!=dependencies()
            or plan['settings']!=parent['settings'] or plan['engines']!=parent['engines']
            or plan['runtime_sha256']!=parent['runtime_sha256'] or plan['referee']!=parent['referee']
            or plan['games']!=first.previous.games(plan['starts'])
            or [{k:r[k] for k in ('id','moves')} for r in plan['starts']]!=book_starts()):
        raise ValueError('Book match binding differs')
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
        prepare();print('Prepared seven book starts / 14 games; no searches or games.')
    else:
        run();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':main()
