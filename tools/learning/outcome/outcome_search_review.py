#!/usr/bin/env python3
"""Fixed20 outcome candidate: six result/side strata x two depth15 searches."""
import sys,json,subprocess
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.outcome import outcome_pilot as pilot
from tools.learning.imitation.imitation_search_review import choose,audit_bytes,EXPORT
from tools.learning.data.prepare_learning_data import ROOT,digest,Probe
from tools.learning.data.refresh_teachers import RecordedEngine,classify,RUNTIME_MANIFEST
from tools.learning.tempo.run_tempo_search import PREPARATION_SHA,write_report
from tools.learning.tempo.prepare_tempo_search import copy_verified

RUN=ROOT/'results/learning-pilot/2026-10-13-outcome-run-v1'
RUN_SHA='e35097e34aa32eaafea939f2f04870bf5f6a5ea213a8ab97cd612b37db03c8bc'
AUDIT_SHA='1478201f8a9e7b77c14c0053876318c7e1b8c8da3d336d338d492b463e6bb4cc'
DELTA_SHA='81ed1ad3a9b37827df31be85e4617d2dc39a96d311db3bd70853cb964dc474d3'
MARKER=RUN/'normal-search-review-attempt-v1.json'
ZERO=ROOT/'results/learning-pilot/2026-10-12-imitation-search-review-v1/params-zero.bin'


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Outcome normal review already started/closed')
    for name,sha in [('report.json',RUN_SHA),('audit.json',AUDIT_SHA),('average-20.txt',DELTA_SHA)]:
        if digest(RUN/name)!=sha:raise ValueError('Fixed outcome candidate changed')
    old=json.loads((RUN/'report.json').read_bytes())
    if old['selected_update']!=20 or not old['closed'] or old['errors']:raise ValueError('Expected audited20')
    for line in (RUN/'average-20.txt').read_text().splitlines():
        if abs(int(line.split()[-1]))>655:raise ValueError('Coefficient cap')
    prep=pilot.load();roots=[dict(id=r['id'],row=r['row'],stratum=r['row']['stratum']) for r in choose(prep['records']['validation'])]
    if len(roots)!=6:raise ValueError('Need fixed six strata')
    if digest(RUNTIME_MANIFEST)!=PREPARATION_SHA:raise ValueError('Baseline manifest changed')
    runtime=json.loads(RUNTIME_MANIFEST.read_bytes());entries=[e for e in runtime['files'] if e['variant']=='baseline']
    build=json.loads((EXPORT.parent/'build.json').read_bytes())
    if digest(EXPORT)!=build['binary_sha256'] or digest(EXPORT.parent/'export.cc')!=build['generated_sha256']:raise ValueError('Frozen exporter changed')
    if digest(ZERO)!=prep['required_sha256']['bin/params.bin']:raise ValueError('Preserved zero export differs')
    output.mkdir(parents=True,exist_ok=False)
    required=dict(old['binding']['required_sha256'])
    for p in [RUN/'report.json',RUN/'audit.json',RUN/'average-20.txt',ZERO,EXPORT,EXPORT.parent/'build.json',EXPORT.parent/'export.cc',Path(__file__),
        ROOT/'tools/learning/imitation/imitation_search_review.py',ROOT/'tools/learning/data/refresh_teachers.py',ROOT/'tools/analysis/analyze_positions.py']:
        required[str(p.relative_to(ROOT))]=digest(p)
    plan=dict(candidate_sha256=DELTA_SHA,selected_update=20,roots=roots,
        selection='one per six existing side/result strata, minSHA256(20261011:id); no improvement/score/feature selection',
        depth=15,threads=1,hash_mb=64,timeout_seconds=30,multipv=1,shin=True,own_book=False,
        max_searches=12,retries=0,refill=False,updates=0,deployment_enabled=False,
        variants=['baseline','candidate'],required_sha256=required)
    write_report(output/'plan.json',plan)
    with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json')),f)
    candidate=output/'candidate/bin/params.bin';candidate.parent.mkdir(parents=True)
    layout=json.loads(subprocess.check_output([str(EXPORT),str(ROOT/'bin/params.bin'),str(RUN/'average-20.txt'),str(candidate)],text=True))
    changed=audit_bytes(ROOT/'bin/params.bin',candidate,layout);copies=[]
    for e in entries:
        source=RUNTIME_MANIFEST.parent/e['path']
        if digest(source)!=e['sha256']:raise ValueError('Baseline copy changed')
        if e['source']=='bin/params.bin':continue
        target=output/'candidate'/e['path'].removeprefix('baseline/')
        copy_verified(source,target,e['sha256']);copies.append(dict(path=str(target.relative_to(ROOT)),sha256=e['sha256']))
    if digest(output/'candidate/bin/release')!=prep['required_sha256']['bin/release']:raise ValueError('Engine binary differs')
    static=Probe(ROOT/'results/learning-tools/learning-data-probe',candidate,details=True)
    try:
        expected={x['id']:x for rows in old['saved'][-1]['observations'].values() for x in rows};checked=0
        for rows in prep['records'].values():
            for r in rows:
                replay=static.replay(r['row']['moves_before'])
                if not replay.get('ok') or replay['positions'][-1]['eval_on']!=expected[r['id']]['candidate_cp']:raise ValueError('Export differs from saved20')
                checked+=1
    finally:static.close()
    export=dict(layout=layout,changed_bytes=changed,candidate_sha256=digest(candidate),zero_export_source=str(ZERO.relative_to(ROOT)),
        zero_export_sha256=digest(ZERO),static_histories=checked,copies=copies)
    write_report(output/'export-audit.json',export)
    r=dict(plan=plan,export=export,records=[],errors=[],attempted=0,completed=0,closed=False,updates=0,qsearch_calls=0,deployed=False)
    legal=Probe(ROOT/'results/learning-tools/learning-data-probe')
    try:
        for root in roots:
            for variant in plan['variants']:
                print(root['stratum'],variant,flush=True)
                binary=RUNTIME_MANIFEST.parent/'baseline/bin/release' if variant=='baseline' else output/'candidate/bin/release'
                e=RecordedEngine(binary)
                try:
                    if any('error' in l.lower() or 'failed' in l.lower() for l in e.transcript):raise ValueError('Engine load error')
                    r['attempted']+=1;write_report(output/'report.json',r)
                    result=e.analyze(root['row']['moves_before'],15,30);cp,reason=classify(result,root['row'],legal)
                finally:e.close()
                r['completed']+=1;r['records'].append(dict(id=root['id'],stratum=root['stratum'],variant=variant,
                    result=result,cp=cp,excluded=reason,commands=e.commands,transcript=e.transcript))
                write_report(output/'report.json',r)
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        for c in copies:
            if digest(ROOT/c['path'])!=c['sha256']:raise ValueError('Isolated file changed')
        if digest(candidate)!=export['candidate_sha256']:raise ValueError('Export changed')
        r['closed']=True
    except Exception as e:r['errors'].append(str(e));r['closed']=True;raise
    finally:legal.close();write_report(output/'report.json',r)
    print('Completed six roots x baseline/candidate, no learning.');return r

if __name__=='__main__':run(Path(sys.argv[1]))
