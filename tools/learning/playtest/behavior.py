"""Fixed validation-root behavior comparison; search scores are not strength results."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from tools.learning.data.prepare_learning_data import ROOT, Probe, digest
from tools.learning.data.refresh_teachers import RecordedEngine
from tools.learning.hybrid.data import load_dataset, load_teachers, output_path, checked, write_json
from tools.learning.hybrid.runner import cohort, exclusive, seal, unseal

SOURCE = ROOT/'results/learning-pilot/2026-10-15-hybrid-v1'
OUTPUT = ROOT/'results/learning-pilot/2026-10-16-hybrid-behavior-v1'
SETTINGS = dict(depth=15, timeout=30, multipv=1, threads=1, hash_mb=64,
                shin_yonenaga_gyoku=True, own_book=False, ponder=False,
                fresh_engine_per_position=True, max_searches=48)


def select(rows):
    selected = []
    for side in ('black', 'white'):
        for target in (0, 1):
            group = [r for r in rows if r['side']==side and r['target']==target]
            group.sort(key=lambda r: (hashlib.sha256(('hybrid-behavior-v1:'+r['id']).encode()).hexdigest(), r['id']))
            if len(group)<6: raise ValueError('Need six roots per side/outcome stratum')
            selected.extend({k:r[k] for k in ('id','split','side','target','run','game','moves_before','sfen','huffman_hex')} for r in group[:6])
    if len({r['id'] for r in selected})!=24: raise ValueError('Duplicate roots')
    return selected


def dependencies():
    names = ['tools/learning/playtest/__init__.py','tools/learning/playtest/behavior.py',
             'tools/learning/data/refresh_teachers.py','tools/learning/data/prepare_learning_data.py',
             'tools/learning/tempo/prepare_tempo_search.py','tools/analysis/analyze_positions.py',
             'tools/learning/hybrid/data.py','tools/learning/hybrid/runner.py',
             'tools/learning/core/king_safety_updater.py','tools/learning/tempo/run_tempo_search.py']
    return {n:digest(ROOT/n) for n in names}


def inputs(source):
    plan,dataset = load_dataset(source)
    teachers = load_teachers(source,plan,dataset['rows'])
    parts,_,_ = cohort(dataset,teachers)
    report = unseal(source/'search/report.json')
    checkpoint = unseal(source/'search/checkpoint.json')
    audit = unseal(source/'search/export-audit.json')
    if (not report['eligible_for_search'] or not checkpoint['stopped']
            or report['checkpoint_sha256']!=digest(source/'search/checkpoint.json')
            or report['binding']!=checkpoint['binding']
            or report['binding']['plan_sha256']!=digest(source/'plan.json')
            or report['binding']['teachers_sha256']!=digest(source/'teachers.json')
            or report['binding']['arm']!='search'
            or report['evaluation']['sidecar_sha256']!=digest(source/'search/delta.txt')
            or audit['schema']!='rakuyou-hybrid-export-v1' or audit['arm']!='search'
            or audit['arm_report_sha256']!=digest(source/'search/report.json')
            or audit['params_sha256']!=digest(source/'search/runtime/bin/params.bin')
            or audit['zero_export_sha256']!=digest(source/'runtime/bin/params.bin')
            or audit['static_checks']!=len(dataset['rows']) or audit['searches']!=0 or audit['deployed']):
        raise ValueError('Search export/report/checkpoint binding differs')
    runtime = {str(source/n):sha for n,sha in plan['runtime_sha256'].items()}
    candidate = source/'search/runtime'
    actual = {str(p.relative_to(candidate)):digest(p) for p in candidate.rglob('*') if p.is_file()}
    if actual!=audit['runtime_sha256']: raise ValueError('Export runtime map differs')
    expected = {str(Path(n).relative_to('runtime')):sha for n,sha in plan['runtime_sha256'].items()}
    for name,sha in expected.items():
        if name!='bin/params.bin' and actual.get(name)!=sha: raise ValueError('Candidate runtime differs')
    runtime.update({str(candidate/n):sha for n,sha in actual.items()})
    for n,sha in runtime.items(): checked(n,sha)
    names = ('plan.json','teachers.json','dataset.json','search/report.json','search/checkpoint.json','search/delta.txt','search/export-audit.json')
    bindings = {str(source/n):digest(source/n) for n in names}
    probe = plan['probes']['replay']
    bindings[str(ROOT/probe['path'])] = probe['sha256']
    return select(parts['validation']),bindings,runtime,str(ROOT/probe['path'])


def prepare(source=SOURCE, output=OUTPUT):
    source=Path(source).resolve(); output=output_path(output)
    if output==source or output.is_relative_to(source): raise ValueError('Output must be outside source experiment')
    roots,bindings,runtime,probe = inputs(source)
    plan=dict(schema='rakuyou-hybrid-behavior-v1', source=str(source), settings=SETTINGS,
              roots=roots, inputs_sha256=bindings, runtime_sha256=runtime,
              code_sha256=dependencies(), probe=probe,
              engines=dict(baseline=str(source/'runtime/bin/release'), candidate=str(source/'search/runtime/bin/release')),
              limitation='Previously exposed validation roots; cp differences are not strength gains')
    output.mkdir(parents=True,exist_ok=False)
    seal(output/'plan.json',plan)
    return plan


def load(output):
    output=output_path(output); plan=unseal(output/'plan.json')
    if plan['schema']!='rakuyou-hybrid-behavior-v1' or plan['settings']!=SETTINGS: raise ValueError('Unexpected behavior settings')
    if dependencies()!=plan['code_sha256']: raise ValueError('Behavior dependencies changed')
    for group in ('inputs_sha256','runtime_sha256'):
        for name,sha in plan[group].items(): checked(name,sha)
    roots,bindings,runtime,probe=inputs(Path(plan['source']))
    if roots!=plan['roots'] or bindings!=plan['inputs_sha256'] or runtime!=plan['runtime_sha256'] or probe!=plan['probe']:
        raise ValueError('Frozen source bindings differ')
    expected=dict(baseline=str(Path(plan['source'])/'runtime/bin/release'),candidate=str(Path(plan['source'])/'search/runtime/bin/release'))
    if plan['engines']!=expected: raise ValueError('Engine path binding differs')
    return plan


def diagnose(result,row,probe):
    root=probe.replay(row['moves_before'])
    if not root.get('ok'): raise ValueError('Illegal root history')
    last=root['positions'][-1]
    if last['sfen']!=row['sfen'] or last['huffman_hex']!=row['huffman_hex']: raise ValueError('Root identity differs')
    flags=['repetition'] if any(p['occurrences']>1 for p in root['positions']) else []
    if result['stopped_early']: raise ValueError('Stopped/incomplete search')
    if result['bestmove'] in ('resign','win'):
        return dict(kind='special_terminal', flags=flags+['special_terminal'], cp=None)
    candidates=result['candidates']
    if len(candidates)!=1: raise ValueError('Missing single-PV analysis')
    c=candidates[0]
    if not c['pv'] or c['pv'][0]!=result['bestmove']: raise ValueError('Bestmove/PV mismatch')
    replay=probe.replay(row['moves_before']+c['pv'])
    if not replay.get('ok'): raise ValueError('Illegal PV')
    if c['score_type']=='mate':
        if not str(c['score']).lstrip('+-').isdigit() or int(c['score'])==0: raise ValueError('Malformed mate score')
        flags.append('mate')
        if c['depth']<15: flags.append('mate_early_depth')
    elif c['depth']!=15: raise ValueError('Incomplete depth15 search')
    if any(t in c['raw'].split() for t in ('lowerbound','upperbound')): flags.append('bounded')
    if any(p['occurrences']>1 for p in replay['positions']) and 'repetition' not in flags: flags.append('repetition')
    cp=int(c['score']) if c['score_type']=='cp' else None
    if cp is not None and abs(cp)>=31000: flags.append('known_win')
    if c['score_type'] not in ('cp','mate'): raise ValueError('Unknown score type')
    return dict(kind='diagnostic' if flags else 'regular', flags=flags, cp=cp)


def paths(output,row,variant):
    stem=hashlib.sha256(row['id'].encode()).hexdigest()+'-'+variant
    return output/'searches'/(stem+'.json')


def saved(output,plan):
    records={}; binding=digest(output/'plan.json')
    for row in plan['roots']:
        for variant in ('baseline','candidate'):
            path=paths(output,row,variant); marker=path.with_suffix('.attempt.json')
            if not path.exists():
                if marker.exists(): raise ValueError('Interrupted attempt blocks retry: '+row['id'])
                continue
            if not marker.exists() or json.loads(marker.read_text())!=dict(id=row['id'],variant=variant,plan_sha256=binding): raise ValueError('Attempt binding differs')
            record=unseal(path)
            if record['id']!=row['id'] or record['variant']!=variant or record['plan_sha256']!=binding: raise ValueError('Search binding differs')
            if record.get('status') not in ('success','failed'): raise ValueError('Unknown saved search status')
            if record['status']=='success' and ('analysis' not in record or 'diagnosis' not in record): raise ValueError('Missing saved successful analysis')
            records[(row['id'],variant)]=record
    return records


def aggregate(output,plan,records):
    pairs=[]; counts=Counter(); changed=valid=0
    strata={f'{side}_{target}':dict(valid_regular_pairs=0,changed_bestmoves=0) for side in ('black','white') for target in (0,1)}
    for row in plan['roots']:
        pair=dict(root=row,results={v:records[(row['id'],v)] for v in ('baseline','candidate') if (row['id'],v) in records})
        for r in pair['results'].values():
            counts[r['status']]+=1
            counts.update(r.get('diagnosis',{}).get('flags',[]))
            if 'failure' in r and 'Incomplete' in r['failure']['message']: counts['incomplete']+=1
        results=list(pair['results'].values())
        if len(results)==2 and all(r['status']=='success' and r['diagnosis']['kind']=='regular' for r in results):
            a,b=(pair['results'][v] for v in ('baseline','candidate'))
            pair['bestmove_changed']=a['analysis']['bestmove']!=b['analysis']['bestmove']
            pair['cp_difference']=b['diagnosis']['cp']-a['diagnosis']['cp']
            valid+=1; changed+=pair['bestmove_changed']
            stratum=strata[f"{row['side']}_{int(row['target'])}"]
            stratum['valid_regular_pairs']+=1; stratum['changed_bestmoves']+=pair['bestmove_changed']
        pairs.append(pair)
    report=dict(schema='rakuyou-hybrid-behavior-report-v1',plan_sha256=digest(output/'plan.json'),settings=plan['settings'],
                attempted_searches=len(records),completed_searches=counts['success'],completed=len(records)==48 and counts['success']==48,requested_searches=48,counts=dict(counts),strata=strata,valid_regular_pairs=valid,
                changed_bestmoves=changed,pairs=pairs,limitation='Previously exposed validation roots; cp differences are not strength gains. No games played.')
    seal(output/'report.json',report)
    text=f"Attempted {len(records)}/48; successful {counts['success']}/48; valid regular pairs {valid}; changed bestmoves {changed}.\nDiagnostics/errors: {dict(counts)}\n"+report['limitation']+'\n'
    temporary=output/'summary.txt.tmp'; temporary.write_text(text); temporary.replace(output/'summary.txt')
    return report


def run(output=OUTPUT):
    output=output_path(output); load(output)
    with exclusive(output/'run.lock'):
        plan=load(output); records=saved(output,plan)
        report=aggregate(output,plan,records)
        if any(r['status']=='failed' for r in records.values()): raise ValueError('Failed attempt blocks automatic continuation/retry')
        if len(records)==48: return report
        (output/'searches').mkdir(exist_ok=True)
        probe=Probe(plan['probe'])
        try:
            for row in plan['roots']:
                for variant in ('baseline','candidate'):
                    if (row['id'],variant) in records: continue
                    path=paths(output,row,variant)
                    print(f"Search {len(records)+1}/48: {variant} {row['id']}",flush=True)
                    record=dict(id=row['id'],variant=variant,plan_sha256=digest(output/'plan.json'),status='failed',commands=[],transcript=[])
                    write_json(path.with_suffix('.attempt.json'),{k:record[k] for k in ('id','variant','plan_sha256')},exclusive=True)
                    engine=None; failure=None
                    try:
                        engine=RecordedEngine.__new__(RecordedEngine); engine.__init__(Path(plan['engines'][variant]))
                        if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript): raise ValueError('Engine loading error')
                        record['analysis']=engine.analyze(row['moves_before'],15,30,multipv=1)
                        if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript): raise ValueError('Engine search error')
                        record['diagnosis']=diagnose(record['analysis'],row,probe); record['status']='success'
                    except BaseException as error:
                        failure=error; record['failure']=dict(type=type(error).__name__,message=str(error))
                    finally:
                        if engine is not None:
                            try: engine.close()
                            except Exception as error:
                                record['status']='failed'; record['failure']=dict(type=type(error).__name__,message=str(error)); failure=error
                            record['commands']=getattr(engine,'commands',[]); record['transcript']=getattr(engine,'transcript',[])
                        seal(path,record); records[(row['id'],variant)]=record
                        report=aggregate(output,plan,records)
                    if failure is not None: raise failure
        finally:
            probe.close(); load(output)
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'))
    parser.add_argument('--source',type=Path,default=None,help='Source experiment for prepare only')
    parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args()
    try:
        if args.command=='prepare':
            prepare(args.source or SOURCE,args.output)
            print(f'Prepared 24 roots / 48 searches: {args.output}',flush=True)
        else:
            if args.source is not None: raise ValueError('--source is prepare-only; run uses the sealed plan')
            run(args.output)
            print((args.output/'summary.txt').read_text(),end='',flush=True)
    except (ValueError,OSError) as error: raise SystemExit(str(error)) from None


if __name__=='__main__': main()
