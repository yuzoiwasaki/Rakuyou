"""Train-only gradient decomposition and hypothetical step diagnostics; no updates."""
import json
import math
from collections import Counter
from pathlib import Path
from tools.learning.constraints import temporal_mixed as mixed
from tools.learning.constraints import temporal_runner as base
from tools.learning.constraints.weighted_objective import objective,sigmoid

OUTPUT=base.data.ROOT/'results/learning-pilot/2026-10-19-gradient-conflict-v1'


def dot(a,b):return math.fsum(v*b.get(k,0.) for k,v in a.items())
def norm(a):return math.sqrt(dot(a,a))
def cosine(a,b):
    denominator=norm(a)*norm(b)
    return dot(a,b)/denominator if denominator else None


def groups(rows,delta,alpha):
    counts=Counter((r['run'],r['game']) for r in rows)
    gradients={g:{} for g in ('original','additional','win','loss')}
    for r in rows:
        weight=1/(len(counts)*counts[r['run'],r['game']])
        score=r['base_cp']+dot(r['factors'],delta)
        target=(1-alpha)*sigmoid(r['teacher_cp']/600)+alpha*r['target']
        derivative=weight*(sigmoid(score/600)-target)/600
        for group in (r['cohort'],'win' if r['target'] else 'loss'):
            g=gradients[group]
            for k,v in r['factors'].items():g[k]=g.get(k,0.)+derivative*v
    return gradients


def diagnose(rows,delta,alpha,config):
    loss,g=objective(rows,delta,alpha,config['l2'])
    gs=groups(rows,delta,alpha);outcome=groups(rows,delta,1.)
    for left,right in [('original','additional'),('win','loss')]:
        error=max(abs(gs[left].get(k,0)+gs[right].get(k,0)+config['l2']*v-g[k]) for k,v in delta.items())
        if error>1e-12:raise ValueError('Group gradients do not reconstruct training gradient')
    maximum=max(map(abs,g.values()));amount=config['step_cp'];cap=config['delta_limit_cp'];limit=config['train_position_limit_cp']
    raw={k:v-amount*g[k]/maximum for k,v in delta.items()}
    clipped={k:max(-cap,min(cap,v)) for k,v in raw.items()}
    result=dict(loss=loss,group_norms={k:norm(v) for k,v in gs.items()},
        win_loss_cosine=cosine(gs['win'],gs['loss']),original_additional_cosine=cosine(gs['original'],gs['additional']),
        coefficient_clips=sum(abs(v)>cap for v in raw.values()),
        raw_position_violations=sum(abs(dot(r['factors'],raw))>limit for r in rows),
        clipped_position_violations=sum(abs(dot(r['factors'],clipped))>limit for r in rows),
        current_positions_near_cap=sum(abs(dot(r['factors'],delta))>=limit-.01 for r in rows),
        current_coefficients_at_cap=sum(abs(v)>=cap-1e-10 for v in delta.values()))
    candidates={'raw':raw,'coefficient_clipped':clipped}
    if result['clipped_position_violations']:
        corrected,sweeps=base.optimizer.correct(rows,delta,clipped,amount,cap,limit,**base.optimizer.OPTIONS)
        result['correction_sweeps']=sweeps
        if corrected is not None:candidates['position_corrected']=corrected
    else:candidates['position_corrected']=clipped;result['correction_sweeps']=0
    steps={}
    for name,candidate in candidates.items():
        direction={k:candidate[k]-v for k,v in delta.items()}
        actual_loss,_=objective(rows,candidate,alpha,config['l2'])
        steps[name]=dict(norm=norm(direction),cosine_to_raw=cosine(direction,{k:raw[k]-v for k,v in delta.items()}),
            total_first_order_change=dot(g,direction),actual_loss_change=actual_loss-loss,
            group_first_order_change={k:dot(v,direction) for k,v in gs.items()},
            outcome_group_first_order_change={k:dot(v,direction) for k,v in outcome.items()},
            max_position_change=max(abs(dot(r['factors'],candidate)) for r in rows))
    result['hypothetical_steps']=steps
    return result


def run():
    plan,_,_,parts,_=mixed.load();rows=parts['train']
    report={};bindings={}
    for name,path,alpha in [('search',base.OUTPUT/'search/checkpoint.json',0.),('mixed',mixed.OUTPUT/'mixed/checkpoint.json',.5)]:
        state=base.old.unseal(path);bindings[str(path.relative_to(base.data.ROOT))]=base.data.digest(path)
        for label,delta in [('zero',{k:0. for k in plan['keys']}),('final',state['delta'])]:
            print(name,label,flush=True)
            report[name+'-'+label]=diagnose(rows,delta,alpha,plan['training'])
    OUTPUT.mkdir(parents=True,exist_ok=False);p=OUTPUT/'audit.json'
    base.old.seal(p,dict(reports=report,checkpoints_sha256=bindings,
        mixed_plan_sha256=base.data.digest(mixed.OUTPUT/'plan.json'),code_sha256=base.data.digest(Path(__file__)),
        scope='Train750 only; full cohort weights retained in group contributions. Hypothetical steps never saved as candidates. No training, search or deployment.'))
    for name,r in report.items():
        print(name,'cos win/loss',r['win_loss_cosine'],'original/added',r['original_additional_cosine'],
              'clips',r['coefficient_clips'],'position violations',r['clipped_position_violations'])
        for step,v in r['hypothetical_steps'].items():print(step,'norm',v['norm'],'cos',v['cosine_to_raw'],'group',v['group_first_order_change'],'outcome',v['outcome_group_first_order_change'])
    print('SHA',base.data.digest(p))


if __name__=='__main__':run()
