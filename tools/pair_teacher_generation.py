#!/usr/bin/env python3
"""Fixed 180-root generation and read-only audit; no learning or replacement."""
import argparse
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path
from prepare_learning_data import ROOT,Probe,digest
from prepare_tempo_search import copy_verified
from run_tempo_search import PREPARATION_SHA,write_report
from learning_backup import safe_path
from refresh_teachers import RecordedEngine,check_root,classify,check_plan,now,RUNTIME_MANIFEST
from audit_refreshed_teachers import audit_record
PREP_SHA='6a3c44bafa2603063c6b1d60a1eb735864be5b365d8e5c9a1d1ace229129084f'
PREP=ROOT/'results/learning-pilot/2026-10-12-pair-expansion-preparation-v1/manifest.json'
DEFAULT_PLAN=PREP.parent/'plan.json'


def load_binding(preparation,plan_path,run):
    preparation=Path(preparation).resolve();plan_path=Path(plan_path).resolve()
    if digest(preparation)!=PREP_SHA:raise ValueError('Expanded preparation SHA mismatch')
    m=json.loads(preparation.read_bytes())
    if digest(DEFAULT_PLAN)!=m['plan_sha256']:raise ValueError('Reference plan changed')
    reference=json.loads(DEFAULT_PLAN.read_bytes());plan=json.loads(plan_path.read_bytes())
    check_plan(plan,reference,run)
    for name,sha in m['required_sha256'].items():
        if digest(safe_path(ROOT,name))!=sha:raise ValueError('Prepared input changed: '+name)
    a=json.loads((preparation.parent/'audit-v1.json').read_bytes())
    if not a['accepted'] or a['manifest_sha256']!=PREP_SHA:raise ValueError('Preparation audit mismatch')
    rows={};snapshots=[preparation,plan_path,DEFAULT_PLAN,preparation.parent/'audit-v1.json']
    for split,e in m['files'].items():
        p=safe_path(preparation.parent,e['path'])
        if digest(p)!=e['sha256']:raise ValueError('Pending roots changed')
        rows[split]=[json.loads(line) for line in p.read_text().splitlines()]
        if len(rows[split])!=e['roots'] or any(r['split']!=split or r['teacher_cp'] is not None or r['outcome_loss_enabled'] for r in rows[split]):raise ValueError('Pending row mismatch')
        snapshots.append(p)
    if set(rows)!= {'train','validation'} or len(rows['train'])!=144 or len(rows['validation'])!=36:raise ValueError('Expected144/36')
    if digest(RUNTIME_MANIFEST)!=PREPARATION_SHA:raise ValueError('Isolated runtime manifest changed')
    rm=json.loads(RUNTIME_MANIFEST.read_bytes());entries=[e for e in rm['files'] if e['variant']=='baseline']
    if len(entries)!=7:raise ValueError('Expected seven isolated files')
    for e in entries:
        if e['source'] in plan['runtime_sha256'] and e['sha256']!=plan['runtime_sha256'][e['source']]:raise ValueError('Baseline mismatch')
        p=safe_path(RUNTIME_MANIFEST.parent,e['path'])
        if digest(p)!=e['sha256'] or p.stat().st_size!=e['bytes']:raise ValueError('Isolated baseline changed')
    probe=ROOT/'results/learning-tools/learning-data-probe'
    if digest(probe)!=plan['original_probe_sha256']:raise ValueError('Probe changed')
    snapshots.append(RUNTIME_MANIFEST)
    return plan,m,rows,entries,list(dict.fromkeys(snapshots)),probe

def run(preparation,plan_path,output,*,execute=False):
    plan,m,rows,entries,snapshots,probe_path=load_binding(preparation,plan_path,execute)
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in ignored results')
    output.mkdir(parents=True,exist_ok=False)
    if execute:
        with (Path(preparation).resolve().parent/'teacher-generation-attempt-v1.json').open('x') as f:
            json.dump(dict(output=str(output.relative_to(ROOT)),preparation_sha256=PREP_SHA),f)
    inputs=[]
    for index,source in enumerate(snapshots):
        target=output/'inputs'/f'{index:02d}-{source.name}'
        sha=digest(source);copy_verified(source,target,sha)
        inputs.append(dict(source=str(source.relative_to(ROOT)),copy=str(target.relative_to(output)),sha256=sha))
    dependencies=('pair_teacher_generation.py','audit_refreshed_teachers.py','refresh_teachers.py','prepare_tempo_search.py','analyze_positions.py',
                  'prepare_learning_data.py','learning_backup.py','run_tempo_search.py')
    report=dict(schema='rakuyou-teacher-refresh-run-v1',mode='run' if execute else 'dry-run',
                started_at=now(),finished_at=None,preparation_sha256=PREP_SHA,
                plan_sha256=digest(plan_path),input_copies=inputs,runtime_files=entries,
                runtime_sha256=plan['runtime_sha256'],settings=plan['search'],
                harness_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                harness_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
                tool_sha256={n:digest(ROOT/'tools'/n) for n in dependencies},probe_sha256=digest(probe_path),
                environment=dict(system=platform.system(),machine=platform.machine(),python=platform.python_version()),
                attempted_searches=0,completed_searches=0,validated_roots=0,generated_teachers=0,
                real_data_updates=0,deployed=False,training_ready=False,teacher_generation_complete=False,
                test_roots_selected=0,records=[],errors=[])
    report_path=output/'report.json';write_report(report_path,report)
    probe=Probe(probe_path);streams={}
    engine_path=RUNTIME_MANIFEST.parent/'baseline/bin/release'
    try:
        for split in rows:streams[split]=(output/f'{split}.teachers.jsonl').open('x')
        if not execute:
            engine=RecordedEngine(engine_path)
            try:
                if any('failed' in l.lower() or 'error' in l.lower() for l in engine.transcript):raise ValueError('Runtime loading error')
            finally:engine.close()
            report['readiness']=dict(commands=engine.commands,transcript=engine.transcript)
        for split in ('train','validation'):
            for row in rows[split]:
                check_root(row,probe);report['validated_roots']+=1
                record={**row,'schema':'rakuyou-refreshed-teacher-v1','teacher_status':'not-generated',
                        'teacher_cp':None,'teacher_origin':plan['teacher']['origin'],
                        'perspective':'root-side-to-move','binding_report':'report.json'}
                if execute:
                    print(f"[{report['attempted_searches']+1}/180] {split} {row['id']}",flush=True)
                    engine=RecordedEngine(engine_path)
                    try:
                        if any('failed' in l.lower() or 'error' in l.lower() for l in engine.transcript):raise ValueError('Runtime loading error')
                        report['attempted_searches']+=1;write_report(report_path,report)
                        result=engine.analyze(row['moves_before'],15,30,multipv=1)
                        record['analysis']=result
                        cp,reason=classify(result,row,probe)
                        record.update(teacher_cp=cp,excluded=reason,teacher_status='accepted' if reason is None else 'excluded')
                        report['completed_searches']+=1
                        if cp is not None:report['generated_teachers']+=1
                    except Exception as error:
                        record.update(teacher_status='failed',failure=dict(type=type(error).__name__,message=str(error)))
                        raise
                    finally:
                        engine.close();record['commands']=engine.commands;record['transcript']=engine.transcript
                        streams[split].write(json.dumps(record,ensure_ascii=False,sort_keys=True)+'\n');streams[split].flush()
                        report['records'].append(record);write_report(report_path,report)
                else:
                    streams[split].write(json.dumps(record,ensure_ascii=False,sort_keys=True)+'\n');streams[split].flush()
                    report['records'].append(record)
        load_binding(preparation,plan_path,execute)
        for e in inputs:
            if digest(ROOT/e['source'])!=e['sha256'] or digest(output/e['copy'])!=e['sha256']:raise ValueError('Input/copy changed')
        report['runtime_unchanged']=True
        report['teacher_generation_complete']=execute and report['completed_searches']==180
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error)))
        raise
    finally:
        probe.close()
        for stream in streams.values():stream.close()
        report['files']={s:dict(path=f'{s}.teachers.jsonl',sha256=digest(output/f'{s}.teachers.jsonl')) for s in streams}
        report['summary']={s:dict(Counter(r['teacher_status'] for r in report['records'] if r['split']==s)) for s in rows}
        report['finished_at']=now();write_report(report_path,report)
    print(json.dumps({k:report[k] for k in ('mode','validated_roots','attempted_searches','generated_teachers','summary')},indent=2))
    return report



def audit(report_path,output):
    report_path=Path(report_path).resolve();output=Path(output)
    if output.exists():raise FileExistsError(output)
    r=json.loads(report_path.read_bytes())
    if (r['schema']!='rakuyou-teacher-refresh-run-v1' or r['mode']!='run' or r['errors'] or
        not r['teacher_generation_complete'] or r['attempted_searches']!=180 or r['completed_searches']!=180 or
        r['real_data_updates']!=0 or r['deployed'] is not False or r['training_ready'] is not False):
        raise ValueError('Expected complete, untrained/undeployed generation')
    for n,sha in r['tool_sha256'].items():
        if digest(ROOT/'tools'/n)!=sha:raise ValueError('Generation tool changed')
    for e in r['input_copies']:
        if digest(ROOT/e['source'])!=e['sha256'] or digest(report_path.parent/e['copy'])!=e['sha256']:
            raise ValueError('Input/copy SHA mismatch')
    prep=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['preparation_sha256'])
    plan=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['plan_sha256'])
    bound_plan,_,pending,entries,_,probe_path=load_binding(prep,plan,True)
    if (r['settings']!=bound_plan['search'] or r['runtime_sha256']!=bound_plan['runtime_sha256'] or
            r['runtime_files']!=entries or r['probe_sha256']!=digest(probe_path) or r['validated_roots']!=180):
        raise ValueError('Reported runtime/settings/probe differs from actual binding')
    known={x['id']:x for rows in pending.values() for x in rows}
    seen=set();records=[]
    for split,e in r['files'].items():
        path=report_path.parent/e['path']
        if digest(path)!=e['sha256']:raise ValueError('Teacher file SHA mismatch')
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if rows!=[x for x in r['records'] if x['split']==split]:raise ValueError('Report/JSONL mismatch')
        records.extend(rows)
    if len(records)!=180 or {x['id'] for x in records}!=set(known):raise ValueError('Root membership mismatch')
    probe=Probe(probe_path);summary={}
    try:
        for record in records:
            if record['id'] in seen:raise ValueError('Duplicate teacher')
            seen.add(record['id'])
            if record['teacher_origin']!=bound_plan['teacher']['origin']:
                raise ValueError('Reported teacher origin changed')
            audit_record(record,known[record['id']],probe)
        for split in ('train','validation'):
            rows=[x for x in records if x['split']==split]
            summary[split]=dict(roots=len(rows),status=dict(Counter(x['teacher_status'] for x in rows)),
                exclusions=dict(Counter(x['excluded'] for x in rows if x['excluded'] is not None)),
                accepted_strata=dict(Counter(x['stratum'] for x in rows if x['teacher_status']=='accepted')),
                accepted_draws=sum(x['teacher_status']=='accepted' and x['stratum'].endswith(':draw') for x in rows),
                accepted_white_draws=sum(x['teacher_status']=='accepted' and x['stratum']=='white:draw' for x in rows))
    finally:probe.close()
    accepted=sum(x['teacher_status']=='accepted' for x in records)
    if accepted!=r['generated_teachers']:raise ValueError('Generated count mismatch')
    load_binding(prep,plan,True)
    out=dict(schema='rakuyou-refreshed-teacher-audit-v1',generation_report_sha256=digest(report_path),
             audit_tool_sha256=digest(Path(__file__)),roots_checked=180,native_root_pv_replays=180,
             accepted=accepted,excluded=180-accepted,summary=summary,teacher_provenance_verified=True,
             searches_executed=0,real_data_updates=0,training_ready=False,deployed=False)
    with output.open('x') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(out['summary'],indent=2))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--plan',type=Path,default=DEFAULT_PLAN);p.add_argument('--run',action='store_true');p.add_argument('--audit',type=Path)
    args=p.parse_args()
    if args.audit:
        if args.run:p.error('Audit cannot search')
        audit(args.audit,args.output)
    else:run(PREP,args.plan,args.output,execute=args.run)
