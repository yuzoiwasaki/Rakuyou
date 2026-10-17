"""Feasible descent with active-bound direction correction and train-only acceptance.

Cyclic halfspace corrections find a feasible direction, not an exact projection.
A numerical stop is never claimed to prove constrained convergence.
"""
import math
from tools.learning.hybrid.objective import finite, objective

OPTIONS = dict(active_position_tolerance=1e-6, active_coefficient_tolerance=1e-6,
               direction_tolerance=1e-10, max_sweeps=1000, minimum_step=1e-12)
REASONS = {'zero_gradient', 'direction_iteration_limit', 'no_descent_direction',
           'step_too_small', 'no_acceptable_improvement', 'update_budget'}


def dot(a, b):
    return math.fsum(v*b[k] for k,v in a.items())


def propose_step(rows, delta, alpha, *, l2=1e-6, step_cp=.02,
                 delta_limit_cp=.5, train_position_limit_cp=100., max_backtracks=20,
                 active_position_tolerance=1e-6, active_coefficient_tolerance=1e-6,
                 direction_tolerance=1e-10, max_sweeps=1000, minimum_step=1e-12):
    for name,value in [('step',step_cp),('coefficient cap',delta_limit_cp),
                       ('position cap',train_position_limit_cp),('minimum step',minimum_step),
                       ('position tolerance',active_position_tolerance),
                       ('coefficient tolerance',active_coefficient_tolerance),
                       ('direction tolerance',direction_tolerance)]:
        if finite(value,name)<=0: raise ValueError(name+' must be positive')
    if active_position_tolerance>=train_position_limit_cp or active_coefficient_tolerance>=delta_limit_cp:
        raise ValueError('Active tolerance must be smaller than cap')
    if type(max_sweeps) is not int or max_sweeps<1 or type(max_backtracks) is not int or max_backtracks<0:
        raise ValueError('Invalid iteration budget')
    before,g=objective(rows,delta,alpha,l2)
    impacts=[dot(r['factors'],delta) for r in rows]
    if max(map(abs,delta.values()),default=0)>delta_limit_cp or max(map(abs,impacts))>train_position_limit_cp:
        raise ValueError('Infeasible initial delta')
    maximum=max(map(abs,g.values()),default=0.)
    result=dict(delta=dict(delta),accepted=False,loss_before=before,loss_after=before,
                step_cp=0.,backtracks=0,gradient_max=maximum,max_train_change_cp=max(map(abs,impacts)),
                cap_hits=0,direction_sweeps=0,stopping_reason='zero_gradient')
    if maximum==0: return result
    v={k:-x/maximum for k,x in g.items()}
    planes=[{k:(1 if impact>=0 else -1)*x for k,x in r['factors'].items()}
            for r,impact in zip(rows,impacts)
            if abs(impact)>=train_position_limit_cp-active_position_tolerance]
    norms=[math.fsum(x*x for x in p.values()) for p in planes]
    bounds=[(k,1 if x>=0 else -1) for k,x in delta.items()
            if abs(x)>=delta_limit_cp-active_coefficient_tolerance]
    result.update(active_positions=len(planes),active_coefficients=len(bounds))
    for sweep in range(max_sweeps):
        for p,norm in zip(planes,norms):
            violation=dot(p,v)
            if violation>0:
                for k,x in p.items(): v[k]-=violation*x/norm
        for k,sign in bounds:
            if sign*v[k]>0: v[k]=0.
        if max([0.]+[dot(p,v) for p in planes])<=direction_tolerance: break
    else:
        result.update(stopping_reason='direction_iteration_limit',direction_sweeps=max_sweeps)
        return result
    result['direction_sweeps']=sweep+1
    # Preserve the original maximum per-coefficient step scale after correction.
    scale=max(1.,max(map(abs,v.values()),default=0.))
    v={k:x/scale for k,x in v.items()}
    slope=dot(g,v);result['gradient_dot_direction']=slope
    if not math.isfinite(slope) or slope>=0:
        result['stopping_reason']='no_descent_direction';return result
    amount=step_cp
    constraints=[(delta[k],v[k],delta_limit_cp) for k in delta]
    constraints.extend((impact,dot(r['factors'],v),train_position_limit_cp) for r,impact in zip(rows,impacts))
    for value,rate,bound in constraints:
        if rate:
            distance=((bound-value) if rate>0 else (-bound-value))/rate
            amount=min(amount,max(0.,distance)*.99)
    for backtrack in range(max_backtracks+1):
        result['backtracks']=backtrack
        if amount<minimum_step:
            result['stopping_reason']='step_too_small';return result
        candidate={k:x+amount*v[k] for k,x in delta.items()}
        impact=max(abs(dot(r['factors'],candidate)) for r in rows)
        if max(map(abs,candidate.values()),default=0)<=delta_limit_cp and impact<=train_position_limit_cp:
            after,_=objective(rows,candidate,alpha,l2)
            # Armijo decrease plus a strict decrease avoids accepting rounded ties.
            if after<before and after<=before+1e-4*amount*slope:
                result.update(delta=candidate,accepted=True,loss_after=after,step_cp=amount,
                              max_train_change_cp=impact,stopping_reason=None)
                return result
        amount*=.5
    result['stopping_reason']='no_acceptable_improvement'
    return result
