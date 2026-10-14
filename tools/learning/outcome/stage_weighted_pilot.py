#!/usr/bin/env python3
"""One fixed20-update progress-weighted256/64 pilot; all validation stays unweighted."""
import sys,json,math,argparse
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from tools.learning.outcome.outcome_objective import supervised
from tools.learning.outcome.stage_weighted_objective import objective,training_samples
from tools.learning.outcome.expanded_outcome_pilot import load as load_baseline
from tools.learning.imitation import sparse_updater as u
from tools.learning.imitation.sparse_objective import native,root_cp,factors,write_delta
from tools.learning.data.prepare_learning_data import ROOT,digest
from tools.learning.core.learning_backup import verify_backup,create_backup
from tools.learning.tempo.run_tempo_search import write_report

PREP=ROOT/'results/learning-pilot/2026-10-14-outcome-expanded-preparation-v1'
PREP_SHA='1034b6b043f079463b27e65724d016c08ceedb38f069064c6c6b58d0f0cc62c0'
AUDIT_SHA='afd61f4f96ebcff7534af60d1b0630cca5d7b4bd8e290b211058affa069365a9'
PARENT=ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
MARKER=PREP/'stage-weighted-attempt-v1.json'
COMPARISON=ROOT/'results/learning-pilot/2026-10-14-outcome-expanded-run-v1'
COMPARISON_SHA='4e56b5c65dd751b8875480ab93238e5e90d02452a0c4469932a809600efa7241'


def load():
    prep=load_baseline()
    if digest(COMPARISON/'report.json')!=COMPARISON_SHA:raise ValueError('Comparison result changed')
    audit=json.loads((COMPARISON/'audit.json').read_bytes())
    if not audit['accepted'] or audit['report_sha256']!=COMPARISON_SHA:raise ValueError('Comparison audit changed')
    training_samples(prep['records']['train'])
    return prep


from tools.learning.outcome.outcome_pilot import summarize,evaluate


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():raise ValueError('New ignored output required')
    if MARKER.exists():raise ValueError('Outcome learning already started/closed')
    prep=load();keys=prep['binding']['active_keys'];train=training_samples(prep['records']['train']);output.mkdir(parents=True,exist_ok=False)
    plan=dict(preparation_sha256=PREP_SHA,audit_sha256=AUDIT_SHA,config=u.CONFIG,full_batch_supervised=256,
        target='verified decisive winner relative to Shin root side',draw_loss_enabled=False,separate_old_white_draw_diagnostic=6,
        selected_update=20,selection='fixed20 averaged candidate, no reselection',max_position_cp_change=10,
        training_enabled=True,deployment_enabled=False,comparison_sha256=COMPARISON_SHA,
        weighting='w=.25+.75*saved_progress; normalize within each of four64 training strata',
        validation_weighting='unchanged equal weights',
        training_weights=[dict(id=r['id'],side=r['row']['side_to_move'],target=r['target'],
            progress=r['features']['progress'],weight=s['weight']) for r,s in zip(
                [x for x in prep['records']['train'] if x['use_outcome_loss']],train)])
    write_report(output/'plan.json',plan)
    with MARKER.open('x') as f:json.dump(dict(output=str(output.relative_to(ROOT)),plan_sha256=digest(output/'plan.json'),max_updates=20),f)
    required=dict(prep['required_sha256']);paths=[PREP/'report.json',PREP/'saved-label-audit.json',PREP/'checkpoint-00.json',
        Path(__file__),ROOT/'test/learning/outcome/test_stage_weighted_pilot.py',output/'plan.json',MARKER]
    paths += [ROOT/'tools/learning/outcome/outcome_pilot.py',ROOT/'tools/learning/outcome/expanded_outcome_pilot.py',
        ROOT/'tools/learning/outcome/stage_weighted_objective.py',ROOT/'test/learning/outcome/test_stage_weighted_objective.py',
        COMPARISON/'report.json',COMPARISON/'audit.json']
    extras={str(p.relative_to(ROOT)):digest(p) for p in paths};create_backup(extras,output/'backup');verify_backup(output/'backup/manifest.json',extras);required.update(extras)
    binding=dict(plan_sha256=digest(output/'plan.json'),required_sha256=required)
    report=dict(plan=plan,binding=binding,updates=0,trajectory=[],saved=[],selected_update=20,errors=[],closed=False,
        deployed=False,searches=0,qsearch_calls=0,backup_sha256=digest(output/'backup/manifest.json'))
    state=u.initial(keys)
    def save():
        avg=u.average(state);cp=output/f'checkpoint-{state["updates"]:02d}.json';write_report(cp,u.checkpoint(state,binding))
        if u.restore(json.loads(cp.read_bytes()),binding)!=state:raise ValueError('Checkpoint mismatch')
        result=evaluate(prep,avg,output/f'average-{state["updates"]:02d}.txt')
        if state['updates']==0 and any(x['change'] for rows in result['observations'].values() for x in rows):raise ValueError('Zero baseline mismatch')
        result.update(weighted_train_smooth_loss=objective(train,avg)[0],update=state['updates'],max_abs_average=max(abs(x) for x in avg.values()),max_abs_current=max(abs(x) for x in state['delta'].values()),
            current_cap_hits=sum(abs(x)>=.01-1e-12 for x in state['delta'].values()),
            checkpoint_sha256=digest(cp),sidecar_sha256=digest(output/f'average-{state["updates"]:02d}.txt'))
        report['saved'].append(result);write_report(output/'report.json',report)
    try:
        save()
        while state['updates']<20:
            loss,g=objective(train,state['delta'],1e-6);state=u.step(state,g)
            report['updates']=state['updates'];report['trajectory'].append(dict(update=state['updates'],loss=loss,gradient=g,state=state))
            if state['updates'] in (5,10,20):save()
        load();verify_backup(output/'backup/manifest.json',extras)
        for n,s in required.items():
            if digest(ROOT/n)!=s:raise ValueError('Protected input changed')
        report['closed']=True
    except Exception as e:report['errors'].append(str(e));report['closed']=True;raise
    finally:write_report(output/'report.json',report)
    print(json.dumps(dict(updates=20,summary=report['saved'][-1]['summary']),indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();run(a.output)
