#!/usr/bin/env python3
"""Six searches on three diagnosed roots, baseline or locked candidate; no retries."""
import argparse
import json
from pathlib import Path

from prepare_learning_data import ROOT,Probe,digest
from prepare_tempo_search import ReadyEngine,SETTINGS
from run_tempo_search import verify,validate_result,write_report,PREPARATION_SHA,PROBE_SHA

BASELINE_CONTROL_SHA='b5b70af8d8301ef7e201e4e6fb93a940807591ebd203d5f350c480e946b5475e'

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


def summarize(original,repeats,candidate,*,variant="baseline"):
    analyses=[original]+repeats
    candidates=[a['candidates'][0] for a in analyses]
    cp=[int(c['score']) for c in candidates if c['score_type']=='cp']
    result=dict(baseline_observations=len(analyses),
                baseline_bestmoves=[a['bestmove'] for a in analyses],
                distinct_baseline_bestmoves=len({a['bestmove'] for a in analyses}),
                distinct_baseline_pvs=len({tuple(c['pv']) for c in candidates}),
                baseline_cp=cp,baseline_cp_min=min(cp) if len(cp)==len(analyses) else None,
                baseline_cp_max=max(cp) if len(cp)==len(analyses) else None,
                prior_candidate_bestmove=candidate['bestmove'],
                prior_candidate_score_type=candidate['candidates'][0]['score_type'],
                prior_candidate_score=candidate['candidates'][0]['score'])
    if variant=='candidate':
        return {(k.replace('prior_candidate','prior_baseline') if k.startswith('prior_candidate')
                 else k.replace('baseline','candidate')):v for k,v in result.items()}
    if variant!='baseline':raise ValueError('Unknown control variant')
    return result


def run(manifest_path,comparison_path,output,*,variant='baseline',baseline_control=None):
    if variant not in ('baseline','candidate'):raise ValueError('Unknown control variant')
    if variant=='candidate':
        if baseline_control is None or digest(baseline_control)!=BASELINE_CONTROL_SHA:
            raise ValueError('Verified baseline control required')
        control=json.loads(Path(baseline_control).read_bytes())
        if control['completed_searches']!=6 or control['errors']:
            raise ValueError('Baseline control incomplete')
    manifest_path=Path(manifest_path).resolve();root=manifest_path.parent
    if digest(comparison_path)!=COMPARISON_SHA:raise ValueError('Comparison SHA mismatch')
    reference=json.loads(Path(comparison_path).read_bytes())
    if reference['completed_searches']!=24 or reference['errors'] or reference['preparation_sha256']!=PREPARATION_SHA:
        raise ValueError('Expected completed prior comparison')
    m,positions=verify(manifest_path)
    chosen=select_controls(reference['records'])
    if variant=='candidate' and [r['position'] for r in chosen]!=[r['position'] for r in control['records']]:
        raise ValueError('Baseline/candidate control roots differ')
    known={p['id']:p for p in positions}
    if any(known[r['position']['id']]!=r['position'] for r in chosen):raise ValueError('Control root mismatch')
    probe_path=ROOT/'results/learning-tools/learning-data-probe'
    if digest(probe_path)!=PROBE_SHA:raise ValueError('Probe SHA mismatch')
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    with (root/f'{variant}-control-attempt-v1.json').open('x') as f:
        json.dump(dict(output=str(output.relative_to(ROOT)),comparison_sha256=COMPARISON_SHA),f)
    report=dict(schema=f'rakuyou-tempo-{variant}-repeatability-v1',settings={**SETTINGS,'max_searches':6},
                preparation_sha256=PREPARATION_SHA,comparison_sha256=COMPARISON_SHA,
                attempted_searches=0,completed_searches=0,records=[],errors=[],
                real_data_updates=0,deployed=False,candidate_searches=0,
                variant=variant,baseline_control_sha256=BASELINE_CONTROL_SHA if variant=="candidate" else None,
                tool_sha256=digest(Path(__file__)),probe_sha256=PROBE_SHA)
    path=output/'report.json';write_report(path,report)
    probe=Probe(probe_path)
    try:
        for source in chosen:
            p=source['position']
            replay=probe.replay(p['moves'])
            if not replay.get('ok') or replay['positions'][-1]['sfen']!=p['sfen']:raise ValueError('Root replay mismatch')
            other='candidate' if variant=='baseline' else 'baseline'
            record=dict(position=p,repeats=[])
            record['original_'+variant]=source['analyses'][variant]
            record['prior_'+other]=source['analyses'][other]
            report['records'].append(record)
            for repeat in range(2):
                print(f"[{report['attempted_searches']+1}/6] {p['id']} {variant} repeat{repeat+1}",flush=True)
                engine=ReadyEngine(root/variant/'bin/release')
                try:
                    if any('failed' in l.lower() or 'error' in l.lower() for l in engine.transcript):raise ValueError('Loading error')
                    report['attempted_searches']+=1
                    if variant=='candidate':report['candidate_searches']+=1
                    write_report(path,report)
                    result=engine.analyze(p['moves'],12,30,multipv=1)
                    record['repeats'].append(result)
                    c=validate_result(result)
                    pv_replay=probe.replay(p['moves']+c['pv'])
                    if not pv_replay.get('ok'):raise ValueError('Illegal PV')
                    result['pv_legal']=True
                    report['completed_searches']+=1
                finally:engine.close()
                write_report(path,report)
            record['summary']=summarize(record['original_'+variant],record['repeats'],record['prior_'+other],variant=variant)
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
    p.add_argument('--candidate-control',type=Path,help='candidate-only control, bound to completed baseline report')
    a=p.parse_args();run(a.manifest,a.comparison,a.output,
                        variant='candidate' if a.candidate_control else 'baseline',baseline_control=a.candidate_control)


if __name__=='__main__':main()
