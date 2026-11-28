#!/usr/bin/env python3
"""Post-game shadow audit: actual attack vs auto defenses, without changing the game."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.analysis.analyze_positions import Engine
from tools.analysis.defense_move_audit import classify_lines
from tools.analysis.defense_preference_audit import select


def summarize_case(actual, candidates, defense):
    if not candidates or any(c['depth'] != 18 for c in candidates):
        return dict(kind='incomplete-depth',selected=None)
    decision=select(candidates,defense,[actual],True)
    if decision['selected'] is None:
        return dict(kind='incomparable-scores',decision=decision)
    lookup={c['pv'][0]:c for c in candidates}
    best_def=max(defense,key=lambda m:int(lookup[m]['score']))
    attack_score=int(lookup[actual]['score']);defense_score=int(lookup[best_def]['score'])
    if decision['selected'] == actual:
        kind='keep-actual'
    elif decision['best'] == actual:
        kind='within50-switch'
    else:
        kind='research-already-prefers-defense'
    return dict(kind=kind,actual_score=attack_score,defense=best_def,
                defense_score=defense_score,gap=attack_score-defense_score,decision=decision)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True)
    p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();data=json.loads(args.game.read_text());game=data['games'][0]
    if game['status'] not in ('completed','unresolved'):
        p.error('Finish the game before auditing; do not compete with timed search')
    records=[r for r in game['records'] if r['player']=='shin' and r['source']=='search'
             and 32<=r['ply']<=100 and r['move'] not in ('resign','win')]
    positions=[game['moves'][:r['ply']-1] for r in records]
    roles=classify_lines(['moves '+' '.join(m) for m in positions])
    output=dict(game=str(args.game),engine=str(args.engine),scope='White searched moves32..100, actual move labeled attack; phase needs human review',
                depth=18,threshold=50,live_policy=False,cases=[],screened=[])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(output,indent=2)+'\n')
    for record,moves,mapping in zip(records,positions,roles):
        actual=record['move'];role=mapping[actual]['role']
        defense=[m for m,v in mapping.items() if v['role']=='defense']
        output['screened'].append(dict(ply=record['ply'],actual=actual,role=role,defense=defense))
        save()
        if role!='attack' or not defense:continue
        pool=[actual]+defense
        e=Engine(args.engine,1,512,len(pool),True)
        try:a=e.analyze(moves,18,65,searchmoves=pool,stop_after=55,multipv=len(pool))
        finally:e.close()
        candidates=a['candidates']
        if {c['pv'][0] for c in candidates}!=set(pool):raise ValueError('Incomplete candidate pool')
        result=summarize_case(actual,candidates,defense)
        row=dict(ply=record['ply'],moves=moves,actual=actual,game_analysis=record['analysis'],roles={m:mapping[m] for m in pool},
                 phase_status='manual-review-required',candidate_scope='actual attack plus all auto defenses',analysis=a,result=result)
        output['cases'].append(row);save()
        print(record['ply'],actual,result,flush=True)


if __name__=='__main__': main()
