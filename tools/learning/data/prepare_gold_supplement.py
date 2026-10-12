#!/usr/bin/env python3
"""Select at most16/8 advanced-gold roots; native replay only, no teachers/training."""
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0,str(_RepoPath(__file__).resolve().parents[3]))
import argparse
import json
from collections import Counter,defaultdict
from pathlib import Path
from tools.analysis.audit_white_positions import Board
from tools.learning.gold_silver.gold_advance_features import FEATURE,gold_advance_details,scores,bucket
from tools.learning.data.prepare_learning_data import ROOT,Probe,digest,stable_order,validate_game
from tools.learning.data.prepare_teacher_refresh import pending_record
from tools.learning.core.learning_backup import create_backup,verify_backup,safe_path
from tools.learning.tempo.run_tempo_search import write_report

BASE=ROOT/'results/learning-pilot/2026-10-11-preparation-v2/manifest.json'
BASE_SHA='44704fc910fc3217a55399951d6a60ab233a49b80b0a017695e7672627954792'
PARENT=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
PARENT_SHA='060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4'
PROBE=ROOT/'results/learning-tools/learning-data-probe'
PROBE_SHA='b1401e61a5e776c2df5f242bb12a8dead5de54a4d9d8c5f86c514559c60a900e'
BUCKETS=tuple(f'{side}:rank{height}:{support}' for side in ('black','white')
              for height in ('4','5plus') for support in ('supported','unsupported'))
SEED=20261011


def game_key(id):
    run,game,_=id.split(':');return run,int(game)


def position_key(sfen):return ' '.join(sfen.split()[:3])


def load_inputs():
    if digest(BASE)!=BASE_SHA or digest(PARENT/'report.json')!=PARENT_SHA or digest(PROBE)!=PROBE_SHA:
        raise ValueError('Original manifest, audited parent or probe changed')
    m=json.loads(BASE.read_bytes());parent=json.loads((PARENT/'report.json').read_bytes())
    required={BASE.relative_to(ROOT).as_posix():BASE_SHA,(PARENT/'report.json').relative_to(ROOT).as_posix():PARENT_SHA,
              PROBE.relative_to(ROOT).as_posix():PROBE_SHA}
    for name,sha in m['runtime_sha256'].items():
        if digest(ROOT/name)!=sha:raise ValueError('Runtime changed: '+name)
        required[name]=sha
    prefixes={};blocked_games=set();blocked_roots=set()
    # Read only separation keys from test metadata, never test game files/quality.
    for split,entry in m['outputs'].items():
        path=safe_path(BASE.parent,entry['path'])
        if digest(path)!=entry['sha256']:raise ValueError('Original split changed')
        required[path.relative_to(ROOT).as_posix()]=entry['sha256']
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        prefixes[split]={r['prefix24'] for r in rows}
        if split=='test':blocked_roots.update(position_key(r['sfen']) for r in rows)
    for rows in parent['records'].values():
        for r in rows:
            blocked_games.add(game_key(r['row']['id']))
            blocked_roots.update(position_key(r['frame'][key]) for key in ('root_sfen','leaf_sfen'))
    history=[ROOT/'results/learning-pilot/2026-10-11-input-validation-v1/qsearch-leaves-v1.json',
             ROOT/'results/learning-pilot/2026-10-11-input-validation-v1/validation-leaves-v1.json',
             ROOT/'results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json',
             ROOT/'results/learning-pilot/2026-10-12-pair-teacher-run-v1/report.json']
    for path in history:
        d=json.loads(path.read_bytes());required[path.relative_to(ROOT).as_posix()]=digest(path)
        entries=d.get('frames',d.get('records',[]))
        for r in entries:
            blocked_games.add(game_key(r['id']))
            frame=r.get('qsearch')
            if frame:blocked_roots.update(position_key(frame[k]) for k in ('root_sfen','leaf_sfen'))
            elif 'sfen' in r:blocked_roots.add(position_key(r['sfen']))
    review=ROOT/'results/learning-pilot/2026-10-12-supported-gold-advance-review-v1/review.json'
    required[review.relative_to(ROOT).as_posix()]=digest(review)
    for case in json.loads(review.read_bytes())['cases']:
        blocked_games.add((case['source_sha256'],case['game']))
    return m,prefixes,blocked_games,blocked_roots,required


def collect(m,prefixes,blocked_games,blocked_roots,required):
    candidates={s:[] for s in ('train','validation')};excluded=Counter();eligible_games={s:set() for s in candidates}
    for source in m['sources']:
        run=source['sha256'];split=m['run_assignments'].get(run)
        if split not in candidates:continue
        path=ROOT/source['path']
        if digest(path)!=run:raise ValueError('Raw run changed: '+source['path'])
        required[source['path']]=run;d=json.loads(path.read_bytes())
        forbidden=set().union(*(v for s,v in prefixes.items() if s!=split))
        # Use the same one-based list index as the original audited corpus;
        # paired runs have pair/game_in_pair fields rather than game_number.
        for number,game in enumerate(d['games'],1):
            if (run,number) in blocked_games:excluded['used_game']+=1;continue
            prefix=' '.join(game['moves'][:24])
            if prefix in forbidden:excluded['cross_split_prefix24']+=1;continue
            validate_game(game,d['settings'])
            b=Board();seen=Counter({b.sfen():1});repeated=False
            for ply,move in enumerate(game['moves'],1):
                if ply>120:break
                side='black' if b.ply%2==0 else 'white'
                record=game['records'][ply-1]
                if ply>=24 and game[side]=='shin_yonenaga' and record['source']=='search' and not repeated:
                    details=gold_advance_details(b.pieces);group=bucket(details,side);sfen=b.sfen()+' 1'
                    if group and position_key(sfen) not in blocked_roots:
                        analysis=record.get('analysis') or {}
                        row=dict(id=f'{run}:{number}:{ply}',split=split,run=run,game=number,ply=ply,
                            side_to_move=side,stratum=f'{side}:{game["result"]}',sfen=sfen,prefix24=prefix,
                            moves_before=game['moves'][:ply-1],source_path=source['path'],source_sha256=run,
                            termination=game['reason'],teacher_cp=int(analysis['score']) if analysis.get('score_type')=='cp' else None,
                            depth=analysis.get('depth'),provenance_status='historical_runtime_not_verified',
                            bucket=group,gold_details=details,gold_scores=scores(details))
                        candidates[split].append(row);eligible_games[split].add((run,number))
                b.push(move);seen[b.sfen()]+=1
                if seen[b.sfen()]>1:repeated=True
    return candidates,dict(excluded),{s:len(v) for s,v in eligible_games.items()}


def choose(candidates,per_bucket,cap,forbidden_roots=(),forbidden_prefixes=()):
    groups=defaultdict(list)
    for row in candidates:groups[row['bucket']].append(row)
    for rows in groups.values():rows.sort(key=lambda r:(stable_order(SEED,r['id']),r['id']))
    selected=[];games=set();roots=set(forbidden_roots);runs=Counter();missing=[]
    for round_index in range(per_bucket):
        for group in BUCKETS:
            row=next((r for r in groups[group] if game_key(r['id']) not in games
                      and runs[r['run']]<cap and position_key(r['sfen']) not in roots
                      and r['prefix24'] not in forbidden_prefixes),None)
            if row is None:missing.append(dict(bucket=group,round=round_index+1));continue
            selected.append(row);games.add(game_key(row['id']));roots.add(position_key(row['sfen']));runs[row['run']]+=1
    return selected,missing


def prepare(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():
        raise ValueError('A new results directory is required')
    m,prefixes,blocked_games,blocked_roots,required=load_inputs()
    pool,excluded,eligible_games=collect(m,prefixes,blocked_games,blocked_roots,required)
    selected={};missing={}
    selected['train'],missing['train']=choose(pool['train'],2,4)
    selected['validation'],missing['validation']=choose(pool['validation'],1,2,
        [position_key(r['sfen']) for r in selected['train']],{r['prefix24'] for r in selected['train']})
    valid={s:[] for s in selected};checks=[];native_exclusions=[]
    probe=Probe(PROBE,ROOT/'bin/params.bin',details=True)
    try:
        for split,rows in selected.items():
            for row in rows:
                replay=probe.replay(row['moves_before'])
                if not replay.get('ok') or any(p['occurrences']>1 for p in replay.get('positions',[])):
                    native_exclusions.append(dict(id=row['id'],reason='illegal_or_repeated_history'));continue
                root=replay['positions'][-1]
                if root['sfen']!=row['sfen']:raise ValueError('Native/Board SFEN mismatch')
                row['huffman_hex']=root['huffman_hex'];valid[split].append(row)
                checks.append(dict(id=row['id'],sfen=root['sfen'],huffman_hex=root['huffman_hex'],
                    progress=root['progress'],base_eval_on=root['eval_on'],base_eval_off=root['eval_off'],
                    gold_scores=row['gold_scores'],bucket=row['bucket']))
    finally:probe.close()
    output.mkdir(parents=True,exist_ok=False)
    reference=json.loads((ROOT/'docs/experiments/configs/teacher-refresh-v1.json').read_bytes())
    plan=dict(schema='rakuyou-gold-supplement-plan-v1',feature=FEATURE,seed=SEED,window=[24,120],
        max_roots_per_game=1,per_bucket=dict(train=2,validation=1),max_roots_per_run=dict(train=4,validation=2),
        buckets=list(BUCKETS),selection_order='SHA256(seed:id), round-robin fixed buckets',
        selection_uses_results_or_scores=False,selection_targets='Shin player own most advanced unpromoted gold',
        prior_games_excluded=len(blocked_games),test_quality_used=False,replacement_after_failure=False,
        existing_counts=dict(train=143,validation=35),supplement_max_counts=dict(train=16,validation=8),
        search={**reference['search'],'max_searches':len(valid['train'])+len(valid['validation'])},
        teacher=reference['teacher'],acceptance=reference['acceptance'],runtime_sha256=m['runtime_sha256'],
        teacher_search_enabled=False,real_data_training_enabled=False,deployment_enabled=False,
        outcome_loss_enabled=False,reference_only_config=dict(max_updates=20,l2=1e-6,delta_limit_cp=.5,
        max_position_cp_change=10),note='Selected roots only; actual teachers/leaves and final L2 still require review')
    write_report(output/'plan.json',plan)
    files={}
    for split,rows in valid.items():
        path=output/f'{split}.pending.jsonl'
        with path.open('x') as f:
            for row in rows:
                pending=pending_record(row)
                pending.update(bucket=row['bucket'],prefix24=row['prefix24'],gold_details=row['gold_details'],gold_scores=row['gold_scores'])
                f.write(json.dumps(pending,ensure_ascii=False,sort_keys=True)+'\n')
        files[split]=dict(path=path.name,sha256=digest(path),roots=len(rows))
        required[path.relative_to(ROOT).as_posix()]=digest(path)
    for path in [Path(__file__),ROOT/'tools/learning/gold_silver/gold_advance_features.py',
                 ROOT/'test/learning/data/test_prepare_gold_supplement.py',output/'plan.json']:
        required[path.relative_to(ROOT).as_posix()]=digest(path)
    existing_manifest=PARENT/'backup/manifest.json';existing=verify_backup(existing_manifest)
    covered={n:s for n,s in required.items() if n in existing};verify_backup(existing_manifest,covered)
    new={n:s for n,s in required.items() if n not in existing}
    create_backup(new,output/'additional-backup');verify_backup(output/'additional-backup/manifest.json',new)
    summary={s:dict(requested=16 if s=='train' else 8,selected=len(rows),runs=len({r['run'] for r in rows}),
        buckets=dict(Counter(r['bucket'] for r in rows)),outcomes=dict(Counter(r['stratum'] for r in rows)),
        min_ply=min((r['ply'] for r in rows),default=None),max_ply=max((r['ply'] for r in rows),default=None)) for s,rows in valid.items()}
    report=dict(schema='rakuyou-gold-supplement-preparation-v1',plan_sha256=digest(output/'plan.json'),
        base_manifest_sha256=BASE_SHA,parent_report_sha256=PARENT_SHA,probe_sha256=PROBE_SHA,
        input_sha256=required,files=files,summary=summary,pool_counts={s:dict(Counter(r['bucket'] for r in rows)) for s,rows in pool.items()},
        pool_eligible_games=eligible_games,game_exclusions=excluded,unfilled_buckets=missing,
        native_exclusions=native_exclusions,native_checks=checks,
        selection_complete=all(not v for v in missing.values()) and not native_exclusions,
        searches=0,updates=0,test_roots=0,deployed=False,teacher_generation_ready=False,training_ready=False,
        existing_backup_sha256=digest(existing_manifest),additional_backup_sha256=digest(output/'additional-backup/manifest.json'))
    for name,sha in required.items():
        if digest(ROOT/name)!=sha:raise ValueError('Bound input changed after preparation: '+name)
    write_report(output/'manifest.json',report)
    print(json.dumps(dict(summary=summary,pool=report['pool_counts'],missing=missing,native_exclusions=native_exclusions),indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();prepare(args.output)
