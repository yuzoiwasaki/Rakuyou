#!/usr/bin/env python3
"""Read-only audit of saved gold-advance teachers/leaves and update-zero state."""
import sys
from pathlib import Path
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import argparse
import json
from collections import Counter
from tools.learning.gold_silver import gold_advance_preparation as p
from tools.learning.checks.check_tempo_rounding import score_from_parts
from tools.learning.data.prepare_gold_supplement import position_key

REPORT_SHA='99c40167875f063baaea07052c5a6c161f5a272edd8f1910498b6aa9852002fc'


def audit(report_path,output):
    report_path=Path(report_path).resolve();output=Path(output).resolve()
    if not output.is_relative_to((p.ROOT/'results').resolve()) or output.exists():
        raise ValueError('New ignored audit output required')
    if p.digest(report_path)!=REPORT_SHA:raise ValueError('Prepared report changed')
    r=json.loads(report_path.read_bytes());base=report_path.parent
    gen,old,new,required=p.verify_inputs()
    for name,sha in r['binding']['required_sha256'].items():
        if p.digest(p.safe_path(p.ROOT,name))!=sha:raise ValueError('Protected input changed: '+name)
    covered={}
    for path in p.BACKUPS+[base/'backup/manifest.json']:covered.update(p.verify_backup(path))
    if p.digest(base/'backup/manifest.json')!=r['backup_sha256']:raise ValueError('Backup manifest changed')
    if any(covered.get(name)!=sha for name,sha in r['binding']['required_sha256'].items()):
        raise ValueError('Backup coverage mismatch')
    if (r['updates'] or r['deployed'] or r['test_roots'] or r['teacher_searches']
        or r['qsearch_calls']!=24 or r['errors'] or r['validation_quality_measured']
        or r['plan']['training_enabled'] or r['plan']['deployment_enabled']):
        raise ValueError('Expected untrained, undeployed24-leaf preparation')
    expected={};summary={}
    for split in ('train','validation'):
        cache=json.loads((base/f'{split}.supplement-leaves.json').read_bytes())
        if cache['frames']!=r['supplement_frames'][split]:raise ValueError('Leaf cache/report mismatch')
        extra=[]
        if [x['id'] for x in cache['frames']]!=[x['id'] for x in new[split]]:
            raise ValueError('Fresh leaf membership changed')
        for row,item in zip(new[split],cache['frames']):
            record,reason=p.frozen_record(row,item['qsearch'])
            if item['excluded'] is None:
                if reason is not None:raise ValueError('Accepted leaf fails eligibility')
                extra.append(dict(row=row,frame=item['qsearch']))
        expected[split]=old[split]+extra
        saved=r['records'][split]
        if [(x['row'],x['frame']) for x in saved]!=[(x['row'],x['frame']) for x in expected[split]]:
            raise ValueError('Existing178 or supplement rows/leaves changed')
        for x in saved:
            f=x['frame'];root=x['root'];leaf=x['leaf']
            if root['sfen']!=f['root_sfen'] or leaf['sfen']!=f['leaf_sfen']:
                raise ValueError('Saved position identity mismatch')
            for location in (root,leaf):
                if (location['gold_advance_scores']!=p.independent_counts(location['sfen'])
                    or location['on_parts']!=location['base_on_parts']
                    or location['eval_on']!=location['base_eval_on']
                    or score_from_parts(location['on_parts'],location['sfen'].split()[1]=='b' and 'black' or 'white',location['progress'])!=location['eval_on']):
                    raise ValueError('Independent counts or packed zero baseline mismatch')
            if leaf['on_parts']!=f['leaf_parts'] or leaf['eval_on']!=f['leaf_eval_full']:
                raise ValueError('Frozen leaf baseline mismatch')
        summary[split]=dict(effective=len(saved),strata=dict(Counter(x['row']['stratum'] for x in saved)))
    p.disjoint(expected)
    train_positions={position_key(x['frame'][k]) for x in expected['train'] for k in ('root_sfen','leaf_sfen')}
    validation_positions={position_key(x['frame'][k]) for x in expected['validation'] for k in ('root_sfen','leaf_sfen')}
    if train_positions&validation_positions:raise ValueError('Normalized cross-split position overlap')
    test_path=p.ROOT/'results/learning-pilot/2026-10-11-preparation-v2/test.provisional.jsonl'
    # Test metadata supplies separation keys only; no test quality/features.
    pool=json.loads((test_path.parent/'manifest.json').read_bytes())
    e=pool['files']['test'] if 'files' in pool else pool['outputs']['test']
    test_path=p.safe_path(test_path.parent,e['path'])
    if p.digest(test_path)!=e['sha256']:raise ValueError('Test isolation metadata changed')
    test_positions={position_key(json.loads(line)['sfen']) for line in test_path.read_text().splitlines()}
    test_overlap=len((train_positions|validation_positions)&test_positions)
    if test_overlap:raise ValueError('Test separation key overlap; report without refill')
    state=p.restore(json.loads((base/'checkpoint-00.json').read_bytes()),p.CONFIG,r['binding'])
    if state!=p.initial(p.CONFIG) or p.digest(base/'checkpoint-00.json')!=r['checkpoint_sha256']:
        raise ValueError('Update-zero checkpoint mismatch')
    sidecar=json.loads((base/'gold-average-00.json').read_bytes())
    if p.digest(base/'gold-average-00.json')!=r['sidecar_sha256'] or sidecar['delta_cp']!=[0,0] or sidecar['raw']!=[0,0] or sidecar['operational_loadable']:
        raise ValueError('Zero sidecar mismatch')
    if any(x['cp_change'] or x['root_cp_change'] for rows in r['zero_observations'].values() for x in rows):
        raise ValueError('Zero observations changed')
    for entry in r['numerical_perturbations'].values():
        if len(entry['observations'])!=sum(len(x) for x in expected.values()):raise ValueError('Perturbation scope changed')
        for x in entry['observations']:
            if max(abs(x['cp_change']),abs(x['root_cp_change']))>3 or abs(x['cp_change']-x['smooth_cp_change'])>2.000001:
                raise ValueError('Perturbation whole-position or rounding bound exceeded')
    result=dict(accepted=True,report_sha256=REPORT_SHA,summary=summary,independent_root_leaf_count_checks=2*sum(len(x) for x in expected.values()),
        normalized_cross_split_overlap=0,test_separation_key_overlap=test_overlap,
        reused_teachers_and_leaves=178,new_qsearch_calls=24,updates=0,deployed=False,
        validation_quality_measured=False,backups_verified=True,checkpoint_zero_verified=True,
        runtime_and_prior_candidates_unchanged=True,auditor_sha256=p.digest(Path(__file__)))
    p.write_report(output,result);print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();audit(args.report,args.output)
