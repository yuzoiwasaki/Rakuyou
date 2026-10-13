"""Stable winner-label logistic loss on baseline-plus-sparse-delta; no updates."""
import math
GAIN=1/600


def supervised(rows):
    result=[]
    for row in rows:
        target=row['target'];enabled=row['use_outcome_loss']
        if type(enabled) is not bool:raise ValueError('Boolean loss mask required')
        if not enabled:
            if target is not None:raise ValueError('Masked outcomes must not carry targets')
            continue
        if target not in (0.0,1.0) or type(target) not in (int,float):raise ValueError('Verified decisive0/1 outcome required')
        if not math.isfinite(row['base_cp']) or any(not math.isfinite(v) for v in row['factors'].values()):raise ValueError('Nonfinite sample')
        result.append(row)
    return result


def objective(rows,delta,l2=0):
    rows=supervised(rows)
    if not rows:raise ValueError('No supervised outcome samples')
    if not math.isfinite(l2) or l2<0 or any(not math.isfinite(v) for v in delta.values()):raise ValueError('Invalid objective state')
    gradient={k:l2*v for k,v in delta.items()};loss=0
    for row in rows:
        cp=row['base_cp']+math.fsum(v*delta.get(k,0) for k,v in row['factors'].items());z=GAIN*cp
        # softplus(-z) for win, softplus(z) for loss; stable at large scores.
        signed=z if row['target']==0 else -z
        loss+=max(signed,0)+math.log1p(math.exp(-abs(signed)))
        probability=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))
        d=GAIN*(probability-row['target'])/len(rows)
        for k,v in row['factors'].items():gradient[k]=gradient.get(k,0)+d*v
    return loss/len(rows)+.5*l2*math.fsum(v*v for v in delta.values()),gradient
