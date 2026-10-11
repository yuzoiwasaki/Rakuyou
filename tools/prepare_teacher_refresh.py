#!/usr/bin/env python3
"""Select and replay 54 planned roots. No engine search, teacher loss or learning."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from prepare_learning_data import ROOT,Probe,digest
from validate_learning_input import load_input

STRATA=tuple(f'{side}:{result}' for side in ('black','white')
             for result in ('black_win','draw','white_win'))


def select_rows(rows,per_stratum,seed,*,max_per_run=6):
    groups={s:[] for s in STRATA}
    for r in rows:
        if r['stratum'] not in groups:raise ValueError('Unknown stratum')
        groups[r['stratum']].append(r)
    for group in groups.values():
        group.sort(key=lambda r:(hashlib.sha256(f"{seed}:{r['id']}".encode()).hexdigest(),r['id']))
    selected=[];games=set();runs=Counter();roots=set()
    for _ in range(per_stratum):
        for stratum in STRATA:
            eligible=next((r for r in groups[stratum] if (r['run'],r['game']) not in games
                           and runs[r['run']]<max_per_run and r['sfen'] not in roots),None)
            if eligible is None:raise ValueError('Insufficient roots under fixed sampling caps')
            selected.append(eligible);games.add((eligible['run'],eligible['game']))
            runs[eligible['run']]+=1;roots.add(eligible['sfen'])
    return selected


def pending_record(row):
    return dict(schema='rakuyou-teacher-refresh-root-v1',id=row['id'],split=row['split'],
                stratum=row['stratum'],side_to_move=row['side_to_move'],sfen=row['sfen'],
                huffman_hex=row['huffman_hex'],moves_before=row['moves_before'],
                source=dict(path=row['source_path'],sha256=row['source_sha256'],run=row['run'],
                            game=row['game'],ply=row['ply'],termination=row['termination']),
                archived_reference=dict(teacher_cp=row['teacher_cp'],depth=row['depth'],
                                        provenance_status=row['provenance_status']),
                teacher_cp=None,teacher_status='not-generated',outcome_loss_enabled=False)


def prepare(manifest_path,plan_path,output):
    plan=json.loads(Path(plan_path).read_bytes())
    if (plan['schema']!='rakuyou-teacher-refresh-plan-v1' or
            any(plan[k] is not False for k in ('teacher_search_enabled','real_data_training_enabled','deployment_enabled'))):
        raise ValueError('Expected disabled design-only plan')
    if digest(manifest_path)!=plan['preparation_manifest_sha256']:raise ValueError('Input manifest SHA mismatch')
    manifest,parts=load_input(manifest_path)
    runtime={n:digest(ROOT/n) for n in plan['runtime_sha256']}
    if runtime!=plan['runtime_sha256'] or runtime!=manifest['runtime_sha256']:raise ValueError('Runtime identity mismatch')
    sel=plan['selection']
    if sel['per_stratum']!={'train':6,'validation':3} or sel['max_roots_per_game']!=1 or sel['max_roots_per_run']!=6 or sel['test_roots']!=0:
        raise ValueError('Fixed pilot sampling policy changed')
    chosen={s:select_rows(parts[s],n,sel['seed']) for s,n in sel['per_stratum'].items()}
    if {r['run'] for r in chosen['train']}&{r['run'] for r in chosen['validation']}:raise ValueError('Split runs overlap')
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()):raise ValueError('Output must be in ignored results')
    if output.exists():raise FileExistsError(output)
    probe_path=ROOT/'results/learning-tools/learning-data-probe'
    if digest(probe_path)!=plan['probe_sha256']:raise ValueError('Probe identity mismatch')
    probe=Probe(probe_path)
    try:
        for rows in chosen.values():
            for r in rows:
                f=probe.replay(r['moves_before'])
                if not f.get('ok'):raise ValueError('Illegal input root')
                root=f['positions'][-1]
                if root['sfen']!=r['sfen'] or root['huffman_hex']!=r['huffman_hex']:raise ValueError('Root identity mismatch')
                if any(p['occurrences']>1 for p in f['positions']):raise ValueError('Repeated root history')
    finally:probe.close()
    if runtime!={n:digest(ROOT/n) for n in runtime}:raise ValueError('Runtime changed during replay')
    output.mkdir(parents=True,exist_ok=False)
    files={};summary={}
    for split,rows in chosen.items():
        path=output/(split+'.pending.jsonl')
        with path.open('x') as f:
            for r in rows:f.write(json.dumps(pending_record(r),ensure_ascii=False,sort_keys=True)+'\n')
        files[split]=dict(path=path.name,sha256=digest(path),roots=len(rows))
        summary[split]=dict(strata=dict(Counter(r['stratum'] for r in rows)),runs=len({r['run'] for r in rows}),
                            games=len({(r['run'],r['game']) for r in rows}),max_roots_per_run=max(Counter(r['run'] for r in rows).values()))
    report=dict(schema='rakuyou-teacher-refresh-preparation-v1',plan_sha256=digest(plan_path),
                preparation_manifest_sha256=digest(manifest_path),runtime_sha256=runtime,
                probe_sha256=digest(probe_path),tool_sha256=digest(Path(__file__)),
                files=files,summary=summary,searches_executed=0,real_data_updates=0,
                test_roots_selected=0,training_ready=False,teacher_generation_ready=False,deployed=False)
    with (output/'manifest.json').open('x') as f:
        json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path)
    p.add_argument('--plan',type=Path,default=ROOT/'docs/experiments/configs/teacher-refresh-v1.json')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=prepare(a.manifest,a.plan,a.output)
    print(json.dumps(r['summary'],indent=2))


if __name__=='__main__':main()
