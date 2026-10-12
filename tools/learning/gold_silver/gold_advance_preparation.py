#!/usr/bin/env python3
"""Prepare and audit one central gold-advance feature; no training/search entry."""
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[3]))

import argparse
import json
import math
import selectors
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.core.king_safety_objective import FrozenLeaf, objective, check_gradient, sigmoid, GAIN
from tools.learning.core.king_safety_updater import Config, initial, checkpoint, restore
from tools.learning.core.learning_backup import create_backup, verify_backup, safe_path
from tools.learning.king_safety.king_safety_pilot import independent_columns
from tools.learning.tempo.run_tempo_search import write_report

from collections import Counter
from tools.learning.gold_silver.gold_advance_features import FEATURE, gold_advance_details, scores
from tools.learning.data.gold_teacher_generation import load_binding, PREP, DEFAULT_PLAN
from tools.learning.data.prepare_refreshed_pilot import frozen_record, validate_teacher

CONFIG = Config(l2=1e-6)
PROBE = ROOT/'results/gold-advance-tools/gold-advance-probe'
PROBE_SHA = '7735d0cbf2bccdfefb9474643e413c5b3913a40da0824947562cf8b7ba1074f0'
GEN = ROOT/'results/learning-pilot/2026-10-12-gold-teacher-run-v1'
PARENT = ROOT/'results/learning-pilot/2026-10-12-supported-pawn-preparation-v1'
ARTIFACTS = {
    GEN/'report.json':'7688a8e3df760a389f327a55a67632798ad6f41c510b48f53807b37622896951',
    GEN/'audit-v1.json':'b6a8c5d0fda8f582ee8a95c49f1ab524ddf5a0a7e5592b1821d7f2c1e9444a22',
    PARENT/'report.json':'060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4',
    PARENT/'audit-v1.json':'1738668b3580e41db2436736667ab158c661d9301fb418983c6d71da2b92b0ed',
    PROBE:PROBE_SHA,
}
BACKUPS = [PARENT/'backup/manifest.json',PREP.parent/'additional-backup/manifest.json']


def details(sfen):
    pieces={}
    ranks=sfen.split()[0].split('/')
    if len(ranks)!=9:raise ValueError('Nine ranks required')
    for rank,row in zip('abcdefghi',ranks):
        file=9;promoted=False
        for char in row:
            if char.isdigit():file-=int(char);continue
            if char=='+':promoted=True;continue
            pieces[str(file)+rank]=('+' if promoted else '')+char
            file-=1;promoted=False
        if file!=0 or promoted:raise ValueError('Invalid SFEN rank')
    return gold_advance_details(pieces)


def independent_counts(sfen):return scores(details(sfen))


class GoldAdvanceProbe(Probe):
    def __init__(self,raw=(0,0)):
        if len(raw)!=2 or any(type(x) is not int or abs(x)>32768 for x in raw):
            raise ValueError('Two signed bounded raw coefficients required')
        self.errors=tempfile.TemporaryFile(mode='w+t');self.qsearch=False
        self.process=subprocess.Popen([str(PROBE),'--gold-perturb',str(ROOT/'bin/params.bin'),
            *[str(x) for x in raw]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=self.errors,text=True,bufsize=1)
        self.selector=selectors.DefaultSelector()
        self.selector.register(self.process.stdout,selectors.EVENT_READ)


def verify_inputs():
    required={}
    for path,sha in ARTIFACTS.items():
        if digest(path)!=sha:raise ValueError('Bound artifact changed: '+str(path.relative_to(ROOT)))
        required[path.relative_to(ROOT).as_posix()]=sha
    parent=json.loads((PARENT/'report.json').read_bytes())
    pa=json.loads((PARENT/'audit-v1.json').read_bytes())
    gen=json.loads((GEN/'report.json').read_bytes());audit=json.loads((GEN/'audit-v1.json').read_bytes())
    if (not parent['closed'] or parent['updates'] or parent['errors'] or not pa['accepted']
        or pa['report_sha256']!=ARTIFACTS[PARENT/'report.json']
        or not gen['teacher_generation_complete'] or gen['errors'] or gen['real_data_updates']
        or gen['deployed'] or audit['accepted']!=24 or not audit['teacher_provenance_verified']
        or audit['generation_report_sha256']!=ARTIFACTS[GEN/'report.json']):
        raise ValueError('Expected audited zero-update baseline data')
    if digest(BACKUPS[0])!=parent['backup_sha256']:raise ValueError('Parent backup manifest changed')
    for path in BACKUPS:required.update(verify_backup(path))
    plan=next(ROOT/e['source'] for e in gen['input_copies'] if e['sha256']==gen['plan_sha256'])
    load_binding(PREP,plan,True)
    for e in gen['input_copies']:
        for path in (ROOT/e['source'],GEN/e['copy']):
            if digest(path)!=e['sha256']:raise ValueError('Generation input changed')
            required[path.relative_to(ROOT).as_posix()]=e['sha256']
    for name,sha in gen['tool_sha256'].items():
        path=ROOT/'tools'/name
        if digest(path)!=sha:raise ValueError('Teacher tool changed')
        required[path.relative_to(ROOT).as_posix()]=sha
    old={};new={}
    for split,size,extra in (('train',143,16),('validation',35,8)):
        old[split]=[dict(row=r['row'],frame=r['frame']) for r in parent['records'][split]]
        if len(old[split])!=size:raise ValueError('Existing178 membership changed')
        e=gen['files'][split];path=safe_path(GEN,e['path'])
        if digest(path)!=e['sha256']:raise ValueError('Teacher JSONL changed')
        required[path.relative_to(ROOT).as_posix()]=e['sha256']
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        if rows!=[r for r in gen['records'] if r['split']==split] or len(rows)!=extra:
            raise ValueError('Supplement membership changed')
        new[split]=[validate_teacher(row,split) for row in rows if row['teacher_status']=='accepted']
    return gen,old,new,required


def prepare_new_leaves(new,output):
    # One attempt; exclusions remain exclusions, no replacement or retry.
    with (GEN/'frozen-leaf-preparation-attempt-v1.json').open('x') as stream:
        json.dump(dict(output=str(output.relative_to(ROOT)),generation_sha256=ARTIFACTS[GEN/'report.json']),stream)
    q=Probe(ROOT/'results/learning-tools/learning-data-probe',ROOT/'bin/params.bin',
        qsearch_progress=ROOT/'bin/progress.bin')
    static=GoldAdvanceProbe();parts={};frames={};calls=0
    try:
        for split,rows in new.items():
            parts[split]=[];frames[split]=[]
            for row in rows:
                print(f"qsearch {calls+1}/24 {split} {row['id']}",flush=True)
                frame=q.replay(row['moves_before']);calls+=1
                record,reason=frozen_record(row,frame)
                if record is not None:
                    replay=static.replay(row['moves_before']+frame['pv'])
                    if not replay.get('ok'):raise ValueError('Frozen PV illegal')
                    leaf=replay['positions'][-1]
                    if any(p['occurrences']>1 for p in replay['positions']):reason='repeated_game_history'
                    elif (leaf['sfen']!=frame['leaf_sfen'] or leaf['eval_on']!=frame['leaf_eval_full']
                        or leaf['progress']!=frame['leaf_progress'] or leaf['on_parts']!=frame['leaf_parts']):
                        raise ValueError('New native leaf mismatch')
                    if reason is None:parts[split].append(dict(row=row,frame=frame))
                frames[split].append(dict(id=row['id'],qsearch=frame,excluded=reason))
            write_report(output/f'{split}.supplement-leaves.json',dict(frames=frames[split],updates=0,
                generation_sha256=ARTIFACTS[GEN/'report.json'],quality_measured=False))
    finally:q.close();static.close()
    return parts,frames,calls


def disjoint(parts):
    for key in ('root_sfen','leaf_sfen'):
        if {r['frame'][key] for r in parts['train']}&{r['frame'][key] for r in parts['validation']}:
            raise ValueError('Cross-split position overlap; do not refill')
    for key in ('id',):
        all_rows=[r['row'][key] for rows in parts.values() for r in rows]
        if len(all_rows)!=len(set(all_rows)):raise ValueError('Duplicate root ID')
    for key in ('run',):
        if {r['row']['source'][key] for r in parts['train']}&{r['row']['source'][key] for r in parts['validation']}:
            raise ValueError('Cross-split run overlap')


def load_records(parts):
    records = {split:[] for split in parts}
    probe = GoldAdvanceProbe()
    try:
        for split, rows in parts.items():
            for r in rows:
                row, f = r['row'], r['frame']
                replay = probe.replay(row['moves_before']+f['pv'])
                if not replay.get('ok') or any(x['occurrences']>1 for x in replay['positions']):
                    raise ValueError('Illegal/repeated frozen history; no refill')
                root, leaf = replay['positions'][len(row['moves_before'])], replay['positions'][-1]
                if (root['sfen']!=f['root_sfen'] or leaf['sfen']!=f['leaf_sfen']
                        or leaf['eval_on']!=f['leaf_eval_full'] or leaf['on_parts']!=f['leaf_parts']
                        or leaf['progress']!=f['leaf_progress']):
                    raise ValueError('Native baseline/cache mismatch')
                for p in (root,leaf):
                    if (p['gold_advance_scores']!=independent_counts(p['sfen'])
                            or p['on_parts']!=p['base_on_parts'] or p['eval_on']!=p['base_eval_on']):
                        raise ValueError('Native/independent counts or zero residual mismatch')
                counts = leaf['gold_advance_scores']
                sign = 1 if f['root_side']==f['leaf_side'] else -1
                sample = FrozenLeaf(sign*leaf['eval_on'],row['teacher_cp'],leaf['progress'],row['side_to_move'],
                                    (counts['black']-counts['white'],0,0,0))
                records[split].append(dict(row=row,frame=f,root=root,leaf=leaf,sample=sample))
    finally:
        probe.close()
    return records


def coverage(records):
    groups = defaultdict(list)
    for r in records:
        groups['all'].append(r)
        groups[r['row']['stratum']].append(r)
    def stats(rows, location):
        values = [r[location]['gold_advance_scores'] for r in rows]
        return dict(positions=len(rows),presence=sum(any(c.values()) for c in values),
                    black_presence=sum(c['black']>0 for c in values),
                    white_presence=sum(c['white']>0 for c in values),
                    net_nonzero=sum(c['black']!=c['white'] for c in values),
                    max_count=max(max(c.values()) for c in values),
                    levels=dict(Counter(str(g['score']) for r in rows for g in details(r[location]['sfen']) if g['score']>0)))
    return {key:{loc:stats(rows,loc) for loc in ('root','leaf')} for key,rows in groups.items()}


def native_scores(records,raw,quality=False):
    probe=GoldAdvanceProbe(raw);out=[]
    try:
        for r in records:
            row,f=r['row'],r['frame'];replay=probe.replay(row['moves_before']+f['pv'])
            if not replay.get('ok'):raise ValueError('Candidate replay failed')
            leaf=replay['positions'][-1];root=replay['positions'][len(row['moves_before'])]
            for before,after in ((r['leaf'],leaf),(r['root'],root)):
                for key in ('sfen','progress','gold_advance_scores','base_on_parts','base_eval_on'):
                    if after[key]!=before[key]:raise ValueError('Baseline/position changed')
                for mode in ('on_parts','off_parts'):
                    for key in ('kp','tempo'):
                        if before[mode][key]!=after[mode][key]:raise ValueError('Protected component changed')
                    net=before['gold_advance_scores']['black']-before['gold_advance_scores']['white']
                    for lane in range(4):
                        expected=net*raw[lane//2] if lane in (0,2) else 0
                        if after[mode]['others'][lane]-before[mode]['others'][lane]!=expected:raise ValueError('Packed gold-advance residual mismatch')
            sign=1 if f['root_side']==f['leaf_side'] else -1
            score=sign*leaf['eval_on'];base=r['sample'].base_root_cp
            smooth=r['sample'].predict(tuple(x/65536 for x in raw)+(0.0,)*6)
            if abs(score-smooth)>2.000001:raise ValueError('Smooth/native mismatch')
            observation=dict(id=row['id'],side=row['side_to_move'],stratum=row['stratum'],base_cp=base,candidate_cp=score,
                cp_change=score-base,smooth_cp_change=smooth-base,root_base_cp=r['root']['eval_on'],root_candidate_cp=root['eval_on'],
                root_cp_change=root['eval_on']-r['root']['eval_on'])
            if quality:observation.update(loss_base=(sigmoid(GAIN*base)-sigmoid(GAIN*row['teacher_cp']))**2,
                loss_candidate=(sigmoid(GAIN*score)-sigmoid(GAIN*row['teacher_cp']))**2)
            out.append(observation)
    finally:probe.close()
    return out



def run(output):
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT/'results').resolve()) or output.exists():
        raise ValueError('A new results directory is required')
    gen, old, new, required = verify_inputs()
    output.mkdir(parents=True,exist_ok=False)
    extra, frames, qsearch_calls = prepare_new_leaves(new,output)
    parts={split:old[split]+extra[split] for split in old}
    disjoint(parts)
    records = load_records(parts)
    samples = [r['sample'] for r in records['train']]
    active = independent_columns(samples)
    if active != [0,1]:
        raise ValueError('Both stage coefficients must be identifiable')
    train_loss, gradient = objective(samples,(0.0,)*8,0)
    regularization = CONFIG.l2*CONFIG.delta_limit_cp
    ratios = [regularization/abs(g) if g else float('inf') for g in gradient[:2]]
    l2_needs_review=any(x>.25 for x in ratios)
    plan = dict(schema='rakuyou-gold-advance-plan-v1',feature=FEATURE,
                purpose='usefulness via current-base search teachers; no positive-sign constraint',
                unit='cp per supported-gold advancement level; each gold once, levels0/1/2/3',
                interpolation='(1-progress)*opening + progress*end; black-minus-white count',
                active_slots=[0,1],unused_slots=[2,3,4,5,6,7],initial_delta=[0,0],sign_constraints=None,
                config=asdict(CONFIG),training_enabled=False,deployment_enabled=False,
                outcome_loss_enabled=False,max_position_cp_change=10,save_updates=[0,5,10,20],
                l2_rationale=dict(train_only_initial_gradient=list(gradient[:2]),train_initial_loss=train_loss,
                                  regularization_gradient_at_cap=regularization,
                                  ratio_to_initial_gradient=ratios,needs_review=l2_needs_review,validation_quality_measured=False),
                runtime_sha256=gen['runtime_sha256'],source_artifacts_sha256={str(p.relative_to(ROOT)):s for p,s in ARTIFACTS.items()},
                probe_sha256=digest(PROBE),coverage={s:coverage(rows) for s,rows in records.items()})
    write_report(output/'plan.json',plan)
    source_paths = [Path(__file__),ROOT/'Makefile',PROBE,
                    ROOT/'tools/learning/native/gold_advance_probe.cc',
                    ROOT/'tools/learning/native/learning_data_probe.cc',
                    ROOT/'tools/learning/native/king_safety_features.h',
                    ROOT/'tools/learning/core/king_safety_objective.py',
                    ROOT/'tools/learning/core/king_safety_updater.py',
                    ROOT/'tools/learning/core/learning_backup.py',
                    ROOT/'tools/learning/data/prepare_learning_data.py',
                    ROOT/'tools/learning/king_safety/king_safety_pilot.py',
                    ROOT/'tools/learning/tempo/run_tempo_search.py',output/'plan.json']
    source_paths += [ROOT/'tools/learning/gold_silver/gold_advance_features.py',
                    ROOT/'tools/learning/data/prepare_refreshed_pilot.py',
                    ROOT/'tools/learning/checks/check_qsearch_leaves.py',
                    ROOT/'tools/learning/checks/check_tempo_rounding.py',
                    ROOT/'tools/learning/gold_silver/build_gold_advance_probe.py',
                    ROOT/'results/gold-advance-tools/build-report.json']
    source_paths += list(output.glob('*.supplement-leaves.json'))
    source_paths += list((ROOT/'test/learning/gold_silver').glob('test_gold_advance*.py'))
    # Record previous candidates/probes without rewriting any archived metadata.
    for folder in ('2026-10-12-expanded-pair-run-v1','2026-10-12-gold-silver-pair-run-v1'):
        source_paths += list((ROOT/'results/learning-pilot'/folder).glob('*.json'))
    for path in source_paths:
        required[path.relative_to(ROOT).as_posix()] = digest(path)
    covered={}
    for path in BACKUPS:covered.update(verify_backup(path))
    additional={name:sha for name,sha in required.items() if name not in covered}
    create_backup(additional,output/'backup')
    verify_backup(output/'backup/manifest.json',additional)
    binding = dict(feature=FEATURE,plan_sha256=digest(output/'plan.json'),required_sha256=required)
    checks = [check_gradient(samples,(0.0,)*8,CONFIG.l2),
              check_gradient(samples,(.01,-.01)+(0.0,)*6,CONFIG.l2)]
    observations = {s:native_scores(rows,(0,0)) for s,rows in records.items()}
    if any(x['cp_change'] or x['root_cp_change'] for rows in observations.values() for x in rows):
        raise ValueError('Zero candidate differs from baseline')
    perturbations = {}
    for raw in ((16384,-16384),(-16384,16384),(32768,32768),(-32768,-32768)):
        rows = native_scores(records['train']+records['validation'],raw)
        maximum = max(max(abs(x['cp_change']),abs(x['root_cp_change'])) for x in rows)
        if maximum>plan['max_position_cp_change']:
            raise ValueError('Position-level evaluation limit exceeded')
        perturbations[str(raw)] = dict(raw=list(raw),maximum_cp_change=maximum,observations=rows)
    state = initial(CONFIG)
    payload = checkpoint(state,CONFIG,binding)
    write_report(output/'checkpoint-00.json',payload)
    if restore(json.loads((output/'checkpoint-00.json').read_bytes()),CONFIG,binding)!=state:
        raise ValueError('Zero checkpoint restoration mismatch')
    write_report(output/'gold-average-00.json',dict(schema='rakuyou-gold-advance-sidecar-v1',feature=FEATURE,
                  base_sha256=gen['runtime_sha256']['bin/params.bin'],probe_sha256=digest(PROBE),
                  delta_cp=[0,0],raw=[0,0],scale=65536,update=0,operational_loadable=False))
    report = dict(schema='rakuyou-gold-advance-preparation-v1',binding=binding,plan=plan,
                  records={s:[dict(row=r['row'],frame=r['frame'],root=r['root'],leaf=r['leaf']) for r in rows]
                           for s,rows in records.items()},gradients=checks,zero_observations=observations,
                  numerical_perturbations=perturbations,zero_checkpoint_restored=True,
                  backup_sha256=digest(output/'backup/manifest.json'),
                  checkpoint_sha256=digest(output/'checkpoint-00.json'),
                  sidecar_sha256=digest(output/'gold-average-00.json'),
                  updates=0,searches=qsearch_calls,teacher_searches=0,test_roots=0,deployed=False,
                  qsearch_calls=qsearch_calls,reused_teachers=178,reused_leaves=178,
                  supplement_frames=frames,
                  summary={split:dict(accepted=len(records[split]),supplement_accepted=len(extra[split]),
                      supplement_excluded=dict(Counter(x['excluded'] for x in frames[split] if x['excluded'])),
                      strata=dict(Counter(r['row']['stratum'] for r in records[split]))) for split in records},
                  validation_quality_measured=False,errors=[],closed=True)
    verify_backup(output/'backup/manifest.json',additional)
    for path in BACKUPS:verify_backup(path)
    for name,sha in required.items():
        if digest(ROOT/name)!=sha:
            raise ValueError('Protected input changed: '+name)
    write_report(output/'report.json',report)
    write_report(output/'audit-v1.json',dict(accepted=True,report_sha256=digest(output/'report.json'),
                  native_replays=sum(map(len,records.values())),independent_root_leaf_count_checks=2*sum(map(len,records.values())),
                  updates=0,searches=qsearch_calls,test_roots=0,backup_verified=True,validation_quality_measured=False,
                  zero_checkpoint_restored=True,runtime_and_prior_pair_candidates_unchanged=True))
    print(json.dumps(dict(summary=report['summary'],coverage=plan['coverage'],l2=plan['l2_rationale'],updates=0,
                         perturbation_maxima={k:v['maximum_cp_change'] for k,v in perturbations.items()}),indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    run(args.output)
