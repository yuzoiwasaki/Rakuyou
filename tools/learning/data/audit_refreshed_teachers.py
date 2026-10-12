#!/usr/bin/env python3
"""Read-only provenance, command, score and native PV audit; no searches/learning."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from collections import Counter
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.refresh_teachers import load_binding
from tools.analysis.analyze_positions import parse_info


def audit_record(record,pending,probe):
    if record['schema']!='rakuyou-refreshed-teacher-v1':raise ValueError('Teacher schema mismatch')
    for k,v in pending.items():
        if k not in ('schema','teacher_cp','teacher_status') and record.get(k)!=v:
            raise ValueError('Pending root/provenance changed: '+k)
    if record.get('outcome_loss_enabled') is not False or record['perspective']!='root-side-to-move':
        raise ValueError('Outcome or perspective mismatch')
    expected=['usi','setoption name ShinYonenagaGyoku value true','setoption name OwnBook value false',
              'setoption name Threads value 1','setoption name USI_Hash value 64','setoption name USI_Ponder value false',
              'setoption name MultiPV value 1','isready','usinewgame',
              'position startpos moves '+' '.join(record['moves_before']),'go depth 15','quit']
    if record['commands']!=expected:raise ValueError('Unexpected search command sequence')
    transcript=record['transcript']
    if 'readyok' not in transcript or any('failed' in l.lower() or 'error' in l.lower() for l in transcript):
        raise ValueError('Readiness/loading mismatch')
    analysis=record['analysis']
    bm=[l.split()[1] for l in transcript if l.startswith('bestmove ')]
    if bm!=[analysis['bestmove']] or analysis['stopped_early']:raise ValueError('Bestmove/stop transcript mismatch')
    candidates=analysis['candidates']
    reason=None;cp=None
    if analysis['bestmove'] in ('win','resign'):
        reason='special_terminal';moves=record['moves_before']
    else:
        if len(candidates)!=1:raise ValueError('Expected one completed PV')
        c=candidates[0]
        if parse_info(c['raw'])!=c or c['raw'] not in transcript:raise ValueError('Parsed result differs from native info')
        if not c['pv'] or c['pv'][0]!=analysis['bestmove']:raise ValueError('PV/bestmove mismatch')
        moves=record['moves_before']+c['pv']
        if c['score_type']=='mate':reason='mate_score'
        elif c['depth']!=15:raise ValueError('Incomplete depth')
        elif any(w in c['raw'].split() for w in ('lowerbound','upperbound')):reason='bounded_score'
        elif c['score_type']!='cp':reason='non_cp_score'
        elif abs(int(c['score']))>=31000:reason='known_win_score'
        else:cp=int(c['score'])
    replay=probe.replay(moves)
    if not replay.get('ok'):raise ValueError('Native root/PV illegal')
    root=replay['positions'][len(record['moves_before'])]
    expected_side='b' if record['side_to_move']=='black' else 'w'
    if root['sfen']!=record['sfen'] or root['huffman_hex']!=record['huffman_hex'] or root['sfen'].split()[1]!=expected_side:
        raise ValueError('Native root/side mismatch')
    if reason is None and any(p['occurrences']>1 for p in replay['positions']):
        reason='repeated_root_or_pv_history';cp=None
    status='accepted' if reason is None else 'excluded'
    if record['teacher_status']!=status or record['teacher_cp']!=cp or record.get('excluded')!=reason:
        raise ValueError('Teacher status/cp/exclusion mismatch')
    return reason


def audit(report_path,output):
    report_path=Path(report_path).resolve();output=Path(output)
    if output.exists():raise FileExistsError(output)
    r=json.loads(report_path.read_bytes())
    if (r['schema']!='rakuyou-teacher-refresh-run-v1' or r['mode']!='run' or r['errors'] or
        not r['teacher_generation_complete'] or r['attempted_searches']!=54 or r['completed_searches']!=54 or
        r['real_data_updates']!=0 or r['deployed'] is not False or r['training_ready'] is not False):
        raise ValueError('Expected complete, untrained/undeployed generation')
    for n,sha in r['tool_sha256'].items():
        if digest(ROOT/'tools'/n)!=sha:raise ValueError('Generation tool changed')
    for e in r['input_copies']:
        if digest(ROOT/e['source'])!=e['sha256'] or digest(report_path.parent/e['copy'])!=e['sha256']:
            raise ValueError('Input/copy SHA mismatch')
    prep=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['preparation_sha256'])
    plan=next(ROOT/e['source'] for e in r['input_copies'] if e['sha256']==r['plan_sha256'])
    bound_plan,_,pending,entries,_,probe_path=load_binding(prep,plan,True)
    if (r['settings']!=bound_plan['search'] or r['runtime_sha256']!=bound_plan['runtime_sha256'] or
            r['runtime_files']!=entries or r['probe_sha256']!=digest(probe_path) or r['validated_roots']!=54):
        raise ValueError('Reported runtime/settings/probe differs from actual binding')
    known={x['id']:x for rows in pending.values() for x in rows}
    seen=set();records=[]
    for split,e in r['files'].items():
        path=report_path.parent/e['path']
        if digest(path)!=e['sha256']:raise ValueError('Teacher file SHA mismatch')
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if rows!=[x for x in r['records'] if x['split']==split]:raise ValueError('Report/JSONL mismatch')
        records.extend(rows)
    if len(records)!=54 or {x['id'] for x in records}!=set(known):raise ValueError('Root membership mismatch')
    probe=Probe(probe_path);summary={}
    try:
        for record in records:
            if record['id'] in seen:raise ValueError('Duplicate teacher')
            seen.add(record['id'])
            if record['teacher_origin']!=bound_plan['teacher']['origin']:
                raise ValueError('Reported teacher origin changed')
            audit_record(record,known[record['id']],probe)
        for split in ('train','validation'):
            rows=[x for x in records if x['split']==split]
            summary[split]=dict(roots=len(rows),status=dict(Counter(x['teacher_status'] for x in rows)),
                exclusions=dict(Counter(x['excluded'] for x in rows if x['excluded'] is not None)),
                accepted_strata=dict(Counter(x['stratum'] for x in rows if x['teacher_status']=='accepted')),
                accepted_draws=sum(x['teacher_status']=='accepted' and x['stratum'].endswith(':draw') for x in rows),
                accepted_white_draws=sum(x['teacher_status']=='accepted' and x['stratum']=='white:draw' for x in rows))
    finally:probe.close()
    accepted=sum(x['teacher_status']=='accepted' for x in records)
    if accepted!=r['generated_teachers']:raise ValueError('Generated count mismatch')
    load_binding(prep,plan,True)
    out=dict(schema='rakuyou-refreshed-teacher-audit-v1',generation_report_sha256=digest(report_path),
             audit_tool_sha256=digest(Path(__file__)),roots_checked=54,native_root_pv_replays=54,
             accepted=accepted,excluded=54-accepted,summary=summary,teacher_provenance_verified=True,
             searches_executed=0,real_data_updates=0,training_ready=False,deployed=False)
    with output.open('x') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(out['summary'],indent=2))
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.report,a.output)
