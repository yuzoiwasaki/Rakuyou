#!/usr/bin/env python3
"""One fixed root, two fixed moves, depth15/20 MultiPV2 under two fixed evaluations."""
import sys,json
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,digest,Probe
from tools.learning.data.refresh_teachers import RecordedEngine,RUNTIME_MANIFEST,check_root
from tools.learning.tempo.run_tempo_search import write_report
from tools.learning.core.learning_backup import create_backup,verify_backup
from tools.analysis.audit_white_positions import Board

PARENT=ROOT/'results/learning-pilot/2026-10-13-outcome-search-review-v1'
REPORT_SHA='d96d50ff65cc9b5b68905de49f85a957a2d204130b1df2e59454baf4af71d7e0'
PARAM_SHA='4e4c73c77060b7a40e782c9daf189a67bcb7acb1fc571f34af7acd59f22f4ed5'
MOVES=('7a8b','4a5b')
MARKER=PARENT/'king-gold-comparison-attempt-v1.json'


def validate_result(result,depth):
    if result['stopped_early'] or len(result['candidates'])!=2:raise ValueError('Incomplete two-move comparison')
    seen=set()
    for c in result['candidates']:
        if c['depth']!=depth or c['score_type']!='cp' or not c['pv'] or any(x in c['raw'].split() for x in ('lowerbound','upperbound')) or abs(int(c['score']))>=31000:
            raise ValueError('Incomplete/bounded/special candidate')
        seen.add(c['pv'][0])
    if seen!=set(MOVES) or result['bestmove']!=result['candidates'][0]['pv'][0]:raise ValueError('Fixed root moves changed')


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Comparison already started/closed')
    if digest(PARENT/'report.json')!=REPORT_SHA or digest(PARENT/'candidate/bin/params.bin')!=PARAM_SHA:raise ValueError('Fixed root/candidate changed')
    parent=json.loads((PARENT/'report.json').read_bytes())
    for n,s in parent['plan']['required_sha256'].items():
        if digest(ROOT/n)!=s:raise ValueError('Parent inputs changed')
    for copy in parent['export']['copies']:
        if digest(ROOT/copy['path'])!=copy['sha256']:raise ValueError('Isolated candidate runtime changed')
    roots=[r for r in parent['plan']['roots'] if r['stratum']=='white:black_win']
    if len(roots)!=1 or roots[0]['id']!='dce17654046bb8b5eac19f023830a2d55915c8273ba072eaf7e2681150e45f9b:23:32':raise ValueError('Fixed root changed')
    root=roots[0];row=root['row'];output.mkdir(parents=True,exist_ok=False)
    required=dict(parent['plan']['required_sha256'])
    for p in [PARENT/'report.json',PARENT/'audit.json',PARENT/'candidate/bin/params.bin',Path(__file__),ROOT/'test/learning/outcome/test_king_gold_comparison.py']:
        required[str(p.relative_to(ROOT))]=digest(p)
    plan=dict(root=root,moves=list(MOVES),depths=[15,20],variants=['baseline','candidate'],multipv=2,threads=1,hash_mb=64,
        timeout_seconds=30,max_searches=4,retries=0,refill=False,shin=True,own_book=False,
        updates=0,deployment_enabled=False,required_sha256=required)
    write_report(output/'plan.json',plan)
    with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json')),f)
    r=dict(plan=plan,records=[],attempted=0,completed=0,errors=[],closed=False,updates=0,qsearch_calls=0,deployed=False)
    legal=Probe(ROOT/'results/learning-tools/learning-data-probe')
    try:
        check_root(row,legal)
        for depth in plan['depths']:
            for variant in plan['variants']:
                binary=RUNTIME_MANIFEST.parent/'baseline/bin/release' if variant=='baseline' else PARENT/'candidate/bin/release'
                print(depth,variant,flush=True);engine=RecordedEngine(binary)
                try:
                    if any('error' in l.lower() or 'failed' in l.lower() for l in engine.transcript):raise ValueError('Runtime load error')
                    engine.send('setoption name MultiPV value 2');engine.send('isready');engine.wait_for('readyok',30)
                    r['attempted']+=1;write_report(output/'report.json',r)
                    result=engine.analyze(row['moves_before'],depth,30,searchmoves=list(MOVES),multipv=2)
                    validate_result(result,depth)
                    for c in result['candidates']:
                        replay=legal.replay(row['moves_before']+c['pv'])
                        if not replay.get('ok') or any(p['occurrences']>1 for p in replay['positions']):raise ValueError('Illegal/repeated PV')
                finally:engine.close()
                r['completed']+=1;r['records'].append(dict(depth=depth,variant=variant,result=result,commands=engine.commands,transcript=engine.transcript))
                write_report(output/'report.json',r)
        # Cross-score identical saved PV endpoints, statically only, to separate
        # small coefficient changes from different search trees.
        static={v:Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin' if v=='baseline' else PARENT/'candidate/bin/params.bin',details=True) for v in plan['variants']}
        endpoints=[]
        try:
            for record in r['records']:
                for c in record['result']['candidates']:
                    moves=row['moves_before']+c['pv'];values={v:probe.replay(moves)['positions'][-1] for v,probe in static.items()}
                    if values['baseline']['sfen']!=values['candidate']['sfen']:raise ValueError('Endpoint identity mismatch')
                    sign=1 if values['baseline']['sfen'].split()[1]=='w' else -1
                    changes=sign*(values['candidate']['eval_on']-values['baseline']['eval_on'])
                    if abs(changes)>10:raise ValueError('Identical-position delta bound')
                    board=Board()
                    for m in row['moves_before']:board.push(m)
                    material=[]
                    for m in c['pv']:
                        material.append(dict(move=m,piece=m[0] if m[1]=='*' else board.pieces[m[:2]],captured=board.pieces.get(m[2:4])))
                        board.push(m)
                    endpoints.append(dict(depth=record['depth'],variant=record['variant'],root_move=c['pv'][0],
                        static_baseline_cp=sign*values['baseline']['eval_on'],static_candidate_cp=sign*values['candidate']['eval_on'],
                        static_change=changes,sfen=values['baseline']['sfen'],moves_and_captures=material))
        finally:
            for probe in static.values():probe.close()
        r['endpoints']=endpoints
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        r['closed']=True
    except Exception as e:r['errors'].append(str(e));r['closed']=True;raise
    finally:legal.close();write_report(output/'report.json',r)
    return r

if __name__=='__main__':run(Path(sys.argv[1]))
