"""Read-only checkpoint diagnosis and one hypothetical feasible direction.

Does not save a candidate, train repeatedly, search, or deploy. Cyclic halfspace
corrections are a feasibility prototype, not an exact quadratic-program solver.
"""
import math

from tools.learning.hybrid import data, objective, runner

OUTPUT = data.ROOT/'results/learning-pilot/2026-10-17-constraint-audit-v1'


def dot(a, b):
    return math.fsum(v*b[k] for k,v in a.items())


def direction(rows, delta, gradient, limit=100., coefficient_limit=.5):
    maximum = max(map(abs, gradient.values()), default=0.)
    if maximum == 0: return dict.fromkeys(delta, 0.), 0
    vector = {k:-v/maximum for k,v in gradient.items()}
    # Active constraints only determine direction; every constraint is checked
    # again when choosing the finite step below.
    planes = []
    for row in rows:
        impact = dot(row['factors'], delta)
        if abs(impact) >= limit-1e-6:
            sign = 1 if impact >= 0 else -1
            planes.append({k:sign*v for k,v in row['factors'].items()})
    bounds = [(k,1 if v>=0 else -1) for k,v in delta.items()
              if abs(v)>=coefficient_limit-1e-9]
    for sweep in range(1000):
        for plane in planes:
            violation = dot(plane, vector)
            if violation>0:
                scale = violation/math.fsum(v*v for v in plane.values())
                for k,v in plane.items(): vector[k]-=scale*v
        for k,sign in bounds:
            if sign*vector[k]>0: vector[k]=0.
        residual=max([0.]+[dot(p,vector) for p in planes])
        if residual<=1e-10: return vector, sweep+1
    raise ValueError('Direction feasibility did not converge')


def feasible_step(rows, delta, vector, limit=100., coefficient_limit=.5, step=.02):
    ceilings=[]
    for value,rate,bound in (
        [(delta[k],vector[k],coefficient_limit) for k in delta]+
        [(dot(r['factors'],delta),dot(r['factors'],vector),limit) for r in rows]):
        if abs(value)>bound: raise ValueError('Infeasible starting checkpoint')
        if rate>0: ceilings.append((bound-value)/rate)
        elif rate<0: ceilings.append((-bound-value)/rate)
    return min([step]+[max(0.,c)*.99 for c in ceilings])


def audit_arm(rows, state, alpha, config):
    delta=state['delta'];before,g=objective.objective(rows,delta,alpha,config['l2'])
    impacts=[dict(id=r['id'],side=r['side'],target=r['target'],
                  impact_cp=dot(r['factors'],delta)) for r in rows]
    impacts.sort(key=lambda r:abs(r['impact_cp']),reverse=True)
    v,sweeps=direction(rows,delta,g,config['train_position_limit_cp'],config['delta_limit_cp'])
    step=feasible_step(rows,delta,v,config['train_position_limit_cp'],config['delta_limit_cp'],config['step_cp'])
    candidate={k:delta[k]+step*v[k] for k in delta}
    after,_=objective.objective(rows,candidate,alpha,config['l2'])
    max_position=max(abs(dot(r['factors'],candidate)) for r in rows)
    max_coefficient=max(map(abs,candidate.values()))
    if max_position>config['train_position_limit_cp'] or max_coefficient>config['delta_limit_cp']:
        raise ValueError('Hypothetical step violated a bound')
    return dict(updates=state['updates'],top_impacts=impacts[:5],
                active_positions=sum(abs(r['impact_cp'])>=100-1e-6 for r in impacts),
                active_coefficients=sum(abs(v)>=.5-1e-9 for v in delta.values()),
                direction_sweeps=sweeps,gradient_dot_direction=dot(g,v),
                hypothetical_step=step,loss_before=before,loss_after=after,
                improvement=before-after,max_position_cp=max_position,
                max_coefficient_cp=max_coefficient,
                feasible_improvement=step>0 and after<before)


def main():
    source=data.DEFAULT_OUTPUT
    plan,dataset=data.load_dataset(source)
    teachers=data.load_teachers(source,plan,dataset['rows'])
    parts,_,_=runner.cohort(dataset,teachers)
    names=['plan.json','dataset.json','teachers.json']+[a+'/checkpoint.json' for a in runner.ARMS]
    bindings={n:data.digest(source/n) for n in names}
    results={}
    for arm,alpha in runner.ARMS.items():
        state=runner.unseal(source/arm/'checkpoint.json')
        results[arm]=audit_arm(parts['train'],state,alpha,plan['training'])
        print(arm, results[arm], flush=True)
    if bindings!={n:data.digest(source/n) for n in names}: raise ValueError('Source changed')
    OUTPUT.mkdir(parents=True,exist_ok=False)
    runner.seal(OUTPUT/'report.json',dict(schema='constraint-direction-audit-v1',
        source=str(source),inputs_sha256=bindings,
        code_sha256={n:data.digest(data.ROOT/n) for n in
                     ['tools/learning/constraints/audit.py','tools/learning/hybrid/objective.py']},
        train_positions=len(parts['train']),arms=results,
        candidate_saved=False,validation_used=False,searches=0,training_runs=0))


if __name__=='__main__': main()
