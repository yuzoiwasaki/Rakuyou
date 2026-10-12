#!/usr/bin/env python3
"""One bounded comparison using the verified 12-root preparation. No retries."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.tempo.prepare_tempo_search import SETTINGS, ReadyEngine

PREPARATION_SHA='05e26d28eb91f7def2277d3cc766e79bed964e12364a3f3223b81a3f8a862aec'
PROBE_SHA='b1401e61a5e776c2df5f242bb12a8dead5de54a4d9d8c5f86c514559c60a900e'


def verify(manifest_path):
    manifest_path=Path(manifest_path).resolve();root=manifest_path.parent
    if digest(manifest_path)!=PREPARATION_SHA:raise ValueError('Preparation SHA mismatch')
    m=json.loads(manifest_path.read_bytes())
    if m['settings']!=SETTINGS:raise ValueError('Search settings changed')
    for e in m['files']:
        if digest(root/e['path'])!=e['sha256']:raise ValueError('Runtime copy changed')
    for n,sha in m['runtime_sha256'].items():
        if digest(ROOT/n)!=sha:raise ValueError('Operational runtime changed')
    if digest(root/'positions.json')!=m['positions_sha256']:raise ValueError('Positions changed')
    positions=json.loads((root/'positions.json').read_bytes())['positions']
    if len(positions)!=12 or len({p['id'] for p in positions})!=12:raise ValueError('Expected twelve unique roots')
    return m,positions


def validate_result(result):
    if result['stopped_early']:raise ValueError('Stopped search')
    cs=result['candidates']
    if len(cs)!=1 or cs[0]['depth']!=12:raise ValueError('Incomplete depth12 result')
    c=cs[0]
    if any(word in c['raw'].split() for word in ('lowerbound','upperbound')):
        raise ValueError('Bounded score instead of completed score')
    if not c['pv'] or result['bestmove']!=c['pv'][0]:raise ValueError('Bestmove/PV mismatch')
    return c


def comparison(a,b):
    x,y=a['candidates'][0],b['candidates'][0]
    return dict(bestmove_changed=a['bestmove']!=b['bestmove'],pv_changed=x['pv']!=y['pv'],
                cp_change=int(y['score'])-int(x['score']) if x['score_type']==y['score_type']=='cp' else None)


def write_report(path,report):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    temporary.replace(path)


def run(manifest_path,output):
    manifest_path=Path(manifest_path).resolve();root=manifest_path.parent
    m,positions=verify(manifest_path)
    probe_path=ROOT/'results/learning-tools/learning-data-probe'
    if digest(probe_path)!=PROBE_SHA:raise ValueError('Probe SHA mismatch')
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in results')
    output.mkdir(parents=True,exist_ok=False)
    # Exclusive preparation-level marker prevents accidental repetition under another output name.
    with (root/'search-attempt-v1.json').open('x') as f:
        json.dump(dict(output=str(output.relative_to(ROOT)),preparation_sha256=PREPARATION_SHA),f)
    report=dict(schema='rakuyou-tempo-full-search-v1',preparation_sha256=PREPARATION_SHA,
                settings=SETTINGS,attempted_searches=0,completed_searches=0,records=[],errors=[],
                real_data_updates=0,deployed=False,candidate_reselected=False,
                tool_sha256=digest(Path(__file__)),probe_sha256=PROBE_SHA)
    path=output/'report.json';write_report(path,report)
    probe=Probe(probe_path)
    try:
        for index,p in enumerate(positions):
            replay=probe.replay(p['moves'])
            if not replay.get('ok') or replay['positions'][-1]['sfen']!=p['sfen']:
                raise ValueError('Root replay mismatch')
            record=dict(position=p,analyses={})
            report['records'].append(record)
            # Alternating order; each root/variant always uses a fresh process.
            order=('baseline','candidate') if index%2==0 else ('candidate','baseline')
            for variant in order:
                print(f"[{report['attempted_searches']+1}/24] {p['id']} {variant}",flush=True)
                engine=ReadyEngine(root/variant/'bin/release')
                try:
                    if any('failed' in l.lower() or 'error' in l.lower() for l in engine.transcript):
                        raise ValueError('Loading error')
                    report['attempted_searches']+=1
                    write_report(path,report)
                    result=engine.analyze(p['moves'],12,30,multipv=1)
                    record['analyses'][variant]=result
                    candidate=validate_result(result)
                    pv_replay=probe.replay(p['moves']+candidate['pv'])
                    if not pv_replay.get('ok'):raise ValueError('Illegal PV')
                    result['pv_legal']=True
                    result['leaf_sfen']=pv_replay['positions'][-1]['sfen']
                    report['completed_searches']+=1
                finally:engine.close()
                write_report(path,report)
            record['comparison']=comparison(record['analyses']['baseline'],record['analyses']['candidate'])
            write_report(path,report)
        verify(manifest_path)
        report['runtime_unchanged']=True
        report['closed']=True
    except Exception as error:
        report['errors'].append(dict(type=type(error).__name__,message=str(error)))
        report['closed']=True
        raise
    finally:
        probe.close();write_report(path,report)
    print(json.dumps(dict(completed=report['completed_searches'],
        bestmove_changed=sum(r['comparison']['bestmove_changed'] for r in report['records']),
        pv_changed=sum(r['comparison']['pv_changed'] for r in report['records'])),indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.manifest,a.output)


if __name__=='__main__':main()
