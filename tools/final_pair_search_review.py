#!/usr/bin/env python3
"""Fixed selected-5 candidate:35 re-QS roots and6 depth12 pairs, no learning."""
import argparse,json,os,hashlib
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from prepare_learning_data import ROOT,Probe,digest
from expanded_pair_pilot import load_records
from gold_silver_pair_pilot import PairProbe
from prepare_tempo_search import copy_verified
from refresh_teachers import RecordedEngine,RUNTIME_MANIFEST
from run_tempo_search import write_report
from king_safety_objective import sigmoid,GAIN

OUT=ROOT/'results/learning-pilot/2026-10-12-pair-final-review-v1'
TOOLS=ROOT/'results/pair-final-tools'
RUN=ROOT/'results/learning-pilot/2026-10-12-expanded-pair-run-v1'

@contextmanager
def raw_env(raw):
    keys=('RAKUYOU_PAIR_RAW_OPEN','RAKUYOU_PAIR_RAW_END');old={k:os.environ.get(k) for k in keys}
    try:
        for k,v in zip(keys,raw):os.environ[k]=str(v)
        yield
    finally:
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v


def choose(records):
    return [min([r for r in records if r['row']['stratum']==s],key=lambda r:hashlib.sha256(('20261011:'+r['row']['id']).encode()).hexdigest()) for s in sorted({r['row']['stratum'] for r in records})]


def run():
    old=json.loads((RUN/'report.json').read_bytes());audit=json.loads((RUN/'audit-v1.json').read_bytes())
    if audit['report_sha256']!=digest(RUN/'report.json') or not audit['accepted'] or old['selected_update']!=5:raise ValueError('Selected candidate changed')
    saved=next(s for s in old['saved'] if s['update']==5);candidate=RUN/'pair-average-05.json'
    if digest(candidate)!=saved['sidecar_sha256']:raise ValueError('Candidate changed')
    raw=json.loads(candidate.read_bytes())['raw']
    if raw!=[7457,7524]:raise ValueError('Fixed candidate raw mismatch')
    gen,parts,required=load_records();records=parts['validation'];normal=choose(records)
    if len(records)!=35 or len(normal)!=6:raise ValueError('Review scope changed')
    OUT.mkdir(parents=True,exist_ok=False)
    with (RUN/'final-search-review-attempt-v1.json').open('x') as f:json.dump(dict(output=OUT.relative_to(ROOT).as_posix(),candidate_sha256=digest(candidate)),f)
    for p in (RUN/'report.json',RUN/'audit-v1.json',candidate,TOOLS/'probe',TOOLS/'engine',TOOLS/'evaluation.cc',TOOLS/'build-manifest.json',Path(__file__),ROOT/'tools/build_pair_final_search.py'):
        required[p.relative_to(ROOT).as_posix()]=digest(p)
    build=json.loads((TOOLS/'build-manifest.json').read_bytes())
    for name,sha in build['source_sha256'].items():
        if digest(ROOT/name)!=sha:raise ValueError('Build source changed')
    m=json.loads(RUNTIME_MANIFEST.read_bytes());copies=[]
    for e in m['files']:
        if e['variant']!='baseline' or e['source']=='bin/release':continue
        rel=e['path'].removeprefix('baseline/')
        target=OUT/rel if rel.startswith('lib/') else OUT/'isolated'/rel
        source=RUNTIME_MANIFEST.parent/e['path'];copy_verified(source,target,e['sha256'])
        copies.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=e['sha256']))
    executable=OUT/'isolated/bin/release';copy_verified(TOOLS/'engine',executable,digest(TOOLS/'engine'))
    copies.append(dict(path=executable.relative_to(ROOT).as_posix(),sha256=digest(TOOLS/'engine')))
    plan=dict(candidate_sha256=digest(candidate),raw=raw,selected_update=5,validation_roots=35,
        normal_ids=[r['row']['id'] for r in normal],normal_selection='one per6strata; minimum SHA256(20261011:id); no results/features used',
        normal_depth=12,threads=1,hash_mb=64,timeout_seconds=30,multipv=1,own_book=False,shin=True,
        max_qsearch_calls=70,max_normal_searches=18,normal_variants=['operational_control','zero','candidate'],
        learning_enabled=False,reselection_enabled=False,deployment_enabled=False,required_sha256=required,copies=copies)
    write_report(OUT/'plan.json',plan)
    report=dict(plan=plan,qsearch=[],normal=[],errors=[],closed=False,updates=0,deployed=False)
    path=OUT/'report.json';write_report(path,report)
    static=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',details=True)
    try:
        for label,values in (('zero',[0,0]),('candidate',raw)):
            with raw_env(values):q=Probe(TOOLS/'probe',ROOT/'bin/params.bin',qsearch_progress=ROOT/'bin/progress.bin')
            pair=PairProbe(values)
            try:
                for record in records:
                    row,base=record['row'],record['frame'];f=q.replay(row['moves_before'])
                    if not f.get('ok') or f['leaf_eval_cached']!=f['leaf_eval_full']:raise ValueError('Qsearch/cached-full mismatch')
                    if label=='zero':
                        for key in ('qscore','nodes','pv','root_sfen','leaf_sfen','leaf_eval_full','leaf_progress','leaf_parts'):
                            if f[key]!=base[key]:raise ValueError('Zero QS differs from original: '+key)
                    replay=pair.replay(row['moves_before']+f['pv']);leaf=replay['positions'][-1]
                    if not replay['ok'] or leaf['sfen']!=f['leaf_sfen'] or leaf['eval_on']!=f['leaf_eval_full'] or leaf['on_parts']!=f['leaf_parts']:raise ValueError('Search residual differs from static candidate')
                    entry=dict(id=row['id'],stratum=row['stratum'],variant=label,frame=f,cp_change=f['qscore']-base['qscore'],
                        pv_changed=f['pv']!=base['pv'],leaf_changed=f['leaf_sfen']!=base['leaf_sfen'],
                        loss=(sigmoid(GAIN*f['qscore'])-sigmoid(GAIN*row['teacher_cp']))**2)
                    report['qsearch'].append(entry);write_report(path,report)
            finally:q.close();pair.close()
        for record in normal:
            row=record['row']
            for variant,values,binary in (('operational_control',[0,0],RUNTIME_MANIFEST.parent/'baseline/bin/release'),('zero',[0,0],executable),('candidate',raw,executable)):
                with raw_env(values):engine=RecordedEngine(binary)
                try:
                    result=engine.analyze(row['moves_before'],12,30,multipv=1)
                    c=result['candidates'][0]
                    if result['stopped_early'] or c['depth']!=12 or c['score_type']!='cp':raise ValueError('Incomplete/special normal search')
                    replay=static.replay(row['moves_before']+c['pv'])
                    if not replay.get('ok') or result['bestmove']!=c['pv'][0]:raise ValueError('Illegal normal bestmove/PV')
                finally:engine.close()
                report['normal'].append(dict(id=row['id'],stratum=row['stratum'],variant=variant,result=result,commands=engine.commands,transcript=engine.transcript))
                write_report(path,report)
        for n,sha in required.items():
            if digest(ROOT/n)!=sha:raise ValueError('Bound input/runtime changed')
        for c in copies:
            if digest(ROOT/c['path'])!=c['sha256']:raise ValueError('Isolated runtime changed')
        report['closed']=True
    except Exception as e:report['errors'].append(dict(type=type(e).__name__,message=str(e)));report['closed']=True;raise
    finally:static.close();write_report(path,report)
    print('Completed35x2QS and6x3normal searches; no learning/deployment.')
    return report

if __name__=='__main__':run()
