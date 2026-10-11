#!/usr/bin/env python3
"""Six baseline-only searches on three diagnosed roots; no retries or tuning."""
import argparse
import json
from pathlib import Path

from prepare_learning_data import ROOT,Probe,digest
from prepare_tempo_search import ReadyEngine,SETTINGS
from run_tempo_search import verify,validate_result,write_report,PREPARATION_SHA,PROBE_SHA

COMPARISON_SHA='a6e87fa8822f85c6f314873dfbf9ebf7e1d170760208164f922eba81754801fe'


def select_controls(records):
    comparable=[r for r in records if r['comparison']['cp_change'] is not None]
    if not comparable:raise ValueError('No cp comparison')
    largest=max(comparable,key=lambda r:abs(r['comparison']['cp_change']))
    chosen=[largest]
    chosen.extend(r for r in records if r['comparison']['bestmove_changed'] and
                  r['position']['id']!=largest['position']['id'])
    if len(chosen)!=3 or len({r['position']['id'] for r in chosen})!=3:
        raise ValueError('Expected three distinct planned controls')
    return chosen


def summarize(original,repeats,candidate):
    analyses=[original]+repeats
    candidates=[a['candidates'][0] for a in analyses]
    cp=[int(c['score']) for c in candidates if c['score_type']=='cp']
    return dict(baseline_observations=len(analyses),
                baseline_bestmoves=[a['bestmove'] for a in analyses],
                distinct_baseline_bestmoves=len({a['bestmove'] for a in analyses}),
                distinct_baseline_pvs=len({tuple(c['pv']) for c in candidates}),
                baseline_cp=cp,baseline_cp_min=min(cp) if len(cp)==len(analyses) else None,
                baseline_cp_max=max(cp) if len(cp)==len(analyses) else None,
                prior_candidate_bestmove=candidate['bestmove'],
                prior_candidate_score_type=candidate['candidates'][0]['score_type'],
                prior_candidate_score=candidate['candidates'][0]['score'])


def run(manifest_path,comparison_path,output):
    manifest_path=Path(manifest_path).resolve();root=manifest_path.parent
    if digest(comparison_path)!=COMPARISON_SHA:raise ValueError('Comparison SHA mismatch')
    reference=json.loads(Path(comparison_path).read_bytes())
    if reference['completed_searches']!=24 or reference['errors'] or reference['preparation_sha256']!=PREPARATION_SHA:
        raise ValueError('Expected completed prior comparison')
    m,positions=verify(manifest_path)
    chosen=select_controls(reference['records'])
    known={p['id']:p for p in positions}
    if any(known[r['position']['id']]!=r['position'] for r in chosen):raise ValueError('Control root mismatch')
    probe_path=ROOT/'results/learning-tools/learning-data-probe'
    if digest(probe_path)!=PROBE_SHA:raise ValueError('Probe SHA mismatch')
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    with (root/'baseline-control-attempt-v1.json').open('x') as f:
        json.dump(dict(output=str(output.relative_to(ROOT)),comparison_sha256=COMPARISON_SHA),f)
    report=dict(schema='rakuyou-tempo-baseline-repeatability-v1',settings={**SETTINGS,'max_searches':6},
                preparation_sha256=PREPARATION_SHA,comparison_sha256=COMPARISON_SHA,
                attempted_searches=0,completed_searches=0,records=[],errors=[],
                real_data_updates=0,deployed=False,candidate_searches=0,
                tool_sha256=digest(Path(__file__)),probe_sha256=PROBE_SHA)
    path=output/'report.json';write_report(path,report)
    probe=Probe(probe_path)
    try:
        for source in chosen:
            p=source['position']
            replay=probe.replay(p['moves'])
            if not replay.get('ok') or replay['positions'][-1]['sfen']!=p['sfen']:raise ValueError('Root replay mismatch')
            record=dict(position=p,original_baseline=source['analyses']['baseline'],
                        prior_candidate=source['analyses']['candidate'],repeats=[])
            report['records'].append(record)
            for repeat in range(2):
                print(f"[{report['attempted_searches']+1}/6] {p['id']} baseline repeat{repeat+1}",flush=True)
                engine=ReadyEngine(root/'baseline/bin/release')
                try:
                    if any('failed' in l.lower() or 'error' in l.lower() for l in engine.transcript):raise ValueError('Loading error')
                    report['attempted_searches']+=1;write_report(path,report)
                    result=engine.analyze(p['moves'],12,30,multipv=1)
                    record['repeats'].append(result)
                    c=validate_result(result)
                    pv_replay=probe.replay(p['moves']+c['pv'])
                    if not pv_replay.get('ok'):raise ValueError('Illegal PV')
                    result['pv_legal']=True
                    report['completed_searches']+=1
                finally:engine.close()
                write_report(path,report)
            record['summary']=summarize(record['original_baseline'],record['repeats'],record['prior_candidate'])
            write_report(path,report)
        verify(manifest_path);report['runtime_unchanged']=True;report['closed']=True
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error)));report['closed']=True
        raise
    finally:probe.close();write_report(path,report)
    print(json.dumps([r['summary'] for r in report['records']],indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('comparison',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.manifest,a.comparison,a.output)


if __name__=='__main__':main()
