#!/usr/bin/env python3
"""Prepare and audit one central supported-pawn feature; no training/search entry."""
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

FEATURE = 'files3to7_rank5_unpromoted_pawn_defended_by_gold_or_unpromoted_silver'
CONFIG = Config(l2=1e-6)
PROBE = ROOT/'results/supported-pawn-tools/supported-pawn-probe'
GEN = ROOT/'results/learning-pilot/2026-10-12-pair-teacher-run-v1'
LEAVES = ROOT/'results/learning-pilot/2026-10-12-pair-leaves-v1'
ARTIFACTS = {
    GEN/'report.json': '01c9a6cdf28e6c5114a0dafae99937ce0ce3dfe06900864faa4683eda403dd4c',
    GEN/'audit-v1.json': '47c044ef535b45b4882107a9e0a68a508942684650232d4851e16c90c71acdc6',
    LEAVES/'report.json': '6e5216775697f1bbeaa6bd5c3e37e105378148f34fb04239aa6e313aa484dfed',
    LEAVES/'audit-v1.json': '747229695ece4961f079dc1bbab30cda86cb52fb6b9ddd5dc4875dc5d7029a73',
    LEAVES/'train.leaves.json': '75ab13da2808161d7ceb81b00dc9360f31c72228c6c4937412db9cfeab814615',
    LEAVES/'validation.leaves.json': '816b7c1d593a14078ae94651f771bef6b3b7fedb25dc32037cba08a0bf475910',
}


def independent_counts(sfen):
    """Short-piece geometry from SFEN, independent of native controls; pins omitted."""
    pieces = {}
    rows = sfen.split()[0].split('/')
    if len(rows) != 9:
        raise ValueError('Nine SFEN rows required')
    for rank, row in zip('abcdefghi', rows):
        file, promoted = 9, False
        for char in row:
            if char.isdigit():
                file -= int(char)
                continue
            if char == '+':
                promoted = True
                continue
            pieces[(file, ord(rank))] = ('+' if promoted else '')+char
            promoted = False
            file -= 1
        if file != 0 or promoted:
            raise ValueError('Invalid SFEN rank')
    counts = {}
    for upper, color in ((True, 'black'), (False, 'white')):
        forward = -1 if upper else 1
        gold, silver, pawn = ('G', 'S', 'P') if upper else ('g', 's', 'p')
        targets = set()
        for (x, y), piece in pieces.items():
            if piece == gold:
                offsets = [(-1,forward),(0,forward),(1,forward),(-1,0),(1,0),(0,-forward)]
            elif piece == silver:
                offsets = [(0,forward),(-1,-1),(1,-1),(-1,1),(1,1)]
            else:
                continue
            targets.update((x+dx,y+dy) for dx,dy in offsets)
        counts[color] = sum(pieces.get((file,ord('e'))) == pawn and (file,ord('e')) in targets
                            for file in range(3,8))
    return counts


class SupportedPawnProbe(Probe):
    def __init__(self, raw=(0,0)):
        if len(raw)!=2 or any(type(x) is not int or abs(x)>32768 for x in raw):
            raise ValueError('Two signed bounded raw coefficients required')
        self.errors = tempfile.TemporaryFile(mode='w+t')
        self.qsearch = False
        self.process = subprocess.Popen([str(PROBE),'--pawn-perturb',str(ROOT/'bin/params.bin'),
                                         *[str(x) for x in raw]], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,stderr=self.errors,text=True,bufsize=1)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout,selectors.EVENT_READ)


def verify_inputs():
    required = {}
    def verify(path, sha):
        if digest(path) != sha:
            raise ValueError('Bound input changed: '+str(path.relative_to(ROOT)))
        required[path.relative_to(ROOT).as_posix()] = sha
    for path, sha in ARTIFACTS.items():
        verify(path, sha)
    gen = json.loads((GEN/'report.json').read_bytes())
    audit = json.loads((GEN/'audit-v1.json').read_bytes())
    prep = json.loads((LEAVES/'report.json').read_bytes())
    leaf_audit = json.loads((LEAVES/'audit-v1.json').read_bytes())
    if (audit['generation_report_sha256'] != ARTIFACTS[GEN/'report.json']
            or not audit['teacher_provenance_verified'] or audit['accepted'] != 178
            or not gen['teacher_generation_complete'] or gen['errors'] or gen['real_data_updates']
            or gen['deployed'] or not prep['closed'] or prep['errors'] or prep['updates']
            or not leaf_audit['accepted'] or leaf_audit['report_sha256'] != ARTIFACTS[LEAVES/'report.json']):
        raise ValueError('Expected audited, untrained143/35 teachers and leaves')
    for name, sha in gen['runtime_sha256'].items():
        verify(safe_path(ROOT,name),sha)
    for entry in gen['input_copies']:
        verify(safe_path(ROOT,entry['source']),entry['sha256'])
        verify(safe_path(GEN,entry['copy']),entry['sha256'])
    parts = {}
    for split, size in (('train',143),('validation',35)):
        file = gen['files'][split]
        path = safe_path(GEN,file['path']);verify(path,file['sha256'])
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if rows != [r for r in gen['records'] if r['split']==split]:
            raise ValueError('Teacher JSONL/report mismatch')
        accepted = [r for r in rows if r['teacher_status']=='accepted']
        cache = json.loads((LEAVES/f'{split}.leaves.json').read_bytes())
        frames = cache['frames']
        if (frames != prep['frames'][split] or cache['generation_sha256'] != ARTIFACTS[GEN/'report.json']
                or len(accepted)!=size or len(frames)!=size
                or len({r['id'] for r in accepted})!=size
                or [r['id'] for r in accepted] != [f['id'] for f in frames]):
            raise ValueError('Teacher/leaf membership changed; no refill')
        parts[split] = []
        for row, frame in zip(accepted,frames):
            verify(safe_path(ROOT,row['source']['path']),row['source']['sha256'])
            f = frame['qsearch']
            if (frame['excluded'] is not None or frame['stratum']!=row['stratum']
                    or row['sfen']!=f['root_sfen'] or row['side_to_move']!=f['root_side']
                    or f['leaf_in_check'] or f['leaf_repetition'] or row['outcome_loss_enabled']):
                raise ValueError('Frozen leaf predicate mismatch')
            parts[split].append(dict(row=row,frame=f))
    for key in ('root_sfen','leaf_sfen'):
        if {r['frame'][key] for r in parts['train']} & {r['frame'][key] for r in parts['validation']}:
            raise ValueError('Cross-split overlap')
    # Archived code paths in old metadata stay historical. Bind current code below;
    # reuse immutable audited data rather than invoking closed, pre-migration runners.
    return gen, parts, required


def load_records(parts):
    records = {split:[] for split in parts}
    probe = SupportedPawnProbe()
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
                    if (p['supported_pawn_counts']!=independent_counts(p['sfen'])
                            or p['on_parts']!=p['base_on_parts'] or p['eval_on']!=p['base_eval_on']):
                        raise ValueError('Native/independent counts or zero residual mismatch')
                counts = leaf['supported_pawn_counts']
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
        values = [r[location]['supported_pawn_counts'] for r in rows]
        return dict(positions=len(rows),presence=sum(any(c.values()) for c in values),
                    black_presence=sum(c['black']>0 for c in values),
                    white_presence=sum(c['white']>0 for c in values),
                    net_nonzero=sum(c['black']!=c['white'] for c in values),
                    max_count=max(max(c.values()) for c in values))
    return {key:{loc:stats(rows,loc) for loc in ('root','leaf')} for key,rows in groups.items()}


def native_scores(records,raw,quality=False):
    probe=SupportedPawnProbe(raw);out=[]
    try:
        for r in records:
            row,f=r['row'],r['frame'];replay=probe.replay(row['moves_before']+f['pv'])
            if not replay.get('ok'):raise ValueError('Candidate replay failed')
            leaf=replay['positions'][-1];root=replay['positions'][len(row['moves_before'])]
            for before,after in ((r['leaf'],leaf),(r['root'],root)):
                for key in ('sfen','progress','supported_pawn_counts','base_on_parts','base_eval_on'):
                    if after[key]!=before[key]:raise ValueError('Baseline/position changed')
                for mode in ('on_parts','off_parts'):
                    for key in ('kp','tempo'):
                        if before[mode][key]!=after[mode][key]:raise ValueError('Protected component changed')
                    net=before['supported_pawn_counts']['black']-before['supported_pawn_counts']['white']
                    for lane in range(4):
                        expected=net*raw[lane//2] if lane in (0,2) else 0
                        if after[mode]['others'][lane]-before[mode]['others'][lane]!=expected:raise ValueError('Packed supported-pawn residual mismatch')
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
    gen, parts, required = verify_inputs()
    records = load_records(parts)
    samples = [r['sample'] for r in records['train']]
    active = independent_columns(samples)
    if active != [0,1]:
        raise ValueError('Both stage coefficients must be identifiable')
    train_loss, gradient = objective(samples,(0.0,)*8,0)
    regularization = CONFIG.l2*CONFIG.delta_limit_cp
    ratios = [regularization/abs(g) if g else float('inf') for g in gradient[:2]]
    if any(x>.25 for x in ratios):
        raise ValueError('L2 overwhelms initial train signal; discuss before changing')
    output.mkdir(parents=True,exist_ok=False)
    plan = dict(schema='rakuyou-supported-pawn-plan-v1',feature=FEATURE,
                purpose='usefulness via current-base search teachers; no positive-sign constraint',
                unit='cp per supported central fifth-rank pawn; once per pawn',
                interpolation='(1-progress)*opening + progress*end; black-minus-white count',
                active_slots=[0,1],unused_slots=[2,3,4,5,6,7],initial_delta=[0,0],sign_constraints=None,
                config=asdict(CONFIG),training_enabled=False,deployment_enabled=False,
                outcome_loss_enabled=False,max_position_cp_change=10,save_updates=[0,5,10,20],
                l2_rationale=dict(train_only_initial_gradient=list(gradient[:2]),train_initial_loss=train_loss,
                                  regularization_gradient_at_cap=regularization,
                                  ratio_to_initial_gradient=ratios,validation_quality_measured=False),
                runtime_sha256=gen['runtime_sha256'],source_artifacts_sha256={str(p.relative_to(ROOT)):s for p,s in ARTIFACTS.items()},
                probe_sha256=digest(PROBE),coverage={s:coverage(rows) for s,rows in records.items()})
    write_report(output/'plan.json',plan)
    source_paths = [Path(__file__),ROOT/'Makefile',PROBE,
                    ROOT/'tools/learning/native/supported_pawn_probe.cc',
                    ROOT/'tools/learning/native/learning_data_probe.cc',
                    ROOT/'tools/learning/native/king_safety_features.h',
                    ROOT/'tools/learning/core/king_safety_objective.py',
                    ROOT/'tools/learning/core/king_safety_updater.py',
                    ROOT/'tools/learning/core/learning_backup.py',
                    ROOT/'tools/learning/data/prepare_learning_data.py',
                    ROOT/'tools/learning/king_safety/king_safety_pilot.py',
                    ROOT/'tools/learning/tempo/run_tempo_search.py',output/'plan.json']
    source_paths += list((ROOT/'src').glob('*.cc'))+list((ROOT/'src').glob('*.h'))
    # Record previous candidates/probes without rewriting any archived metadata.
    for folder in ('2026-10-12-expanded-pair-run-v1','2026-10-12-gold-silver-pair-run-v1'):
        source_paths += list((ROOT/'results/learning-pilot'/folder).glob('*.json'))
    for path in source_paths:
        required[path.relative_to(ROOT).as_posix()] = digest(path)
    create_backup(required,output/'backup')
    verify_backup(output/'backup/manifest.json',required)
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
    write_report(output/'pawn-average-00.json',dict(schema='rakuyou-supported-pawn-sidecar-v1',feature=FEATURE,
                  base_sha256=gen['runtime_sha256']['bin/params.bin'],probe_sha256=digest(PROBE),
                  delta_cp=[0,0],raw=[0,0],scale=65536,update=0,operational_loadable=False))
    report = dict(schema='rakuyou-supported-pawn-preparation-v1',binding=binding,plan=plan,
                  records={s:[dict(row=r['row'],frame=r['frame'],root=r['root'],leaf=r['leaf']) for r in rows]
                           for s,rows in records.items()},gradients=checks,zero_observations=observations,
                  numerical_perturbations=perturbations,zero_checkpoint_restored=True,
                  backup_sha256=digest(output/'backup/manifest.json'),
                  checkpoint_sha256=digest(output/'checkpoint-00.json'),
                  sidecar_sha256=digest(output/'pawn-average-00.json'),
                  updates=0,searches=0,teacher_searches=0,test_roots=0,deployed=False,
                  validation_quality_measured=False,errors=[],closed=True)
    verify_backup(output/'backup/manifest.json',required)
    for name,sha in required.items():
        if digest(ROOT/name)!=sha:
            raise ValueError('Protected input changed: '+name)
    write_report(output/'report.json',report)
    write_report(output/'audit-v1.json',dict(accepted=True,report_sha256=digest(output/'report.json'),
                  native_replays=178,independent_root_leaf_count_checks=356,
                  updates=0,searches=0,test_roots=0,backup_verified=True,validation_quality_measured=False,
                  zero_checkpoint_restored=True,runtime_and_prior_pair_candidates_unchanged=True))
    print(json.dumps(dict(coverage=plan['coverage'],l2=plan['l2_rationale'],updates=0,
                         perturbation_maxima={k:v['maximum_cp_change'] for k,v in perturbations.items()}),indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    run(args.output)
