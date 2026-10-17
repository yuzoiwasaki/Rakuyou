"""Export fixed projected-search and compare 24 exposed roots with saved old searches."""
import argparse
import json
from pathlib import Path
import subprocess

from tools.learning.constraints import runner_v2 as training
from tools.learning.hybrid import export as exporter
from tools.learning.hybrid import runner as common
from tools.learning.hybrid.data import checked, output_path, write_json
from tools.learning.playtest import behavior as previous
from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.refresh_teachers import RecordedEngine
from tools.learning.tempo.prepare_tempo_search import copy_verified

SOURCE=training.OUTPUT
OUTPUT=ROOT/'results/learning-pilot/2026-10-17-projected-behavior-v1'
ARM='projected-search'
SETTINGS=dict(depth=15,timeout=30,multipv=1,threads=1,hash_mb=64,
              shin_yonenaga_gyoku=True,own_book=False,fresh_engine_per_position=True,
              new_searches=24)


def source_inputs():
    plan,base,dataset,parts=training.load(SOURCE)
    directory=SOURCE/ARM
    state=common.unseal(directory/'checkpoint.json')
    training.validate(state,plan['keys'],dict(plan_sha256=digest(SOURCE/'plan.json'),
                      method='projected',arm='search',alpha=0.),plan['training'],parts['train'])
    report=common.unseal(directory/'report.json')
    if (not state['stopped'] or state['updates']!=200 or state['stopping_reason']!='update_budget'
            or report['checkpoint_sha256']!=digest(directory/'checkpoint.json')
            or report['evaluation']['sidecar_sha256']!=digest(directory/'delta.txt')
            or report['evaluation']['max_smooth_change_cp']>100):
        raise ValueError('Expected unchanged fixed search checkpoint within observed impact bound')
    return base,dataset,report


def export():
    base,dataset,report=source_inputs()
    directory=SOURCE/ARM
    with common.exclusive(SOURCE/'training.lock'):
        source_inputs()
        bound={str(p):digest(p) for p in (directory/'checkpoint.json',directory/'report.json',directory/'delta.txt')}
        binary=exporter.EXPORTER
        build=json.loads((binary.parent/'build.json').read_text())
        if (digest(binary)!=build['binary_sha256']
                or digest(binary.parent/'export.cc')!=build['generated_sha256']
                or digest(ROOT/'tools/learning/native/imitation_probe.cc')!=build['probe_source_sha256']):
            raise ValueError('Exporter binding differs')
        target=directory/'runtime';target.mkdir(exist_ok=False);(target/'bin').mkdir()
        params=target/'bin/params.bin';original=training.SOURCE/'runtime/bin/params.bin'
        layout=json.loads(subprocess.check_output([str(binary),str(original),str(directory/'delta.txt'),str(params)],text=True))
        zero=target/'zero.txt';zero.write_text('')
        subprocess.run([str(binary),str(original),str(zero),str(target/'zero-params.bin')],capture_output=True,text=True,check=True)
        if digest(target/'zero-params.bin')!=digest(original):raise ValueError('Zero export differs')
        changed=exporter.audit_bytes(original,params,layout)
        for name,sha in base['runtime_sha256'].items():
            relative=Path(name).relative_to('runtime')
            if relative!=Path('bin/params.bin'):copy_verified(training.SOURCE/name,target/relative,sha)
        raw={}
        for line in (directory/'delta.txt').read_text().splitlines():
            *key,value=line.split();raw[':'.join(key)]=int(value)
        expected={r['id']:r['candidate_cp'] for r in report['evaluation']['observations']}
        frames=common.native_frames(base,training.SOURCE,dataset['rows'],params=params)
        for row,frame in zip(dataset['rows'],frames):
            if common.check_frame(row,frame,raw)!=expected[row['id']]:raise ValueError('Export score differs')
        source_inputs()
        for name,sha in bound.items():checked(name,sha)
        audit=dict(schema='projected-export-v1',inputs_sha256=bound,params_sha256=digest(params),
                   zero_export_sha256=digest(original),exporter_sha256=digest(binary),changed_bytes=changed,
                   static_checks=len(frames),searches=0,deployed=False,
                   runtime_sha256={str(p.relative_to(target)):digest(p) for p in target.rglob('*') if p.is_file()})
        common.seal(directory/'export-audit.json',audit)
        print('Exported fixed projected-search; 469 static checks, no search.',flush=True)


def dependencies():
    return {**previous.dependencies(),**training.dependencies(),
            'tools/learning/constraints/behavior.py':digest(Path(__file__)),
            'tools/learning/hybrid/export.py':digest(ROOT/'tools/learning/hybrid/export.py')}


def preparation_inputs():
    source_inputs()
    parent=previous.load(previous.OUTPUT)
    records=previous.saved(previous.OUTPUT,parent)
    if len(records)!=48 or any(r['status']!='success' for r in records.values()):
        raise ValueError('Expected 48 successful saved searches')
    audit=common.unseal(SOURCE/ARM/'export-audit.json');runtime=SOURCE/ARM/'runtime'
    if audit['schema']!='projected-export-v1' or audit['static_checks']!=469 or audit['searches'] or audit['deployed']:
        raise ValueError('Invalid export audit')
    for path,sha in audit['inputs_sha256'].items():checked(path,sha)
    actual={str(p.relative_to(runtime)):digest(p) for p in runtime.rglob('*') if p.is_file()}
    if actual!=audit['runtime_sha256']:raise ValueError('Export runtime changed')
    bindings={str(previous.OUTPUT/'plan.json'):digest(previous.OUTPUT/'plan.json'),
              str(SOURCE/'plan.json'):digest(SOURCE/'plan.json'),
              str(SOURCE/ARM/'export-audit.json'):digest(SOURCE/ARM/'export-audit.json')}
    for row in parent['roots']:
        for variant in ('baseline','candidate'):
            path=previous.paths(previous.OUTPUT,row,variant)
            bindings[str(path)]=digest(path)
            marker=path.with_suffix('.attempt.json');bindings[str(marker)]=digest(marker)
    return parent,records,audit,bindings


def prepare():
    parent,records,audit,bindings=preparation_inputs()
    probe=Probe(parent['probe'])
    try:
        for row in parent['roots']:
            for variant in ('baseline','candidate'):
                record=records[(row['id'],variant)]
                diagnosis=previous.diagnose(record['analysis'],row,probe)
                if diagnosis!=record['diagnosis']:raise ValueError('Saved diagnosis differs')
                commands=record['commands']
                if commands.count('go depth 15')!=1 or 'stop' in commands:
                    raise ValueError('Saved search not reusable')
    finally:probe.close()
    plan=dict(schema='projected-behavior-v1',settings=SETTINGS,roots=parent['roots'],
              inputs_sha256=bindings,code_sha256=dependencies(),probe=parent['probe'],
              runtime_sha256=audit['runtime_sha256'],engine=str(SOURCE/ARM/'runtime/bin/release'))
    OUTPUT.mkdir(parents=True,exist_ok=False);common.seal(OUTPUT/'plan.json',plan)
    print('Prepared 24 new searches; 48 old searches audited for reuse.',flush=True)


def load():
    plan=common.unseal(OUTPUT/'plan.json')
    parent,records,audit,bindings=preparation_inputs()
    if (plan['schema']!='projected-behavior-v1' or plan['settings']!=SETTINGS
            or plan['roots']!=parent['roots'] or plan['inputs_sha256']!=bindings
            or plan['code_sha256']!=dependencies() or plan['probe']!=parent['probe']
            or plan['runtime_sha256']!=audit['runtime_sha256']
            or plan['engine']!=str(SOURCE/ARM/'runtime/bin/release')):
        raise ValueError('Frozen comparison changed')
    return plan,records


def path_for(row):return previous.paths(OUTPUT,row,'projected')


def saved(plan):
    records={};binding=digest(OUTPUT/'plan.json')
    for row in plan['roots']:
        path=path_for(row);marker=path.with_suffix('.attempt.json')
        expected=dict(id=row['id'],plan_sha256=binding)
        if not marker.exists():
            if path.exists():raise ValueError('Missing attempt marker')
            continue
        if json.loads(marker.read_text())!=expected:raise ValueError('Attempt binding differs')
        if not path.exists():raise ValueError('Interrupted attempt blocks retry')
        r=common.unseal(path)
        if any(r.get(k)!=v for k,v in expected.items()) or r['status'] not in ('success','failed'):
            raise ValueError('Saved search binding differs')
        records[row['id']]=r
    return records


def comparisons(plan,old,new):
    pairs=[];changed=dict(baseline=0,old_search=0);valid=0
    for row in plan['roots']:
        variants=dict(baseline=old[(row['id'],'baseline')],old_search=old[(row['id'],'candidate')])
        if row['id'] in new:variants['projected_search']=new[row['id']]
        pair=dict(root=row,results=variants)
        if len(variants)==3 and all(r['status']=='success' and r['diagnosis']['kind']=='regular' for r in variants.values()):
            valid+=1
            pair['changed']={k:variants[k]['analysis']['bestmove']!=variants['projected_search']['analysis']['bestmove'] for k in changed}
            for k in changed:changed[k]+=pair['changed'][k]
        pairs.append(pair)
    return dict(plan_sha256=digest(OUTPUT/'plan.json'),new_attempted=len(new),
                new_successful=sum(r['status']=='success' for r in new.values()),
                valid_triples=valid,changed_bestmoves=changed,pairs=pairs,
                limitation='Exposed validation roots; score differences are not strength gains. No games or deployment.')


def summarize(plan,old,new):
    report=comparisons(plan,old,new);common.seal(OUTPUT/'report.json',report)
    text=(f"New searches {report['new_successful']}/24 successful, {report['new_attempted']}/24 attempted; "
          f"valid triples {report['valid_triples']}.\nChanged moves: {report['changed_bestmoves']}\n"+report['limitation']+'\n')
    (OUTPUT/'summary.txt').write_text(text)


def run():
    plan,old=load()
    with common.exclusive(OUTPUT/'run.lock'):
        new=saved(plan);(OUTPUT/'searches').mkdir(exist_ok=True)
        probe=Probe(plan['probe'])
        try:
            for row in plan['roots']:
                if row['id'] in new:continue
                print(f"Search {len(new)+1}/24: projected {row['id']}",flush=True)
                path=path_for(row);identity=dict(id=row['id'],plan_sha256=digest(OUTPUT/'plan.json'))
                write_json(path.with_suffix('.attempt.json'),identity,exclusive=True)
                record=dict(**identity,status='failed');engine=None
                try:
                    engine=RecordedEngine.__new__(RecordedEngine);engine.__init__(Path(plan['engine']))
                    if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript):raise ValueError('Engine loading error')
                    record['analysis']=engine.analyze(row['moves_before'],15,30,multipv=1)
                    if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript):raise ValueError('Engine search error')
                    record['diagnosis']=previous.diagnose(record['analysis'],row,probe)
                    record['status']='success'
                except Exception as error:record['failure']=f'{type(error).__name__}: {error}'
                finally:
                    if engine is not None:
                        try:engine.close()
                        except Exception as error:record.update(status='failed',failure=f'Close: {error}')
                        record['commands']=getattr(engine,'commands',[]);record['transcript']=getattr(engine,'transcript',[])
                    common.seal(path,record);new[row['id']]=record;summarize(plan,old,new)
        finally:probe.close();load()
        summarize(plan,old,new)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('export','prepare','run'))
    args=parser.parse_args()
    if args.command=='export':export()
    elif args.command=='prepare':prepare()
    else:run();print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':main()
