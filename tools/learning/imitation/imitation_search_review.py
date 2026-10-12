#!/usr/bin/env python3
"""Fixed20 imitation candidate:12 roots x baseline/candidate depth15; no learning."""
import sys,json,hashlib,subprocess,struct
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,digest,Probe
from tools.learning.data.refresh_teachers import RecordedEngine,classify,RUNTIME_MANIFEST
from tools.learning.tempo.prepare_tempo_search import copy_verified
from tools.learning.tempo.run_tempo_search import write_report,PREPARATION_SHA
from tools.learning.imitation import imitation_pilot as pilot

RUN=ROOT/'results/learning-pilot/2026-10-12-imitation-run-v1'
RUN_SHA='8738582ae7a3590e87140b240b905a458510d1af6f11d7d4c34f2edee6845707'
AUDIT_SHA='ced22e4266f2a2208476d2ba99ed2ff6ae84a740be5b7b6d6c40600d5ebacabd'
CANDIDATE_SHA='e13e34bcfd26ba99e5baf3a65bb15f1684685ab882bb102706b5fe3e367c5e8b'
EXPORT=ROOT/'results/imitation-export-tools/export'


def choose(records):
    # All six preexisting side/result strata receive one root; no score/PV/
    # feature/improvement ranks used. Original validation remains a reused diagnostic.
    return [min([r for r in records if r['row']['stratum']==s],key=lambda r:hashlib.sha256(('20261011:'+r['row']['id']).encode()).hexdigest())
        for s in sorted({r['row']['stratum'] for r in records})]


def audit_bytes(base,candidate,layout):
    changed=0
    with Path(base).open('rb') as a,Path(candidate).open('rb') as b:
        offset=0
        while True:
            x=a.read(65536);y=b.read(65536)
            if not x and not y:break
            if len(x)!=len(y):raise ValueError('Parameter size changed')
            if x!=y:
                for index,(old,new) in enumerate(zip(x,y)):
                    if old==new:continue
                    absolute=offset+index
                    if layout['kp_offset']<=absolute<layout['pp_offset']:
                        if (absolute-layout['kp_offset'])%16>=12:raise ValueError('Progress bytes changed')
                    elif layout['pp_offset']<=absolute<layout['controls_offset']:
                        if (absolute-layout['pp_offset'])%16 not in (0,1,2,3,8,9,10,11):raise ValueError('PP tempo bytes changed')
                    else:raise ValueError('Non-KP/PP parameter bytes changed')
                    changed+=1
            offset+=len(x)
    if offset!=layout['bytes']:raise ValueError('Layout bytes mismatch')
    return changed


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    for name,sha in [('report.json',RUN_SHA),('audit.json',AUDIT_SHA),('average-20.txt',CANDIDATE_SHA)]:
        if digest(RUN/name)!=sha:raise ValueError('Fixed20 candidate/run changed')
    for line in (RUN/'average-20.txt').read_text().splitlines():
        if abs(int(line.split()[-1]))>655:raise ValueError('Candidate coefficient cap changed')
    prep,_=pilot.verify_inputs()
    old=json.loads((RUN/'report.json').read_bytes())
    if old['selected_update']!=20 or old['errors'] or not old['closed']:raise ValueError('Expected closed20 run')
    if digest(RUNTIME_MANIFEST)!=PREPARATION_SHA:raise ValueError('Runtime binding changed')
    runtime=json.loads(RUNTIME_MANIFEST.read_bytes());entries=[e for e in runtime['files'] if e['variant']=='baseline']
    build=json.loads((EXPORT.parent/'build.json').read_bytes())
    if digest(EXPORT)!=build['binary_sha256'] or digest(EXPORT.parent/'export.cc')!=build['generated_sha256']:raise ValueError('Exporter changed')
    output.mkdir(parents=True,exist_ok=False)
    roots=[dict(id=p['id'],group='train',row=p['row']) for p in prep['pairs']]
    roots += [dict(id=p['row']['id'],group='diagnostic',row=p['row']) for p in choose(prep['validation'])]
    if len(roots)!=12:raise ValueError('Expected6train+6diagnostic')
    required=dict(old['binding']['required_sha256'])
    for path in [RUN/'report.json',RUN/'audit.json',RUN/'average-20.txt',EXPORT,EXPORT.parent/'export.cc',EXPORT.parent/'build.json',
        Path(__file__),ROOT/'tools/learning/imitation/build_imitation_export.py',ROOT/'tools/learning/data/refresh_teachers.py',ROOT/'tools/analysis/analyze_positions.py']:
        required[str(path.relative_to(ROOT))]=digest(path)
    plan=dict(selected_update=20,candidate_sha256=CANDIDATE_SHA,roots=roots,
        selection='six fixed training roots; one per six existing side/result strata by min SHA256(20261011:id), no score/feature selection',
        depth=15,threads=1,hash_mb=64,multipv=1,timeout_seconds=30,own_book=False,shin=True,
        variants=['baseline','candidate'],max_searches=24,retries=0,updates=0,
        learning_enabled=False,deployment_enabled=False,reselection_enabled=False,required_sha256=required)
    write_report(output/'plan.json',plan)
    with (RUN/'final-search-review-attempt-v1.json').open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json')),f)
    zero=output/'zero.txt';zero.write_text('')
    candidate=output/'candidate/bin/params.bin';candidate.parent.mkdir(parents=True)
    layout=json.loads(subprocess.check_output([str(EXPORT),str(ROOT/'bin/params.bin'),str(RUN/'average-20.txt'),str(candidate)],text=True))
    subprocess.run([str(EXPORT),str(ROOT/'bin/params.bin'),str(zero),str(output/'params-zero.bin')],check=True,capture_output=True,text=True)
    if digest(output/'params-zero.bin')!=digest(ROOT/'bin/params.bin'):raise ValueError('Zero export changed baseline')
    changed=audit_bytes(ROOT/'bin/params.bin',candidate,layout)
    copies=[]
    for e in entries:
        source=RUNTIME_MANIFEST.parent/e['path']
        if digest(source)!=e['sha256']:raise ValueError('Isolated baseline changed')
        if e['source']=='bin/params.bin':continue
        target=output/'candidate'/e['path'].removeprefix('baseline/')
        copy_verified(source,target,e['sha256']);copies.append(dict(path=str(target.relative_to(ROOT)),sha256=e['sha256']))
    if digest(output/'candidate/bin/release')!=prep['plan']['runtime_sha256']['bin/release']:raise ValueError('Engine differs from operational')
    points=json.loads((RUN/'baseline-locations.json').read_bytes())
    native=Probe(ROOT/'results/learning-tools/learning-data-probe',candidate,details=True)
    try:
        # Reuse the existing probe's supported --evaluate-details SFEN-free replay
        # path, using the actual recorded histories for all12 training leaves and
        # original35 validation roots/leaves. No new qsearch.
        checks=[]
        for pair in prep['pairs']:
            for label,branch in pair['branches'].items():checks.append((pair['id']+':'+label,branch['moves']))
        old_prep=json.loads((pilot.OLD/'report.json').read_bytes())
        for record in old_prep['records']['validation']:
            row=record['row'];checks.append((row['id']+':leaf',row['moves_before']+record['frame']['pv']))
            checks.append((row['id']+':root',row['moves_before']))
        for pair in prep['pairs']:checks.append((pair['id']+':root',pair['row']['moves_before']))
        expected={x['id']:x for x in old['saved'][-1]['observations']}
        for id,moves in checks:
            replay=native.replay(moves)
            if not replay.get('ok'):raise ValueError('Export static history failed')
            leaf=replay['positions'][-1];point=next(p for p in points if p['id']==id)
            sign=1 if (leaf['sfen'].split()[1]=='b')==(point['root_side']=='black') else -1
            if sign*leaf['eval_on']!=expected[id]['candidate_cp']:raise ValueError('Export differs from fixed candidate')
    finally:native.close()
    export_record=dict(layout=layout,changed_bytes=changed,zero_export_sha256=digest(output/'params-zero.bin'),
        candidate_sha256=digest(candidate),static_history_checks=len(checks),copies=copies)
    write_report(output/'export-audit.json',export_record)
    r=dict(plan=plan,export=export_record,records=[],errors=[],attempted=0,completed=0,updates=0,deployed=False,closed=False)
    probe=Probe(ROOT/'results/learning-tools/learning-data-probe')
    try:
        for root in roots:
            for variant in plan['variants']:
                print(root['id'],variant,flush=True)
                binary=RUNTIME_MANIFEST.parent/'baseline/bin/release' if variant=='baseline' else output/'candidate/bin/release'
                e=RecordedEngine(binary)
                try:
                    if any('failed' in line.lower() or 'error' in line.lower() for line in e.transcript):raise ValueError('Engine load error')
                    r['attempted']+=1;write_report(output/'report.json',r)
                    result=e.analyze(root['row']['moves_before'],15,30)
                    cp,reason=classify(result,root['row'],probe)
                finally:e.close()
                r['completed']+=1;r['records'].append(dict(id=root['id'],group=root['group'],variant=variant,result=result,
                    cp=cp,excluded=reason,commands=e.commands,transcript=e.transcript))
                write_report(output/'report.json',r)
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        for c in copies:
            if digest(ROOT/c['path'])!=c['sha256']:raise ValueError('Isolated file changed')
        if digest(candidate)!=export_record['candidate_sha256']:raise ValueError('Candidate file changed')
        r['closed']=True
    except Exception as e:r['closed']=True;r['errors'].append(str(e));raise
    finally:probe.close();write_report(output/'report.json',r)
    print('Completed12x2 normal searches, no learning or adoption.');return r

if __name__=='__main__':run(Path(sys.argv[1]))
