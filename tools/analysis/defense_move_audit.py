#!/usr/bin/env python3
"""Automatic role diagnostics only; phase/initiative eligibility remains external."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def classify_lines(lines):
    run=subprocess.run([str(ROOT/'results/defense-move-tools/native-test'),str(ROOT/'bin/params.bin')],
                       input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True,timeout=60)
    output=[{} for _ in lines]
    for line in run.stdout.splitlines():
        i,move,role,blockade,exposed,links,threats=line.split()
        output[int(i)][move]=dict(role=role,blockade=bool(int(blockade)),exposed=bool(int(exposed)),
                                  links=links.split(':')[1:],threats=threats.split(':')[1:])
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixtures',type=Path,default=ROOT/'test/analysis/defense_move_positions.json')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();fixtures=json.loads(args.fixtures.read_text())
    roles=classify_lines(['moves '+' '.join(f['moves']) for f in fixtures])
    output=[dict(id=f['id'],moves=f['moves'],roles=r) for f,r in zip(fixtures,roles)]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    for row in output:
        print(row['id'],'defense:',[m for m,v in row['roles'].items() if v['role']=='defense'])


if __name__=='__main__': main()
