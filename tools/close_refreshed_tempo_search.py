#!/usr/bin/env python3
"""Final bounded tempo diagnostics: 36 QS calls and 12 depth15 searches. No tuning."""
import argparse
import json
from pathlib import Path
from prepare_learning_data import ROOT,Probe,digest
from prepare_refreshed_pilot import load_refreshed
from prepare_tempo_search import copy_verified
from refresh_teachers import RecordedEngine,classify,RUNTIME_MANIFEST
from check_selected_qsearch import compare_frames,summarize
from run_tempo_search import write_report

PILOT_SHA='88733fd21826476f77e861dcd451105f01e1453a23563505ef33f87d9f8f3a3d'


def select_normal(rows):
    chosen=[];seen=set()
    for row in rows:
        if row['stratum'] not in seen:chosen.append(row);seen.add(row['stratum'])
    if len(chosen)!=6:raise ValueError('Expected six validation strata')
    return chosen


def normal_difference(a,b):
    return dict(bestmove_changed=a['analysis']['bestmove']!=b['analysis']['bestmove'],
                pv_changed=[c['pv'] for c in a['analysis']['candidates']]!=[c['pv'] for c in b['analysis']['candidates']],
                cp_change=b['cp']-a['cp'] if a['cp'] is not None and b['cp'] is not None else None)


def run(pilot_path,generation_path,audit_path,output):
    pilot_path=Path(pilot_path).resolve()
    if digest(pilot_path)!=PILOT_SHA:raise ValueError('Selected pilot SHA mismatch')
    pilot=json.loads(pilot_path.read_bytes())
    if pilot['selected_update']!=20 or pilot['real_data_updates']!=20 or pilot['deployed'] or not pilot['closed'] or pilot['errors']:
        raise ValueError('Expected completed selected20 pilot')
    selected=next(x for x in pilot['saved'] if x['update']==20)
    candidate=pilot_path.parent/'params-average-20.bin'
    if digest(candidate)!=selected['export']['candidate_sha256']:raise ValueError('Selected candidate changed')
    generation,parts,_,probe_path=load_refreshed(generation_path,audit_path)
    rows=parts['validation'];normal_rows=select_normal(rows)
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    with (pilot_path.parent/'selected-final-search-attempt-v1.json').open('x') as f:
        json.dump(dict(output=str(output.relative_to(ROOT)),pilot_sha256=PILOT_SHA),f)
    rm=json.loads(RUNTIME_MANIFEST.read_bytes());files=[]
    for e in rm['files']:
        if e['variant']!='baseline':continue
        relative=Path(e['path']).relative_to('baseline')
        source=RUNTIME_MANIFEST.parent/e['path']
        if digest(source)!=e['sha256']:raise ValueError('Baseline sidecar changed')
        expected=e['sha256']
        if relative.as_posix()=='bin/params.bin':source=candidate;expected=selected['export']['candidate_sha256']
        target=output/'candidate'/relative;copy_verified(source,target,expected)
        files.append(dict(path=str(target.relative_to(output)),sha256=expected))
    report=dict(schema='rakuyou-refreshed-tempo-final-search-v1',pilot_sha256=PILOT_SHA,
                selected_update=20,candidate_sha256=digest(candidate),runtime_sha256=generation['runtime_sha256'],
                candidate_files=files,qs_calls=0,normal_searches=0,real_data_updates=0,
                deployed=False,test_roots_selected=0,qs_records=[],normal_records=[],errors=[],closed=False,
                normal_settings=dict(depth=15,multipv=1,threads=1,hash_mb=64,timeout_seconds=30,
                                     ShinYonenagaGyoku=True,OwnBook=False,Ponder=False,fresh_process=True),
                tool_sha256=digest(Path(__file__)),probe_sha256=digest(probe_path))
    path=output/'report.json';write_report(path,report)
    base=Probe(probe_path,ROOT/'bin/params.bin',qsearch_progress=ROOT/'bin/progress.bin')
    trial=Probe(probe_path,candidate,qsearch_progress=ROOT/'bin/progress.bin')
    try:
        try:
            for row in rows:
                report['qs_calls']+=1;a=base.replay(row['moves_before'])
                report['qs_calls']+=1;b=trial.replay(row['moves_before'])
                report['qs_records'].append(compare_frames(row,a,b));write_report(path,report)
        finally:base.close();trial.close()
        report['qs_summary']=summarize(report['qs_records'])
        native=Probe(probe_path)
        try:
            for i,row in enumerate(normal_rows):
                record=dict(id=row['id'],stratum=row['stratum'],analyses={});report['normal_records'].append(record)
                order=('baseline','candidate') if i%2==0 else ('candidate','baseline')
                for variant in order:
                    engine_path=RUNTIME_MANIFEST.parent/'baseline/bin/release' if variant=='baseline' else output/'candidate/bin/release'
                    print(f"[{report['normal_searches']+1}/12] {row['stratum']} {variant}",flush=True)
                    engine=RecordedEngine(engine_path)
                    try:
                        if any('failed' in l.lower() or 'error' in l.lower() for l in engine.transcript):raise ValueError('Loading error')
                        report['normal_searches']+=1;write_report(path,report)
                        analysis=engine.analyze(row['moves_before'],15,30,multipv=1)
                        cp,reason=classify(analysis,row,native)
                        record['analyses'][variant]=dict(analysis=analysis,cp=cp,excluded=reason)
                    finally:
                        engine.close()
                    record['analyses'][variant].update(commands=engine.commands,transcript=engine.transcript)
                    write_report(path,report)
                record['comparison']=normal_difference(record['analyses']['baseline'],record['analyses']['candidate'])
                write_report(path,report)
        finally:native.close()
        load_refreshed(generation_path,audit_path)
        for f in files:
            if digest(output/f['path'])!=f['sha256']:raise ValueError('Candidate sidecar changed')
        if digest(candidate)!=report['candidate_sha256']:raise ValueError('Selected params changed')
        report['runtime_unchanged']=True;report['closed']=True
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error)));report['closed']=True
        raise
    finally:write_report(path,report)
    print(json.dumps(report['qs_summary'],indent=2))
    print(json.dumps([x['comparison'] for x in report['normal_records']],indent=2));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pilot',type=Path);p.add_argument('generation',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.pilot,a.generation,a.audit,a.output)
