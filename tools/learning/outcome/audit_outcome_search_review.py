#!/usr/bin/env python3
"""Read-only provenance/PV/parameter audit for fixed20 normal-search comparison."""
import sys,json
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.outcome import outcome_search_review as s
from tools.learning.data.prepare_learning_data import ROOT,Probe,digest
from tools.learning.data.refresh_teachers import classify
from tools.learning.core.learning_backup import create_backup,verify_backup
from tools.learning.tempo.run_tempo_search import write_report


def audit(folder):
    folder=Path(folder).resolve();r=json.loads((folder/'report.json').read_bytes());plan=json.loads((folder/'plan.json').read_bytes())
    if (not r['closed'] or r['errors'] or r['attempted']!=12 or r['completed']!=12 or len(r['records'])!=12
        or r['updates'] or r['deployed'] or plan!=r['plan'] or plan['selected_update']!=20):raise ValueError('Unexpected review scope')
    for n,sha in plan['required_sha256'].items():
        if digest(ROOT/n)!=sha:raise ValueError('Protected input changed')
    candidate=folder/'candidate/bin/params.bin'
    if digest(candidate)!=r['export']['candidate_sha256'] or digest(s.ZERO)!=r['export']['zero_export_sha256']:
        raise ValueError('Export changed')
    changed=s.audit_bytes(ROOT/'bin/params.bin',candidate,r['export']['layout'])
    if changed!=r['export']['changed_bytes']:raise ValueError('Byte audit changed')
    for c in r['export']['copies']:
        if digest(ROOT/c['path'])!=c['sha256']:raise ValueError('Isolated runtime changed')
    previous_path=ROOT/'results/learning-pilot/2026-10-12-imitation-search-review-v1/report.json'
    if digest(previous_path)!='5d18c80d6d39c4336e8c69e2f15e3dd0ed74168fbff64d0a36712c6d2f433726':raise ValueError('Prior baseline changed')
    previous=json.loads(previous_path.read_bytes())
    original={x['id']:x for x in previous['records'] if x['variant']=='baseline'}
    probe=Probe(ROOT/'results/learning-tools/learning-data-probe');pairs=[];exclusions=[];counter_differences=[]
    try:
        for index,root in enumerate(plan['roots']):
            a,b=r['records'][2*index:2*index+2]
            if [x['variant'] for x in (a,b)]!=['baseline','candidate'] or any(x['id']!=root['id'] for x in (a,b)):
                raise ValueError('Comparison membership/order changed')
            for x in (a,b):
                cp,reason=classify(x['result'],root['row'],probe)
                if cp!=x['cp'] or reason!=x['excluded']:raise ValueError('PV/cp eligibility changed')
                if [c for c in x['commands'] if c.startswith('go ')]!=['go depth 15']:raise ValueError('Search settings changed')
                for command in ['setoption name OwnBook value false','setoption name ShinYonenagaGyoku value true','setoption name Threads value 1','setoption name USI_Hash value 64']:
                    if command not in x['commands']:raise ValueError('Runtime options missing')
                if reason:exclusions.append(dict(id=x['id'],stratum=x['stratum'],variant=x['variant'],reason=reason))
            previous=original[root['id']]['result'];current=a['result']
            if current['bestmove']!=previous['bestmove']:raise ValueError('Baseline bestmove not reproducible')
            for key in ('depth','score_type','score','pv'):
                if current['candidates'][0][key]!=previous['candidates'][0][key]:raise ValueError('Baseline differs: '+key)
            if current['candidates'][0]['nodes']!=previous['candidates'][0]['nodes']:
                counter_differences.append(dict(id=root['id'],before_nodes=previous['candidates'][0]['nodes'],now_nodes=current['candidates'][0]['nodes']))
            pairs.append(dict(id=root['id'],stratum=root['stratum'],
                baseline_best=a['result']['bestmove'],candidate_best=b['result']['bestmove'],
                bestmove_changed=a['result']['bestmove']!=b['result']['bestmove'],pv_changed=a['result']['candidates'][0]['pv']!=b['result']['candidates'][0]['pv'],
                score_change=b['cp']-a['cp'] if a['cp'] is not None and b['cp'] is not None else None,
                baseline_cp=a['cp'],candidate_cp=b['cp']))
    finally:probe.close()
    valid=[x for x in pairs if x['score_change'] is not None]
    summary=dict(roots=6,valid_cp_pairs=len(valid),bestmove_changed=sum(x['bestmove_changed'] for x in pairs),
        pv_changed=sum(x['pv_changed'] for x in pairs),max_abs_search_cp_change=max(abs(x['score_change']) for x in valid))
    result=dict(accepted=True,report_sha256=digest(folder/'report.json'),pairs=pairs,summary=summary,exclusions=exclusions,
        baseline_six_bestmoves_scores_pvs_reproduced=True,baseline_counter_differences=counter_differences,static_export_history_checks=178,
        restricted_bytes_verified=True,updates=0,additional_searches=0,deployed=False,auditor_sha256=digest(Path(__file__)))
    output=folder/'audit.json'
    if output.exists():raise ValueError('Do not overwrite audit')
    write_report(output,result)
    # Baseline runtime already has independent verified copies. Preserve new
    # source and search records; candidate is reproducible from bound raw delta.
    paths=[Path(__file__),folder/'plan.json',folder/'report.json',folder/'export-audit.json',output,
        ROOT/'tools/learning/outcome/outcome_search_review.py',ROOT/'tools/learning/imitation/imitation_search_review.py',
        ROOT/'test/learning/outcome/test_outcome_search_review.py',s.EXPORT,s.EXPORT.parent/'build.json',s.EXPORT.parent/'export.cc']
    required={str(p.relative_to(ROOT)):digest(p) for p in paths}
    create_backup(required,folder/'backup');verify_backup(folder/'backup/manifest.json',required)
    print(json.dumps(dict(summary=summary,exclusions=exclusions,pairs=pairs),indent=2));return result

if __name__=='__main__':audit(Path(sys.argv[1]))
