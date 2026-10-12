#!/usr/bin/env python3
"""Select fixed12/12 historical roots and replay audit; no search/training entry."""
import sys,json,argparse
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.data.prepare_learning_data import ROOT,digest,Probe
from tools.learning.core.learning_backup import create_backup,verify_backup
from tools.learning.tempo.run_tempo_search import write_report

INPUT=ROOT/'results/learning-pilot/2026-10-12-historical-two-game-input-v1/input.json'
INPUT_SHA='ea00042097935e0174ac3bcd1c7f9165e809476cb1ff427b300fb741cd88fedb'
PILOT=ROOT/'results/learning-pilot/2026-10-12-imitation-run-v1'
PROBE=ROOT/'results/learning-tools/learning-data-probe'
PROBE_SHA='b1401e61a5e776c2df5f242bb12a8dead5de54a4d9d8c5f86c514559c60a900e'
PARENT=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'


def choose(rows,count=12):
    rows=sorted(rows,key=lambda r:r['ply'])
    if len(rows)<count:raise ValueError('Not enough roots; do not refill')
    return [rows[i*(len(rows)-1)//(count-1)] for i in range(count)]


def prepare(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if digest(INPUT)!=INPUT_SHA or digest(PROBE)!=PROBE_SHA:raise ValueError('Input/probe changed')
    data=json.loads(INPUT.read_bytes());baseline_plan=json.loads((ROOT/'results/learning-pilot/2026-10-12-imitation-preparation-v1/plan.json').read_bytes())
    required=dict(baseline_plan['runtime_sha256'])
    required[str(INPUT.relative_to(ROOT))]=INPUT_SHA;required[str(PROBE.relative_to(ROOT))]=PROBE_SHA
    for n,s in required.items():
        if digest(ROOT/n)!=s:raise ValueError('Operational baseline changed')
    selected={};candidate_counts={}
    for split,game_id in (('train',1),('validation',2)):
        game=next(g for g in data['games'] if g['id']==game_id)
        if digest(ROOT/game['source'])!=game['source_sha256']:raise ValueError('KIF changed')
        required[game['source']]=game['source_sha256']
        rows=[r for r in game['positions'] if r['side']=='white' and r['ply']>20]
        candidate_counts[split]=len(rows);selected[split]=[]
        for row in choose(rows):
            selected[split].append(dict(id=f'historical:{game_id}:{row["ply"]}',split=split,game=game_id,
                ply=row['ply'],side_to_move='white',sfen=row['sfen'],actual_move=row['next_move'],
                moves_before=game['moves'][:row['ply']-1],source=game['source'],source_sha256=game['source_sha256'],
                huffman_hex=game['native']['positions'][row['ply']-1]['huffman_hex'],teacher_status='not-generated',
                outcome_loss_enabled=False,actual_white_result='loss'))
    keys=lambda rows:{' '.join(r['sfen'].split()[:3]) for r in rows}
    if keys(selected['train'])&keys(selected['validation']):raise ValueError('Cross-game root overlap')
    output.mkdir(parents=True,exist_ok=False)
    plan=dict(schema='rakuyou-game-split-root-plan-v1',selection='White after20, floor(i*(n-1)/11), fixed before scores',
        train_game=1,validation_game=2,requested=dict(train=12,validation=12),initial='operational baseline plus zero delta',
        teacher_search_enabled=False,training_enabled=False,deployment_enabled=False,outcome_loss_enabled=False,
        max_new_normal_searches=48,max_new_qsearch_calls=48,retry_or_refill=False,
        proposed_learner=dict(max_updates=20,per_key_cap_cp=.01,max_position_cp_change=10),
        stop_policy='at most one further20-update transfer pilot; no tuning, split swap, automatic expansion or normal-search extension',
        validation_scope='previously exposed game; prospective transfer diagnostic, not unseen',runtime_sha256=baseline_plan['runtime_sha256'])
    write_report(output/'plan.json',plan)
    probe=Probe(PROBE,ROOT/'bin/params.bin',details=True);checks=[];excluded=[];accepted={s:[] for s in selected}
    try:
        for split,rows in selected.items():
            for row in rows:
                replay=probe.replay(row['moves_before']+[row['actual_move']])
                if not replay.get('ok'):
                    excluded.append(dict(id=row['id'],reason='illegal_history_or_actual_move'));continue
                root=replay['positions'][-2]
                if root['sfen']!=row['sfen'] or root['huffman_hex']!=row['huffman_hex']:raise ValueError('Root identity mismatch')
                if any(x['occurrences']>1 for x in replay['positions']):
                    excluded.append(dict(id=row['id'],reason='repeated_history'));continue
                checks.append(dict(id=row['id'],root=root,actual_after=replay['positions'][-1]));accepted[split].append(row)
    finally:probe.close()
    for split,rows in accepted.items():write_report(output/f'{split}.pending.json',dict(records=rows,teacher_searches=0,updates=0))
    # Mark reusable baseline records without opening a closed runner or searching.
    prior=ROOT/'results/learning-pilot/2026-10-12-historical-move-comparison-v1/report.json'
    prior_sha='d7825b838e41f8f544107874ef6571e6c1e65cfae250274b0c19d013dcd9dacd'
    if digest(prior)!=prior_sha:raise ValueError('Prior comparison changed')
    required[str(prior.relative_to(ROOT))]=prior_sha
    prior_records=json.loads(prior.read_bytes())['records'];reuse=[]
    for rows in accepted.values():
        for row in rows:
            existing=[x for x in prior_records if x['row']['id']==row['id'] and x['row']['moves_before']==row['moves_before'] and x['excluded'] is None]
            if {x['variant'] for x in existing}=={'unrestricted','forced-actual'}:reuse.append(row['id'])
    for p in [Path(__file__),ROOT/'test/learning/imitation/test_prepare_game_split.py',output/'plan.json',output/'train.pending.json',output/'validation.pending.json']:
        required[str(p.relative_to(ROOT))]=digest(p)
    covered=verify_backup(PARENT/'backup/manifest.json')
    extras={n:s for n,s in required.items() if covered.get(n)!=s}
    create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras)
    manifest=dict(schema='rakuyou-game-split-root-preparation-v1',plan=plan,requested=selected,accepted=accepted,
        candidate_counts=candidate_counts,native_checks=checks,excluded=excluded,reusable_baseline_comparison_ids=reuse,
        required_sha256=required,plan_sha256=digest(output/'plan.json'),backup_sha256=digest(output/'backup/manifest.json'),
        teacher_searches=0,qsearch_calls=0,updates=0,training_ready=False,deployed=False)
    for n,s in required.items():
        if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
    write_report(output/'manifest.json',manifest)
    write_report(output/'audit.json',dict(accepted=True,manifest_sha256=digest(output/'manifest.json'),native_histories=24,
        counts={s:len(rows) for s,rows in accepted.items()},cross_game_root_overlap=0,excluded=excluded,
        searches=0,updates=0,runtime_and_old_candidates_unchanged=True,backups_verified=True))
    print(json.dumps(dict(plies={s:[r['ply'] for r in rows] for s,rows in accepted.items()},excluded=excluded,reusable=reuse),indent=2));return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output)
