"""Frozen-leaf KP/PP move imitation arithmetic; no optimizer or search entry."""
import math
import subprocess
from pathlib import Path
from tools.learning.data.prepare_learning_data import ROOT

PROBE=ROOT/'results/imitation-tools/imitation-probe'
SCALE=65536
TEMPERATURE_CP=600.0


def native(sfens,delta_file=None):
    command=[str(PROBE),'--features-sfen',str(ROOT/'bin/params.bin')]
    if delta_file is not None:command.append(str(delta_file))
    result=subprocess.run(command,input='\n'.join(sfens)+'\n',capture_output=True,text=True,check=True,timeout=30)
    import json
    rows=[json.loads(line) for line in result.stdout.splitlines()]
    if len(rows)!=len(sfens):raise ValueError('Native feature frame count mismatch')
    return rows


def transformed(sfen,rotate=False):
    pieces={}
    board,side,hands,*rest=sfen.split()
    for rank,row in enumerate(board.split('/')):
        file=9;promoted=False
        for c in row:
            if c.isdigit():file-=int(c);continue
            if c=='+':promoted=True;continue
            x,y=(10-file,8-rank) if rotate else (10-file,rank)
            pieces[(x,y)]=('+' if promoted else '')+(c.swapcase() if rotate else c)
            file-=1;promoted=False
    rows=[]
    for y in range(9):
        row='';empty=0
        for x in range(9,0,-1):
            p=pieces.get((x,y))
            if p:row+=(str(empty) if empty else '')+p;empty=0
            else:empty+=1
        rows.append(row+(str(empty) if empty else ''))
    if rotate:
        side='w' if side=='b' else 'b'
        # Canonical SFEN hands order: first uppercase, then lowercase.
        import re
        tokens=re.findall(r'(\d*)([A-Za-z])',hands)
        counts={p.swapcase():n for n,p in tokens}
        hands=''.join(counts[p]+p for p in 'RBGSNLPrbgsnlp' if p in counts) or '-'
    return '/'.join(rows)+' '+side+' '+hands+' 1'


def factors(frame,root_side='white'):
    p=int(frame['progress']*SCALE)/SCALE
    kp=(1-2*p,2*p,0.0) if p<.5 else (0.0,2-2*p,2*p-1)
    sign=1 if root_side=='black' else -1
    result={}
    for type_,a,b,count in frame['features']:
        stages=enumerate(kp) if type_==0 else ((0,1-p),(2,p))
        for lane,weight in stages:
            if weight:result[f'{type_}:{a}:{b}:{lane}']=sign*count*weight
    return result


def root_cp(frame,side='white'):
    return frame['eval_on']*(1 if (frame['sfen'].split()[1]=='b')==(side=='black') else -1)


def pair_record(actual,alternative):
    a=factors(actual);b=factors(alternative)
    differences={k:b.get(k,0)-a.get(k,0) for k in a.keys()|b.keys()}
    return dict(base_gap=root_cp(alternative)-root_cp(actual),
                factors={k:v for k,v in sorted(differences.items()) if v})


def objective(pairs,delta,l2=0):
    if not pairs:raise ValueError('No usable move pairs')
    if l2<0 or any(not math.isfinite(v) for v in delta.values()):raise ValueError('Invalid objective state')
    loss=0;gradient={k:l2*v for k,v in delta.items()}
    for pair in pairs:
        gap=pair['base_gap']+math.fsum(v*delta.get(k,0) for k,v in pair['factors'].items())
        x=gap/TEMPERATURE_CP
        loss+=max(x,0)+math.log1p(math.exp(-abs(x)))
        probability=1/(1+math.exp(-x)) if x>=0 else math.exp(x)/(1+math.exp(x))
        for k,v in pair['factors'].items():gradient[k]=gradient.get(k,0)+probability*v/(len(pairs)*TEMPERATURE_CP)
    return loss/len(pairs)+.5*l2*math.fsum(v*v for v in delta.values()),gradient


def write_delta(path,raw):
    path=Path(path)
    if not path.resolve().is_relative_to((ROOT/'results').resolve()):raise ValueError('Delta output must be ignored results')
    for k,v in raw.items():
        t,a,b,lane=map(int,k.split(':'))
        if (type(v) is not int or abs(v)>32768 or t not in (0,1)
            or lane not in ((0,1,2) if t==0 else (0,2))):raise ValueError('Invalid bounded sparse delta')
    with path.open('x') as f:
        for k,v in sorted(raw.items()):f.write(k.replace(':',' ')+f' {v}\n')
