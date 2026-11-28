#!/usr/bin/env python3
"""One-pass MultiPV role/selection trial. No deeper confirmation or live policy."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.analysis.analyze_positions import Engine
from tools.analysis.defense_move_audit import classify_lines
from tools.analysis.defense_preference_audit import select


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=Path,required=True)
    p.add_argument('--fixtures',type=Path,default=ROOT/'test/analysis/automatic_defense_positions.json')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();fixtures=json.loads(args.fixtures.read_text());rows=[]
    roles=classify_lines(['moves '+' '.join(f['moves']) for f in fixtures])
    for f,r in zip(fixtures,roles):
        e=Engine(args.engine,1,512,min(8,len(r)),True)
        try:a=e.analyze(f['moves'],18,60,stop_after=50,multipv=min(8,len(r)))
        finally:e.close()
        candidates=a['candidates']
        defense=[m for m,v in r.items() if v['role']=='defense']
        attacks=[m for m,v in r.items() if v['role']=='attack']
        # Early stops are recorded, not used to fabricate a depth18 decision.
        decision=select(candidates,defense,attacks,f['eligible']) if all(c['depth']==18 for c in candidates) else dict(selected=None,reason='target-depth-not-completed')
        row=dict(id=f['id'],moves=f['moves'],eligibility='manual-for-diagnostic',roles=r,analysis=a,decision=decision)
        rows.append(row);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(rows,indent=2)+'\n')
        print(f['id'],[(c['pv'][0],c['score'],r[c['pv'][0]]['role']) for c in candidates],decision,flush=True)


if __name__=='__main__': main()
