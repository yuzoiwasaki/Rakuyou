"""Legacy coefficient clipping, followed by position-bound correction if needed.

Cyclic corrections are a bounded feasibility heuristic, not an exact projection.
Only an actually feasible, strictly improving training step can be accepted.
"""
import math
from tools.learning.hybrid.objective import finite, objective
from tools.learning.constraints.optimizer import dot, REASONS

OPTIONS = dict(max_sweeps=1000, interior_margin=1e-8)


def correct(rows, delta, candidate, amount, coefficient_limit, position_limit,
            max_sweeps, interior_margin):
    # Include the step box so correction cannot silently enlarge the step budget.
    lower={k:max(-coefficient_limit,x-amount) for k,x in delta.items()}
    upper={k:min(coefficient_limit,x+amount) for k,x in delta.items()}
    candidate=dict(candidate)
    norms=[math.fsum(v*v for v in r['factors'].values()) for r in rows]
    for sweep in range(1,max_sweeps+1):
        for row,norm in zip(rows,norms):
            impact=dot(row['factors'],candidate)
            if abs(impact)>position_limit-interior_margin:
                target=math.copysign(position_limit-interior_margin,impact)
                for k,v in row['factors'].items(): candidate[k]-=(impact-target)*v/norm
        candidate={k:max(lower[k],min(upper[k],v)) for k,v in candidate.items()}
        if all(abs(dot(r['factors'],candidate))<=position_limit for r in rows):
            return candidate,sweep
    return None,max_sweeps


def propose_step(rows,delta,alpha,*,l2=1e-6,step_cp=.02,delta_limit_cp=.5,
                 train_position_limit_cp=100.,max_backtracks=20,
                 max_sweeps=1000,interior_margin=1e-8):
    for name,value in [('step',step_cp),('coefficient cap',delta_limit_cp),
                       ('position cap',train_position_limit_cp),('margin',interior_margin)]:
        if finite(value,name)<=0: raise ValueError(name+' must be positive')
    if interior_margin>=train_position_limit_cp: raise ValueError('Margin exceeds cap')
    if type(max_sweeps) is not int or max_sweeps<1 or type(max_backtracks) is not int or max_backtracks<0:
        raise ValueError('Invalid iteration budget')
    before,g=objective(rows,delta,alpha,l2)
    initial=max(abs(dot(r['factors'],delta)) for r in rows)
    if initial>train_position_limit_cp or any(abs(x)>delta_limit_cp for x in delta.values()):
        raise ValueError('Infeasible initial delta')
    maximum=max(map(abs,g.values()),default=0.)
    result=dict(delta=dict(delta),loss_before=before,loss_after=before,accepted=False,
                step_cp=0.,backtracks=0,gradient_max=maximum,max_train_change_cp=initial,
                cap_hits=0,stopping_reason='zero_gradient',correction_sweeps=0,
                correction_attempts=0,correction_used=False)
    if maximum==0: return result
    feasible_trials=0
    for backtrack in range(max_backtracks+1):
        amount=step_cp*2.**(-backtrack)
        proposed={k:x-amount*(g[k]/maximum) for k,x in delta.items()}
        hits=sum(abs(x)>delta_limit_cp for x in proposed.values())
        candidate={k:max(-delta_limit_cp,min(delta_limit_cp,x)) for k,x in proposed.items()}
        used=max(abs(dot(r['factors'],candidate)) for r in rows)>train_position_limit_cp
        if used:
            result['correction_attempts']+=1
            candidate,sweeps=correct(rows,delta,candidate,amount,delta_limit_cp,
                                    train_position_limit_cp,max_sweeps,interior_margin)
            result['correction_sweeps']+=sweeps
            if candidate is None: continue
        feasible_trials+=1
        impact=max(abs(dot(r['factors'],candidate)) for r in rows)
        if impact>train_position_limit_cp or any(abs(x)>delta_limit_cp for x in candidate.values()):
            raise ValueError('Correction produced infeasible trial')
        after,_=objective(rows,candidate,alpha,l2)
        if after<before:
            result.update(delta=candidate,loss_after=after,accepted=True,step_cp=amount,
                          backtracks=backtrack,max_train_change_cp=impact,cap_hits=hits,
                          stopping_reason=None,correction_used=used)
            return result
    result.update(backtracks=max_backtracks,stopping_reason=(
        'no_acceptable_improvement' if feasible_trials else 'direction_iteration_limit'))
    return result
