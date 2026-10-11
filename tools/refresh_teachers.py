#!/usr/bin/env python3
"""Runtime-bound teacher generation; default search-zero dry-run, no learning."""
import argparse
import json
import platform
import subprocess
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

from prepare_learning_data import ROOT,Probe,digest
from prepare_tempo_search import ReadyEngine,copy_verified
from run_tempo_search import PREPARATION_SHA,write_report
from learning_backup import safe_path

PREP_SHA='a4662b0f349560cfa3f03b2fef536d5c6000f9e4d5ee6b75a569f306ed9be5fc'
DEFAULT_PLAN=ROOT/'docs/experiments/configs/teacher-refresh-v1.json'
RUNTIME_MANIFEST=ROOT/'results/learning-pilot/2026-10-11-full-search-preparation-v1/manifest.json'


def now():return datetime.now(timezone.utc).isoformat()


def check_plan(plan,reference,run):
    expected=dict(reference)
    expected['teacher_search_enabled']=run
    if plan!=expected or plan['real_data_training_enabled'] or plan['deployment_enabled']:
        raise ValueError('Expected fixed plan with teacher-search flag matching requested mode')


def load_binding(preparation,plan_path,run):
    preparation=Path(preparation).resolve();plan_path=Path(plan_path).resolve()
    if digest(preparation)!=PREP_SHA:raise ValueError('Teacher preparation SHA mismatch')
    m=json.loads(preparation.read_bytes())
    if digest(DEFAULT_PLAN)!=m['plan_sha256']:raise ValueError('Reference plan changed')
    reference=json.loads(DEFAULT_PLAN.read_bytes());plan=json.loads(plan_path.read_bytes())
    check_plan(plan,reference,run)
    rows={};snapshots=[preparation,plan_path,DEFAULT_PLAN]
    for split,e in m['files'].items():
        p=safe_path(preparation.parent,e['path'])
        if digest(p)!=e['sha256']:raise ValueError('Pending roots changed')
        rows[split]=[json.loads(line) for line in p.read_text().splitlines()]
        if len(rows[split])!=e['roots']:raise ValueError('Pending row count mismatch')
        if any(r['split']!=split or r['teacher_cp'] is not None or r['outcome_loss_enabled'] for r in rows[split]):
            raise ValueError('Expected pending, outcome-masked roots')
        snapshots.append(p)
    if set(rows)!= {'train','validation'} or len(rows['train'])!=36 or len(rows['validation'])!=18:
        raise ValueError('Expected 36 train and 18 validation roots')
    if m['runtime_sha256']!=plan['runtime_sha256']:raise ValueError('Preparation/runtime binding differs')
    if digest(RUNTIME_MANIFEST)!=PREPARATION_SHA:raise ValueError('Isolated runtime manifest changed')
    rm=json.loads(RUNTIME_MANIFEST.read_bytes())
    entries=[e for e in rm['files'] if e['variant']=='baseline']
    if len(entries)!=7:raise ValueError('Expected seven isolated runtime files')
    runtime={n:digest(ROOT/n) for n in plan['runtime_sha256']}
    if runtime!=plan['runtime_sha256']:raise ValueError('Operational runtime changed')
    for e in entries:
        if e['source'] in runtime and e['sha256']!=runtime[e['source']]:raise ValueError('Baseline identity mismatch')
        p=safe_path(RUNTIME_MANIFEST.parent,e['path'])
        if digest(p)!=e['sha256'] or p.stat().st_size!=e['bytes']:raise ValueError('Isolated baseline changed')
    probe_path=ROOT/'results/learning-tools/learning-data-probe'
    if digest(probe_path)!=plan['probe_sha256']:raise ValueError('Probe identity mismatch')
    snapshots.append(RUNTIME_MANIFEST)
    return plan,m,rows,entries,list(dict.fromkeys(snapshots)),probe_path


class RecordedEngine(ReadyEngine):
    def __init__(self,path):
        self.commands=[]
        super().__init__(path)

    def send(self,command):
        self.commands.append(command)
        super().send(command)

    def close(self):
        super().close()
        if self.process.poll() is None:
            self.process.kill();self.process.wait(timeout=5)


def check_root(row,probe):
    replay=probe.replay(row['moves_before'])
    if not replay.get('ok'):raise ValueError('Illegal root history')
    root=replay['positions'][-1]
    if root['sfen']!=row['sfen'] or root['huffman_hex']!=row['huffman_hex']:raise ValueError('Root identity mismatch')
    if any(p['occurrences']>1 for p in replay['positions']):raise ValueError('Repeated root history')


def classify(result,row,probe):
    if result['stopped_early']:raise ValueError('Stopped search')
    candidates=result['candidates']
    if result['bestmove'] in ('resign','win'):return None,'special_terminal'
    if len(candidates)!=1:raise ValueError('Missing single-PV result')
    c=candidates[0]
    if not c['pv'] or result['bestmove']!=c['pv'][0]:raise ValueError('Bestmove/PV mismatch')
    replay=probe.replay(row['moves_before']+c['pv'])
    if not replay.get('ok'):raise ValueError('Illegal teacher PV')
    if c['score_type']=='mate':return None,'mate_score'
    if c['depth']!=15:raise ValueError('Incomplete depth15 search')
    if any(w in c['raw'].split() for w in ('lowerbound','upperbound')):return None,'bounded_score'
    if c['score_type']!='cp':return None,'non_cp_score'
    cp=int(c['score'])
    if abs(cp)>=31000:return None,'known_win_score'
    if any(p['occurrences']>1 for p in replay['positions']):return None,'repeated_root_or_pv_history'
    return cp,None


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
    dependencies=('refresh_teachers.py','prepare_tempo_search.py','analyze_positions.py',
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
                    print(f"[{report['attempted_searches']+1}/54] {split} {row['id']}",flush=True)
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
        report['teacher_generation_complete']=execute and report['completed_searches']==54
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


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('preparation',type=Path);p.add_argument('--plan',type=Path,default=DEFAULT_PLAN)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--run',action='store_true')
    a=p.parse_args();run(a.preparation,a.plan,a.output,execute=a.run)


if __name__=='__main__':main()
