"""Bounded hypothetical common-descent check, train-only; never saves a candidate."""
from pathlib import Path
from tools.learning.constraints import conflict_audit as audit
from tools.learning.constraints.weighted_objective import objective

OUTPUT=audit.base.data.ROOT/'results/learning-pilot/2026-10-20-common-direction-v1'
MAX_BACKTRACKS=6


def losses(rows,delta,l2):
    result={'total_mixed_l2':objective(rows,delta,.5,l2)[0]}
    for group,target in [('win',1),('loss',0)]:
        selected=[r for r in rows if r['target']==target]
        for name,alpha in [('mixed',.5),('outcome',1.)]:
            result[group+'_'+name]=objective(selected,delta,alpha,0.)[0]
    return result


def check(rows,delta,config):
    before=losses(rows,delta,config['l2'])
    _,mean=objective(rows,delta,.5,config['l2'])
    gs=audit.groups(rows,delta,.5);norms={g:audit.norm(gs[g]) for g in ('win','loss')}
    balanced={k:sum(gs[g].get(k,0.)/norms[g] for g in norms if norms[g]) for k in delta}
    results={}
    for name,gradient in [('mean',mean),('unit_group_sum',balanced)]:
        maximum=max(map(abs,gradient.values()),default=0.)
        trials=[]
        if maximum:
            for backtrack in range(MAX_BACKTRACKS+1):
                amount=config['step_cp']*2**(-backtrack);cap=config['delta_limit_cp'];limit=config['train_position_limit_cp']
                raw={k:v-amount*gradient[k]/maximum for k,v in delta.items()}
                clipped={k:max(-cap,min(cap,v)) for k,v in raw.items()}
                corrected=any(abs(audit.dot(r['factors'],clipped))>limit for r in rows)
                sweeps=0
                if corrected:
                    candidate,sweeps=audit.base.optimizer.correct(rows,delta,clipped,amount,cap,limit,**audit.base.optimizer.OPTIONS)
                else:candidate=clipped
                if candidate is None:
                    trials.append(dict(backtrack=backtrack,feasible=False));continue
                impact=max(abs(audit.dot(r['factors'],candidate)) for r in rows)
                step=max(abs(candidate[k]-v) for k,v in delta.items())
                if impact>limit or max(map(abs,candidate.values()))>cap or step>amount+1e-12:
                    raise ValueError('Feasibility correction violated limits')
                after=losses(rows,candidate,config['l2']);changes={k:after[k]-v for k,v in before.items()}
                success=all(v < -1e-12 for v in changes.values())
                trials.append(dict(backtrack=backtrack,feasible=True,amount=amount,max_coefficient_step=step,
                    max_position_impact=impact,correction_used=corrected,correction_sweeps=sweeps,
                    changes=changes,common_improvement=success))
                if success:break
        results[name]=dict(found=any(t.get('common_improvement',False) for t in trials),trials=trials)
    return dict(before=before,methods=results)


def run():
    plan,_,_,parts,_=audit.mixed.load();path=audit.mixed.OUTPUT/'mixed/checkpoint.json'
    state=audit.base.old.unseal(path)
    binding=dict(plan_sha256=audit.base.data.digest(audit.mixed.OUTPUT/'plan.json'),method='projected',arm='mixed',alpha=.5)
    audit.base.validate(state,plan['keys'],binding,plan['training'],parts['train'])
    results={}
    for name,delta in [('zero',{k:0. for k in plan['keys']}),('final',state['delta'])]:
        print(name,flush=True);results[name]=check(parts['train'],delta,plan['training'])
    OUTPUT.mkdir(parents=True,exist_ok=False);target=OUTPUT/'audit.json'
    audit.base.old.seal(target,dict(results=results,max_backtracks=MAX_BACKTRACKS,
        checkpoint_sha256=audit.base.data.digest(path),plan_sha256=binding['plan_sha256'],
        code_sha256={str(p.relative_to(audit.base.data.ROOT)):audit.base.data.digest(p) for p in [Path(__file__),Path(audit.__file__)]},
        scope='Train-only local trials: both group mixed CE, both group outcome CE, and global mixed+L2 must strictly decrease. No checkpoint updated or candidate saved; failure is not infeasibility proof.'))
    for name,r in results.items():
        for method,v in r['methods'].items():print(name,method,v)
    print('SHA',audit.base.data.digest(target))


if __name__=='__main__':run()
