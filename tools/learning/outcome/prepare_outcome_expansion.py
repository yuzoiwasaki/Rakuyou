#!/usr/bin/env python3
"""Fixed384/96 outcome roots from unused games; static audit, report shortages, no refill."""
import sys,json,argparse
from pathlib import Path
from collections import Counter,defaultdict
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,digest,validate_game,outcome,teacher_rejection,stable_order,Probe
from tools.learning.data.prepare_gold_supplement import load_inputs,position_key,game_key,BASE,PARENT,PROBE,PROBE_SHA
from tools.learning.data.prepare_teacher_refresh import STRATA
from tools.analysis.audit_white_positions import Board
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report
from tools.learning.imitation.sparse_updater import CONFIG

SEED=20261011
CAPS={'train':24,'validation':24}


def bindings():
    manifest,prefixes,used,blocked,required=load_inputs()
    gold=ROOT/'results/learning-pilot/2026-10-12-gold-supplement-preparation-v1/manifest.json'
    if digest(gold)!='06d59cc954ccae8e464b05b26f3c3fe4eb3008b23d6a538aa08267ae90dc1938':raise ValueError('Prior selection changed')
    g=json.loads(gold.read_bytes());required[str(gold.relative_to(ROOT))]=digest(gold)
    for split,e in g['files'].items():
        path=gold.parent/e['path']
        if digest(path)!=e['sha256']:raise ValueError('Prior pending games changed')
        required[str(path.relative_to(ROOT))]=e['sha256']
        for line in path.read_text().splitlines():
            row=json.loads(line);used.add(game_key(row['id']));blocked.add(position_key(row['sfen']))
    return manifest,prefixes,used,blocked,required


def collect(manifest,prefixes,used,blocked,required):
    candidates={'train':[],'validation':[]};excluded=Counter();available={s:Counter() for s in candidates}
    for source in manifest['sources']:
        split=manifest['run_assignments'].get(source['sha256'])
        if split not in candidates:continue
        path=ROOT/source['path']
        if digest(path)!=source['sha256']:raise ValueError('Raw run changed')
        required[source['path']]=source['sha256'];doc=json.loads(path.read_bytes())
        forbidden=set().union(*(v for key,v in prefixes.items() if key!=split))
        for number,game in enumerate(doc['games'],1):
            if (source['sha256'],number) in used:excluded['used_game']+=1;continue
            validate_game(game,doc['settings'])
            side='black' if game['black']=='shin_yonenaga' else 'white';stratum=side+':'+game['result']
            available[split][stratum]+=1
            prefix=' '.join(game['moves'][:24])
            if prefix in forbidden:excluded['cross_split_prefix24']+=1;continue
            board=Board();seen=Counter({board.sfen():1});repeated=False
            for ply,move in enumerate(game['moves'],1):
                if ply>80:break
                record=game['records'][ply-1]
                rejection=teacher_rejection(record)
                if not rejection and not repeated:
                    sfen=board.sfen()+' 1'
                    if position_key(sfen) not in blocked:
                        label=outcome(game,side)
                        candidates[split].append(dict(id=f'{source["sha256"]}:{number}:{ply}',split=split,run=source['sha256'],game=number,
                            ply=ply,side_to_move=side,stratum=stratum,sfen=sfen,moves_before=game['moves'][:ply-1],actual_move=move,
                            prefix24=prefix,target=label['target'],use_outcome_loss=label['use_outcome_loss'],outcome_kind=label['kind'],
                            source=dict(path=source['path'],sha256=source['sha256'],run=source['sha256'],game=number,ply=ply,termination=game['reason']),
                            historical_runtime_provenance='not_verified'))
                board.push(move);seen[board.sfen()]+=1;repeated|=seen[board.sfen()]>1
    return candidates,dict(excluded),{s:dict(c) for s,c in available.items()}


def select(rows,per_stratum,cap,forbidden_roots=(),forbidden_prefixes=()):
    groups={s:[] for s in STRATA}
    for r in rows:groups[r['stratum']].append(r)
    for group in groups.values():group.sort(key=lambda r:(stable_order(SEED,r['id']),r['id']))
    selected=[];games=set();roots=set(forbidden_roots);runs=Counter()
    for _ in range(per_stratum):
        for s in STRATA:
            row=next((r for r in groups[s] if game_key(r['id']) not in games and runs[r['run']]<cap
                and position_key(r['sfen']) not in roots and r['prefix24'] not in forbidden_prefixes),None)
            if row is None:continue
            selected.append(row);games.add(game_key(row['id']));roots.add(position_key(row['sfen']));runs[row['run']]+=1
    counts=Counter(r['stratum'] for r in selected)
    return selected,{s:per_stratum-counts[s] for s in STRATA if counts[s]<per_stratum}


def prepare(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    m,prefixes,used,blocked,required=bindings()
    pool,rejections,available=collect(m,prefixes,used,blocked,required)
    selected={};shortages={}
    selected['train'],shortages['train']=select(pool['train'],64,CAPS['train'])
    selected['validation'],shortages['validation']=select(pool['validation'],16,CAPS['validation'],
        [position_key(r['sfen']) for r in selected['train']],{r['prefix24'] for r in selected['train']})
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(requested={'train':384,'validation':96},per_stratum={'train':64,'validation':16},seed=SEED,window=[24,80],
        eligibility='existing teacher_rejection plus nonrepeated history: Shin/search/depth15 cp, abs archivedcp<=1000; not a new cp teacher',
        max_roots_per_game=1,max_roots_per_run=CAPS,selection='fixed SHA256(seed:id) round-robin six strata, no post-learning quality selection',
        prior_used_games=len(used),draw_policy='max_plies masked from winner loss/keys/denominator',config=CONFIG,
        training_enabled=False,searches_enabled=False,deployment_enabled=False,refill_after_failure=False,
        initial='operational baseline plus zero sparse KP/PP; no previous candidate continuation')
    write_report(output/'plan.json',plan)
    accepted={s:[] for s in selected};native_exclusions=[];checks=[];probe=Probe(PROBE,ROOT/'bin/params.bin',details=True)
    try:
        for split,rows in selected.items():
            for index,row in enumerate(rows):
                if index%64==0:print(split,index,len(rows),flush=True)
                replay=probe.replay(row['moves_before']+[row['actual_move']])
                if not replay.get('ok') or any(x['occurrences']>1 for x in replay.get('positions',[])):
                    native_exclusions.append(dict(id=row['id'],reason='illegal_or_repeated_history'));continue
                root=replay['positions'][-2]
                if root['sfen']!=row['sfen']:raise ValueError('Native/Board identity mismatch')
                row={**row,'huffman_hex':root['huffman_hex']};accepted[split].append(row);checks.append(dict(id=row['id'],root=root))
    finally:probe.close()
    summary={}
    for split,rows in accepted.items():
        runs=Counter(r['run'] for r in rows);counts=Counter(r['stratum'] for r in rows)
        summary[split]=dict(roots=len(rows),supervised=sum(r['use_outcome_loss'] for r in rows),masked=sum(not r['use_outcome_loss'] for r in rows),
            strata=dict(counts),games=len({game_key(r['id']) for r in rows}),runs=len(runs),max_per_run=max(runs.values(),default=0),
            deficits={s:plan['per_stratum'][split]-counts[s] for s in STRATA if counts[s]<plan['per_stratum'][split]})
        write_report(output/f'{split}.roots.json',dict(records=rows,updates=0))
    if {r['run'] for r in accepted['train']}&{r['run'] for r in accepted['validation']}:raise ValueError('Run split overlap')
    if {position_key(r['sfen']) for r in accepted['train']}&{position_key(r['sfen']) for r in accepted['validation']}:raise ValueError('Root overlap')
    if any(game_key(r['id']) in used for rows in accepted.values() for r in rows):raise ValueError('Prior game reused')
    for p in [Path(__file__),ROOT/'tools/learning/data/prepare_gold_supplement.py',ROOT/'tools/analysis/audit_white_positions.py',
        ROOT/'tools/learning/data/prepare_learning_data.py',ROOT/'test/learning/outcome/test_prepare_outcome_expansion.py',
        output/'plan.json',output/'train.roots.json',output/'validation.roots.json']:
        required[str(p.relative_to(ROOT))]=digest(p)
    covered=verify_backup(PARENT/'backup/manifest.json')
    covered.update(verify_backup(ROOT/'results/learning-pilot/2026-10-12-gold-supplement-preparation-v1/additional-backup/manifest.json'))
    extras={n:s for n,s in required.items() if covered.get(n)!=s};create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras)
    for n,s in required.items():
        if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
    result=dict(plan=plan,summary=summary,available_unused_games=available,pool_games={s:dict(Counter({st:len({game_key(r['id']) for r in pool[s] if r['stratum']==st}) for st in STRATA})) for s in pool},
        collection_rejections=rejections,sampling_shortages=shortages,native_exclusions=native_exclusions,native_checks=checks,
        required_sha256=required,selection_complete=not any(summary[s]['deficits'] for s in summary),
        searches=0,qsearch_calls=0,updates=0,deployed=False,training_ready=False,backup_sha256=digest(output/'backup/manifest.json'))
    write_report(output/'manifest.json',result)
    write_report(output/'audit.json',dict(accepted=True,manifest_sha256=digest(output/'manifest.json'),summary=summary,
        selection_complete=result['selection_complete'],native_exclusions=native_exclusions,no_retry_or_refill=True,
        searches=0,updates=0,no_test_games_read=True,runtime_unchanged=True))
    print(json.dumps(dict(summary=summary,unused=available,pool_games=result['pool_games']),indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.output)
