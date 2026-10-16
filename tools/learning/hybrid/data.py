"""Immutable hybrid inputs and one-attempt, resumable root-search teachers."""
import argparse
from collections import Counter
import hashlib
import json
import math
import re
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.refresh_teachers import RecordedEngine, check_root, classify
from tools.learning.imitation.sparse_objective import factors, root_cp
from tools.learning.tempo.prepare_tempo_search import copy_verified

DEFAULT_OUTPUT = ROOT/'results/learning-pilot/2026-10-15-hybrid-v1'
SOURCE = ROOT/'results/learning-pilot/2026-10-14-outcome-expanded-preparation-v1'
REPORT_SHA = '1034b6b043f079463b27e65724d016c08ceedb38f069064c6c6b58d0f0cc62c0'
AUDIT_SHA = 'afd61f4f96ebcff7534af60d1b0630cca5d7b4bd8e290b211058affa069365a9'
TRAINING = dict(max_updates=200,save_updates=[0,25,50,100,200],step_cp=.02,
                delta_limit_cp=.5,train_position_limit_cp=100.,max_backtracks=20,l2=1e-6)
SEARCH = dict(depth=15,timeout=30,multipv=1,threads=1,hash_mb=64,
              shin_yonenaga_gyoku=True,own_book=False,fresh_engine_per_position=True)


def write_json(path, value, *, exclusive=False):
    path = Path(path)
    data = json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if exclusive:
        with path.open('x') as stream: stream.write(data)
    else:
        temporary = path.with_suffix(path.suffix+'.tmp')
        with temporary.open('x') as stream: stream.write(data)
        temporary.replace(path)


def checked(path, sha):
    if digest(path) != sha: raise ValueError(f'SHA mismatch: {path}')


def output_path(path):
    path = Path(path).resolve()
    results = (ROOT/'results').resolve()
    if path == results or not path.is_relative_to(results):
        raise ValueError('Output must be a new descendant of results')
    return path


def validate_rows(rows):
    if Counter(r['split'] for r in rows) != dict(train=383,validation=80,diagnostic=6):
        raise ValueError('Expected complete 469-root dataset')
    if len({r['id'] for r in rows}) != len(rows) or len({(r['run'],r['game']) for r in rows}) != len(rows):
        raise ValueError('Duplicate root or game')
    runs = {s:{r['run'] for r in rows if r['split']==s} for s in ('train','validation')}
    if runs['train'] & runs['validation']: raise ValueError('Cross-split run')
    if Counter(r['split'] for r in rows if r['use_outcome_loss']) != dict(train=256,validation=64):
        raise ValueError('Expected 256/64 decisive roots')
    for row in rows:
        side = row['side']; frame = row['features']
        if type(row['use_outcome_loss']) is not bool:raise ValueError('Outcome mask must be bool')
        if any(not math.isfinite(v) for v in [row['base_cp'],frame['progress'],frame['eval_on'],*row['factors'].values()]):raise ValueError('Nonfinite frame/sample')
        if row['sfen'].split()[1] != ('b' if side=='black' else 'w'):raise ValueError('SFEN side mismatch')
        if side not in ('black','white') or ('black' if len(row['moves_before'])%2==0 else 'white') != side:
            raise ValueError('Root side/history mismatch')
        if frame['sfen'] != row['sfen'] or row['base_cp'] != root_cp(frame,side) or row['factors'] != factors(frame,side):
            raise ValueError('Feature/sample mismatch')
        if row['use_outcome_loss']:
            if row['split']=='diagnostic' or type(row['target']) not in (int,float) or row['target'] not in (0.,1.): raise ValueError('Invalid target')
        elif row['target'] is not None: raise ValueError('Masked draws must have no target')


def source_rows(report):
    rows=[]
    for split in ('train','validation','diagnostic'):
        for saved in report['records'][split]:
            row=saved['row']; frame=saved['features']; sample=saved['sample']
            side=row['side_to_move']
            expected=dict(base_cp=root_cp(frame,side),factors=factors(frame,side))
            if any(sample[k]!=v for k,v in expected.items()): raise ValueError('Saved sample differs')
            if saved['id']!=row['id'] or frame['sfen']!=row['sfen'] or saved['baseline']['huffman_hex']!=row['huffman_hex']:
                raise ValueError('Saved root identity differs')
            for key in ('sfen','eval_on','eval_off','progress'):
                if saved['baseline'][key]!=frame[key]:raise ValueError('Saved baseline/frame differs')
            for key in ('target','use_outcome_loss'):
                if saved[key]!=sample[key]: raise ValueError('Saved target differs')
            source=row['source'];checked(ROOT/source['path'],source['sha256'])
            if source['sha256']!=source['run']:raise ValueError('Source/run mismatch')
            rows.append(dict(id=row['id'],split=split,side=side,run=source['run'],game=source['game'],
                moves_before=row['moves_before'],sfen=row['sfen'],huffman_hex=row['huffman_hex'],
                **expected,features=frame,target=saved['target'],use_outcome_loss=saved['use_outcome_loss']))
    validate_rows(rows)
    return rows


def code_files():
    files=list((ROOT/'tools/learning/hybrid').glob('*.py'))
    files += [ROOT/n for n in ('tools/learning/imitation/sparse_objective.py',
        'tools/learning/data/refresh_teachers.py','tools/learning/data/prepare_learning_data.py',
        'tools/learning/tempo/prepare_tempo_search.py','tools/analysis/analyze_positions.py',
        'tools/learning/core/king_safety_updater.py','tools/learning/tempo/run_tempo_search.py',
        'tools/learning/imitation/imitation_search_review.py')]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(files)}


def prepare(output=DEFAULT_OUTPUT):
    output=output_path(output)
    checked(SOURCE/'report.json',REPORT_SHA);checked(SOURCE/'saved-label-audit.json',AUDIT_SHA)
    report=json.loads((SOURCE/'report.json').read_text());audit=json.loads((SOURCE/'saved-label-audit.json').read_text())
    if report['errors'] or not audit['accepted'] or audit['report_sha256']!=REPORT_SHA or audit['outcome_records_rechecked']!=469:
        raise ValueError('Preparation not accepted')
    for name,sha in report['required_sha256'].items():checked(ROOT/name,sha)
    rows=source_rows(report)
    # Exclusive creation deliberately refuses old experiment directories.
    output.mkdir(parents=True,exist_ok=False)
    runtime={}
    manifest=json.loads((ROOT/'results/learning-pilot/2026-10-11-full-search-preparation-v1/manifest.json').read_text())
    entries={e['source']:e for e in manifest['files'] if e['variant']=='baseline'}
    for name in ('bin/release','bin/params.bin','bin/progress.bin','bin/probability.bin','bin/book.bin','lib/libomp-x86_64/lib/libomp.dylib'):
        sha=report['required_sha256'].get(name,entries[name]['sha256'])
        target=output/'runtime'/name
        copy_verified(ROOT/name,target,sha);runtime[str(target.relative_to(output))]=sha
    dataset=dict(schema='rakuyou-hybrid-dataset-v1',rows=rows)
    write_json(output/'dataset.json',dataset,exclusive=True)
    probes={name:dict(path=path,sha256=digest(ROOT/path)) for name,path in
            [('features','results/imitation-tools/imitation-probe'),('replay','results/learning-tools/learning-data-probe')]}
    plan=dict(schema='rakuyou-hybrid-plan-v1',dataset_sha256=digest(output/'dataset.json'),
        source_sha256={str((SOURCE/n).relative_to(ROOT)):sha for n,sha in [('report.json',REPORT_SHA),('saved-label-audit.json',AUDIT_SHA)]},
        required_sha256=report['required_sha256'],code_sha256=code_files(),runtime_sha256=runtime,probes=probes,
        search=SEARCH,teacher_count=320,arms=dict(search=0.,outcome=1.,mixed=.5),training=TRAINING,
        selection='final train-stopped state; no validation selection',
        cohort_minimum_fraction=.9,cohort_require_all_side_outcome_strata=True,
        cohort='accepted decisive current-root teachers shared by all arms; draws diagnostic only',
        historical_runtime_provenance='unknown; current teachers are self-distillation, not stronger independent truth')
    write_json(output/'plan.json',plan,exclusive=True)
    (output/'plan.sha256').write_text(digest(output/'plan.json')+'\n')
    load_dataset(output)
    print('Prepared 469 roots (383 train / 80 validation / 6 diagnostic); 320 teacher searches pending. Timeout cap: 160 minutes plus process startup.',flush=True)
    return plan,dataset


def load_dataset(output=DEFAULT_OUTPUT):
    output=output_path(output)
    checked(output/'plan.json',(output/'plan.sha256').read_text().strip())
    plan=json.loads((output/'plan.json').read_text())
    if (plan.get('schema')!='rakuyou-hybrid-plan-v1' or plan['search']!=SEARCH or plan['training']!=TRAINING
            or plan['teacher_count']!=320 or plan['arms']!=dict(search=0.,outcome=1.,mixed=.5)
            or plan['cohort_minimum_fraction']!=.9 or plan['cohort_require_all_side_outcome_strata'] is not True):
        raise ValueError('Unexpected fixed configuration')
    checked(output/'dataset.json',plan['dataset_sha256'])
    for binding in ('source_sha256','required_sha256','code_sha256'):
        for name,sha in plan[binding].items(): checked(ROOT/name,sha)
    if plan['code_sha256']!=code_files():raise ValueError('Hybrid code files changed')
    for name,sha in plan['runtime_sha256'].items(): checked(output/name,sha)
    for entry in plan['probes'].values():checked(ROOT/entry['path'],entry['sha256'])
    dataset=json.loads((output/'dataset.json').read_text())
    if dataset['schema']!='rakuyou-hybrid-dataset-v1':raise ValueError('Dataset schema mismatch')
    validate_rows(dataset['rows'])
    return plan,dataset


def record_path(output, id):
    return Path(output)/'teachers'/(hashlib.sha256(id.encode()).hexdigest()+'.json')


def validate_teacher(record,row,plan_sha):
    if (record.get('schema')!='rakuyou-hybrid-teacher-v1' or record['id']!=row['id']
            or record['plan_sha256']!=plan_sha or record['split']!=row['split']):
        raise ValueError('Teacher binding mismatch')
    if record['status'] not in ('accepted','excluded','failed'):raise ValueError('Unknown teacher status')
    if not isinstance(record['commands'],list) or not isinstance(record['transcript'],list):raise ValueError('Missing teacher transcript')
    if record['status']=='accepted':
        result=record['analysis']; candidates=result['candidates']
        if result['stopped_early'] or len(candidates)!=1:raise ValueError('Incomplete accepted teacher')
        c=candidates[0];raw=c['raw'];tokens=raw.split()
        if (c['depth']!=15 or c['score_type']!='cp' or not c['pv']
                or result['bestmove']!=c['pv'][0] or any(t in tokens for t in ('lowerbound','upperbound'))):
            raise ValueError('Invalid accepted teacher')
        score=int(c['score'])
        if (type(record['teacher_cp']) is not int or record['teacher_cp']!=score or abs(score)>=31000
                or not re.search(r'\bdepth 15(?:\s|$)',raw)
                or not re.search(rf'\bscore cp {score}(?:\s|$)',raw)
                or raw.split(' pv ')[-1].split()!=c['pv'] or raw not in record['transcript']):
            raise ValueError('Accepted teacher raw score/depth/PV mismatch')
    elif record['teacher_cp'] is not None:raise ValueError('Nonaccepted teacher has score')


def teacher_summary(output,plan,rows):
    records=[];hashes={};plan_sha=digest(Path(output)/'plan.json')
    for row in rows:
        path=record_path(output,row['id']);marker=path.with_suffix('.attempt.json')
        if marker.exists() and not path.exists():raise ValueError(f'Orphan teacher attempt; no automatic retry: {row["id"]}')
        if not path.exists():continue
        if not marker.exists():raise ValueError('Teacher result missing attempt marker')
        try:
            attempt=json.loads(marker.read_text())
            if attempt != dict(id=row['id'],plan_sha256=plan_sha):raise ValueError('Teacher attempt binding mismatch')
            checked(path,path.with_suffix('.sha256').read_text().strip())
            record=json.loads(path.read_text())
        except (OSError,json.JSONDecodeError) as error:
            raise ValueError(f'Incomplete teacher result; no automatic retry: {row["id"]}') from error
        validate_teacher(record,row,plan_sha)
        hashes[row['id']]=digest(path);records.append(record)
    counts=dict(Counter(r['status'] for r in records))
    return dict(schema='rakuyou-hybrid-teachers-v1',plan_sha256=plan_sha,
        dataset_sha256=plan['dataset_sha256'],completed=bool(len(records)==len(rows) and not counts.get('failed')),
        records=records,records_sha256=hashes,counts=counts)


def aggregate(output,plan,rows):
    result=teacher_summary(output,plan,rows)
    write_json(Path(output)/'teachers.json',result)
    return result


def load_teachers(output,plan,rows):
    """Validate saved teachers and aggregate without starting a native process."""
    expected=teacher_summary(output,plan,[r for r in rows if r.get('use_outcome_loss',True)])
    try:saved=json.loads((Path(output)/'teachers.json').read_text())
    except (OSError,json.JSONDecodeError) as error:raise ValueError('Missing or incomplete teacher aggregate') from error
    if saved!=expected:raise ValueError('Teacher aggregate differs from checksummed records')
    return saved


def teachers(output=DEFAULT_OUTPUT):
    output=output_path(output);plan,dataset=load_dataset(output)
    rows=[r for r in dataset['rows'] if r['use_outcome_loss']]
    (output/'teachers').mkdir(exist_ok=True)
    summary=aggregate(output,plan,rows)
    if len(summary['records'])==len(rows):return summary
    probe=Probe(ROOT/plan['probes']['replay']['path'])
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
                engine.__init__(output/'runtime/bin/release')
                if any('error' in line.lower() or 'failed' in line.lower() for line in engine.transcript):raise ValueError('Engine loading error')
                result=engine.analyze(row['moves_before'],15,30,multipv=1)
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
            if len(summary['records'])%10==0:print(f"teachers {len(summary['records'])}/320 {summary['counts']}",flush=True)
    finally:probe.close()
    load_dataset(output)
    print(json.dumps(dict(completed=summary['completed'],counts=summary['counts'])),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','teachers'])
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    try:
        result=globals()[args.command](args.output)
        if args.command=='teachers' and not result['completed']:raise SystemExit('Teacher collection failed or incomplete; training blocked')
    except (ValueError,OSError) as error:raise SystemExit(str(error)) from None


if __name__=='__main__':main()
