"""Fixed guarded candidate vs baseline, 24 stratified exposed roots / 48 searches."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from tools.learning.constraints import temporal_guarded as training
from tools.learning.hybrid import export as exporter
from tools.learning.playtest import behavior as previous
from tools.learning.tempo.prepare_tempo_search import copy_verified

base = training.base
common = base.old
ROOT = base.data.ROOT
SOURCE = training.OUTPUT
OUTPUT = ROOT / 'results/learning-pilot/2026-10-20-guarded-behavior-v1'
DIRECTORY = SOURCE / 'guarded-mixed'
SETTINGS = dict(previous.SETTINGS, timeout=120)


def select(rows):
    selected = []
    for cohort in ('original', 'additional'):
        for side in ('black', 'white'):
            for target in (0, 1):
                group = [r for r in rows if r['split']=='validation' and r['cohort']==cohort and r['side']==side and r['target']==target]
                group.sort(key=lambda r: (hashlib.sha256(('guarded-behavior-v1:'+r['id']).encode()).hexdigest(), r['id']))
                games = set()
                chosen = []
                for r in group:
                    game = (r['run'], r['game'])
                    if game in games:
                        continue
                    games.add(game)
                    chosen.append({k:r[k] for k in ('id','split','cohort','side','target','run','game','moves_before','sfen')})
                    if len(chosen)==3:
                        break
                if len(chosen)!=3:
                    raise ValueError('Need three distinct games per cohort/side/result stratum')
                selected.extend(chosen)
    if len({r['id'] for r in selected})!=24 or len({' '.join(r['sfen'].split()[:3]) for r in selected})!=24:
        raise ValueError('Duplicate selected roots')
    return selected


def source_inputs():
    plan, source, rows, parts, _ = training.load()
    checkpoint = SOURCE / 'mixed/checkpoint.json'
    state = common.unseal(checkpoint)
    binding = dict(plan_sha256=base.data.digest(SOURCE/'plan.json'), method='group-guarded', arm='mixed', alpha=.5)
    training.validate(state, plan['keys'], binding, plan['training'], parts['train'])
    report = common.unseal(SOURCE/'comparison.json')
    if (not state['stopped'] or state['updates']!=200 or state['stopping_reason']!='update_budget'
            or report['checkpoint_sha256']!=base.data.digest(checkpoint) or report['plan_sha256']!=binding['plan_sha256']):
        raise ValueError('Expected fixed completed guarded candidate')
    base.data.checked(DIRECTORY/'delta.txt',report['reports']['guarded-mixed']['sidecar_sha256'])
    names = ['plan.json','comparison.json','mixed/checkpoint.json','guarded-mixed/delta.txt']
    bindings = {str(SOURCE/n):base.data.digest(SOURCE/n) for n in names}
    return source, rows, parts, report['reports']['guarded-mixed'], bindings


def export():
    with common.exclusive(SOURCE/'training.lock'):
        source, rows, _, report, bindings = source_inputs()
        binary = exporter.EXPORTER
        build = json.loads((binary.parent/'build.json').read_text())
        if (base.data.digest(binary)!=build['binary_sha256'] or base.data.digest(binary.parent/'export.cc')!=build['generated_sha256']
                or base.data.digest(ROOT/'tools/learning/native/imitation_probe.cc')!=build['probe_source_sha256']):
            raise ValueError('Exporter binding differs')
        target = DIRECTORY/'runtime'
        target.mkdir(exist_ok=False)
        (target/'bin').mkdir()
        original = base.data.DEFAULT_OUTPUT/'runtime/bin/params.bin'
        params = target/'bin/params.bin'
        layout = json.loads(subprocess.check_output([str(binary),str(original),str(DIRECTORY/'delta.txt'),str(params)],text=True))
        zero = target/'zero.txt'
        zero.write_text('')
        subprocess.run([str(binary),str(original),str(zero),str(target/'zero-params.bin')],capture_output=True,text=True,check=True)
        if base.data.digest(target/'zero-params.bin')!=base.data.digest(original):
            raise ValueError('Zero export differs')
        changed = exporter.audit_bytes(original,params,layout)
        for name, sha in source['runtime_sha256'].items():
            relative = Path(name).relative_to('runtime')
            if relative!=Path('bin/params.bin'):
                copy_verified(base.data.DEFAULT_OUTPUT/name,target/relative,sha)
        raw = {}
        for line in (DIRECTORY/'delta.txt').read_text().splitlines():
            *key, value = line.split()
            raw[':'.join(key)] = int(value)
        expected = {r['id']:r['candidate_cp'] for r in report['observations']}
        frames = common.native_frames(source,base.data.DEFAULT_OUTPUT,rows,params=params)
        for row, frame in zip(rows,frames):
            if common.check_frame(row,frame,raw)!=expected[row['id']]:
                raise ValueError('Exported score differs')
        source_inputs()
        for path, sha in bindings.items():
            base.data.checked(path,sha)
        audit = dict(schema='guarded-export-v1',inputs_sha256=bindings,static_checks=len(frames),searches=0,deployed=False,
                     changed_bytes=changed,exporter_sha256=base.data.digest(binary),
                     runtime_sha256={str(p.relative_to(target)):base.data.digest(p) for p in target.rglob('*') if p.is_file()})
        common.seal(DIRECTORY/'export-audit.json',audit)
        print(f'Exported guarded candidate: {len(frames)} static checks; no search.',flush=True)


def specification():
    source, rows, parts, _, bindings = source_inputs()
    audit = common.unseal(DIRECTORY/'export-audit.json')
    if (audit['schema']!='guarded-export-v1' or audit['inputs_sha256']!=bindings or audit['static_checks']!=len(rows)
            or audit['searches'] or audit['deployed']):
        raise ValueError('Export audit differs')
    target = DIRECTORY/'runtime'
    actual = {str(p.relative_to(target)):base.data.digest(p) for p in target.rglob('*') if p.is_file()}
    if actual!=audit['runtime_sha256']:
        raise ValueError('Candidate runtime changed')
    runtime = {str(base.data.DEFAULT_OUTPUT/n):sha for n,sha in source['runtime_sha256'].items()}
    for n,sha in source['runtime_sha256'].items():
        relative = str(Path(n).relative_to('runtime'))
        if relative!='bin/params.bin' and actual.get(relative)!=sha:
            raise ValueError('Non-parameter runtime differs')
    runtime.update({str(target/n):sha for n,sha in actual.items()})
    for path,sha in runtime.items():
        base.data.checked(path,sha)
    probe = source['probes']['replay']
    base.data.checked(ROOT/probe['path'],probe['sha256'])
    bindings[str(ROOT/probe['path'])] = probe['sha256']
    bindings[str(DIRECTORY/'export-audit.json')] = base.data.digest(DIRECTORY/'export-audit.json')
    roots = select(parts['validation'])
    replay_probe = previous.Probe(str(ROOT/probe['path']))
    try:
        for row in roots:
            replay = replay_probe.replay(row['moves_before'])
            if not replay.get('ok') or replay['positions'][-1]['sfen']!=row['sfen']:
                raise ValueError('Root replay differs')
            if any(p['occurrences']>1 for p in replay['positions']):
                raise ValueError('Repeated selected root; do not refill')
            row['huffman_hex'] = replay['positions'][-1]['huffman_hex']
    finally:
        replay_probe.close()
    return dict(schema='guarded-behavior-v1',settings=SETTINGS,roots=roots,
                inputs_sha256=bindings,runtime_sha256=runtime,probe=str(ROOT/probe['path']),
                code_sha256={**previous.dependencies(),str(Path(__file__).relative_to(ROOT)):base.data.digest(Path(__file__)),
                             'tools/learning/hybrid/export.py':base.data.digest(Path(exporter.__file__))},
                engines=dict(baseline=str(base.data.DEFAULT_OUTPUT/'runtime/bin/release'),candidate=str(target/'bin/release')))


def prepare():
    plan = specification()
    OUTPUT.mkdir(parents=True,exist_ok=False)
    common.seal(OUTPUT/'plan.json',plan)
    print('Prepared 24 roots /48 fresh searches; no search performed.',flush=True)


def load():
    plan = common.unseal(OUTPUT/'plan.json')
    if plan!=specification():
        raise ValueError('Frozen behavior plan differs')
    return plan


def summarize(plan, records):
    report = previous.aggregate(OUTPUT,plan,records)
    strata = {}
    for pair in report['pairs']:
        row = pair['root']
        key = f"{row['cohort']}_{row['side']}_{int(row['target'])}"
        group = strata.setdefault(key,dict(valid=0,changed=0))
        if 'bestmove_changed' in pair:
            group['valid']+=1
            group['changed']+=int(pair['bestmove_changed'])
    report['cohort_strata'] = strata
    common.seal(OUTPUT/'report.json',report)
    return report


def run():
    plan = load()
    with common.exclusive(OUTPUT/'run.lock'):
        records = previous.saved(OUTPUT,plan)
        report = summarize(plan,records)
        if any(r['status']=='failed' for r in records.values()):
            raise ValueError('Failed attempt blocks automatic retry; retain logs')
        if len(records)==48:
            return report
        (OUTPUT/'searches').mkdir(exist_ok=True)
        probe = previous.Probe(plan['probe'])
        try:
            for row in plan['roots']:
                for variant in ('baseline','candidate'):
                    if (row['id'],variant) in records:
                        continue
                    print(f"Search {len(records)+1}/48: {variant} {row['id']}",flush=True)
                    path = previous.paths(OUTPUT,row,variant)
                    record = dict(id=row['id'],variant=variant,plan_sha256=base.data.digest(OUTPUT/'plan.json'),status='failed',commands=[],transcript=[])
                    base.data.write_json(path.with_suffix('.attempt.json'),{k:record[k] for k in ('id','variant','plan_sha256')},exclusive=True)
                    engine = None
                    failure = None
                    try:
                        engine = previous.RecordedEngine.__new__(previous.RecordedEngine)
                        engine.__init__(Path(plan['engines'][variant]))
                        if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript):
                            raise ValueError('Engine loading error')
                        record['analysis'] = engine.analyze(row['moves_before'],SETTINGS['depth'],SETTINGS['timeout'],multipv=1)
                        if any('error' in s.lower() or 'failed' in s.lower() for s in engine.transcript):
                            raise ValueError('Engine search error')
                        record['diagnosis'] = previous.diagnose(record['analysis'],row,probe)
                        record['status'] = 'success'
                    except BaseException as error:
                        failure = error
                        record['failure'] = dict(type=type(error).__name__,message=str(error))
                    finally:
                        if engine is not None:
                            try:
                                engine.close()
                            except Exception as error:
                                record.update(status='failed',failure=dict(type=type(error).__name__,message=str(error)))
                                failure = error
                            record['commands'] = getattr(engine,'commands',[])
                            record['transcript'] = getattr(engine,'transcript',[])
                        common.seal(path,record)
                        records[(row['id'],variant)] = record
                        report = summarize(plan,records)
                    if failure is not None:
                        raise failure
        finally:
            probe.close()
            load()
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('export','prepare','run'))
    args = parser.parse_args()
    if args.command=='export':
        export()
    elif args.command=='prepare':
        prepare()
    else:
        run()
        print((OUTPUT/'summary.txt').read_text(),end='')


if __name__=='__main__':
    main()
