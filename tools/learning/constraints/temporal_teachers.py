"""Fresh teachers for fixed temporal roots; no training or deployment."""
import argparse
import json
from pathlib import Path
from tools.learning.hybrid import data as old
from tools.learning.hybrid.runner import exclusive,seal,unseal,native_frames
from tools.learning.data.refresh_teachers import RecordedEngine,classify
from tools.learning.data.prepare_learning_data import ROOT,Probe,digest
from tools.learning.imitation.sparse_objective import factors,root_cp
from tools.learning.constraints import temporal
from tools.learning.hybrid.data import write_json,record_path,aggregate,output_path

OUTPUT=ROOT/'results/learning-pilot/2026-10-18-temporal-teachers-v2'


def dependencies():
    return {str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),Path(temporal.__file__)]}


def prepare(output=OUTPUT):
    output=old.output_path(output)
    parent,dataset=old.load_dataset(temporal.SOURCE)
    old.load_teachers(temporal.SOURCE,parent,dataset['rows'])
    path=temporal.OUTPUT/'selection.json';selection=json.loads(path.read_text())
    for name,sha in {**selection['inputs_sha256'],**selection['code_sha256']}.items():old.checked(ROOT/name,sha)
    rows=selection['additional']
    # Static feature extraction only, using the same isolated baseline parameters.
    frames=native_frames(parent,temporal.SOURCE,[dict(features=dict(sfen=r['sfen'])) for r in rows])
    prepared=[]
    for row,frame in zip(rows,frames):
        if frame['sfen']!=row['sfen']:raise ValueError('Feature SFEN differs')
        prepared.append(dict(**row,use_outcome_loss=True,features=frame,
                             base_cp=root_cp(frame,row['side']),factors=factors(frame,row['side'])))
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'dataset.json',dict(rows=prepared),exclusive=True)
    plan=dict(schema='temporal-teachers-v1',dataset_sha256=digest(output/'dataset.json'),
              selection_sha256=digest(path),parent_plan_sha256=digest(temporal.SOURCE/'plan.json'),
              parent_teachers_sha256=digest(temporal.SOURCE/'teachers.json'),code_sha256=dependencies(),
              referee='results/match-tools-v2/match-referee',
              referee_sha256=digest(ROOT/'results/match-tools-v2/match-referee'),
              engine=str((temporal.SOURCE/'runtime/bin/release').relative_to(ROOT)),
              search={**parent['search'], 'timeout':300},new_search_budget=len(rows),
              reuse_count=len(selection['original_ids']),training=False,
              weighting='After exclusions, each original game has equal total weight within its split; never pool rows uniformly.',
              no_refill=True)
    seal(output/'plan.json',plan)
    return plan


def load(output=OUTPUT):
    output=old.output_path(output);plan=unseal(output/'plan.json')
    parent,dataset=old.load_dataset(temporal.SOURCE)
    if (plan['schema']!='temporal-teachers-v1' or plan['code_sha256']!=dependencies()
            or plan['search']!={**parent['search'],'timeout':300} or plan['training'] is not False):
        raise ValueError('Temporal teacher plan differs')
    old.checked(temporal.SOURCE/'plan.json',plan['parent_plan_sha256'])
    old.checked(temporal.SOURCE/'teachers.json',plan['parent_teachers_sha256'])
    old.checked(temporal.OUTPUT/'selection.json',plan['selection_sha256'])
    old.checked(ROOT/plan['referee'],plan['referee_sha256'])
    old.checked(output/'dataset.json',plan['dataset_sha256'])
    new=json.loads((output/'dataset.json').read_text())
    if len(new['rows'])!=plan['new_search_budget']:raise ValueError('Row count differs')
    return plan,new


def check_root(row,probe):
    state=probe.replay(row['moves_before'])
    if (not state.get('ok') or state['result']!='ongoing'
            or state['positions'][-1]['sfen']!=row['sfen']
            or any(p['occurrences']>1 for p in state['positions'])):
        raise ValueError('Root history differs')


def _teachers(output=OUTPUT):
    output=output_path(output);plan,dataset=load(output)
    rows=[r for r in dataset['rows'] if r['use_outcome_loss']]
    (output/'teachers').mkdir(exist_ok=True)
    summary=aggregate(output,plan,rows)
    if len(summary['records'])==len(rows):return summary
    probe=Probe(ROOT/plan['referee'])
    try:
        for row in rows:
            path=record_path(output,row['id'])
            if path.exists():continue
            record=dict(schema='rakuyou-hybrid-teacher-v1',id=row['id'],split=row['split'],status='failed',teacher_cp=None,
                        plan_sha256=digest(output/'plan.json'),commands=[],transcript=[])
            write_json(path.with_suffix('.attempt.json'),dict(id=row['id'],plan_sha256=record['plan_sha256']),exclusive=True)
            engine=None
            try:
                check_root(row,probe)
                # Allocate before __init__ so startup failures retain their transcript.
                engine=RecordedEngine.__new__(RecordedEngine)
                engine.__init__(ROOT/plan['engine'])
                if any('error' in line.lower() or 'failed' in line.lower() for line in engine.transcript):raise ValueError('Engine loading error')
                result=engine.analyze(row['moves_before'],15,plan['search']['timeout'],multipv=1)
                record['analysis']=result
                if any('error' in line.lower() or 'failed' in line.lower() for line in engine.transcript):raise ValueError('Engine search error')
                cp,reason=classify(result,row,probe)
                record.update(status='excluded' if reason else 'accepted',teacher_cp=cp,excluded=reason)
            except BaseException as error:
                record['failure']=dict(type=type(error).__name__,message=str(error))
                if not isinstance(error,Exception):raise
            finally:
                if engine is not None:
                    try:engine.close()
                    except Exception as error:
                        record.update(status='failed',teacher_cp=None,close_error=str(error))
                    record['commands']=getattr(engine,'commands',[])
                    record['transcript']=getattr(engine,'transcript',[])
                write_json(path,record,exclusive=True)
                with path.with_suffix('.sha256').open('x') as stream:stream.write(digest(path)+'\n')
                summary=aggregate(output,plan,rows)
            if len(summary['records'])%10==0:print(f"teachers {len(summary['records'])}/{len(rows)} {summary['counts']}",flush=True)
    finally:probe.close()
    load(output)
    print(json.dumps(dict(completed=summary['completed'],counts=summary['counts'])),flush=True)
    return summary



def teachers(output=OUTPUT):
    with exclusive(output/'teachers.lock'):
        return _teachers(output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','teachers'])
    args=parser.parse_args()
    if args.command=='prepare':
        plan=prepare();print('Prepared',plan['new_search_budget'],'new teachers; no searches.')
    else:
        result=teachers()
        if not result['completed']:raise SystemExit('Incomplete teachers; inspect saved errors. No automatic retry.')


if __name__=='__main__':main()
