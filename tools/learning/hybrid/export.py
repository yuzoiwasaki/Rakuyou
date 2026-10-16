"""Export one fixed hybrid arm to an isolated USI runtime, with static audits.

This performs no search, games, model selection or operational deployment.
"""
import argparse
import json
from pathlib import Path
import subprocess

from tools.learning.data.prepare_learning_data import ROOT, digest
from tools.learning.imitation.imitation_search_review import audit_bytes
from tools.learning.tempo.prepare_tempo_search import copy_verified
from .data import DEFAULT_OUTPUT, load_dataset
from .runner import ARMS, check_frame, exclusive, native_frames, unseal, seal

EXPORTER = ROOT/'results/imitation-export-tools/export'


def export(output, arm):
    output = Path(output).resolve()
    # Validate the destination before creating a lock file; revalidate inside it.
    load_dataset(output)
    with exclusive(output/'training.lock'):
        return _export_locked(output, arm)


def _export_locked(output, arm):
    output = Path(output).resolve()
    plan, dataset = load_dataset(output)
    if arm not in ARMS:
        raise ValueError('Unknown hybrid arm')
    directory = output/arm
    report = unseal(directory/'report.json')
    checkpoint = unseal(directory/'checkpoint.json')
    if (not report['eligible_for_search'] or not checkpoint['stopped']
            or report['checkpoint_sha256'] != digest(directory/'checkpoint.json')
            or report['binding'] != checkpoint['binding']
            or report['binding']['plan_sha256'] != digest(output/'plan.json')
            or report['binding']['teachers_sha256'] != digest(output/'teachers.json')
            or report['binding']['arm'] != arm
            or report['evaluation']['sidecar_sha256'] != digest(directory/'delta.txt')):
        raise ValueError('Expected eligible final arm with unchanged inputs')
    bound_inputs = {path: digest(path) for path in (
        directory/'report.json', directory/'checkpoint.json', directory/'delta.txt', output/'teachers.json')}
    build = json.loads((EXPORTER.parent/'build.json').read_text())
    if (digest(EXPORTER) != build['binary_sha256']
            or digest(EXPORTER.parent/'export.cc') != build['generated_sha256']
            or digest(ROOT/'tools/learning/native/imitation_probe.cc') != build['probe_source_sha256']):
        raise ValueError('Sparse exporter build/probe source differs')
    target = directory/'runtime'
    if target.exists():
        raise ValueError('Arm runtime already exists; retain it and its audit rather than overwrite')
    target.mkdir()
    (target/'bin').mkdir()
    params = target/'bin/params.bin'
    base = output/'runtime/bin/params.bin'
    layout = json.loads(subprocess.check_output(
        [str(EXPORTER), str(base), str(directory/'delta.txt'), str(params)], text=True))
    zero = target/'zero.txt'
    zero.write_text('')
    subprocess.run([str(EXPORTER), str(base), str(zero), str(target/'zero-params.bin')],
                   capture_output=True, text=True, check=True)
    if digest(target/'zero-params.bin') != digest(base):
        raise ValueError('Zero export does not preserve baseline')
    changed = audit_bytes(base, params, layout)
    for path, sha in plan['runtime_sha256'].items():
        relative = Path(path).relative_to('runtime')
        if relative == Path('bin/params.bin'):
            continue
        copy_verified(output/path, target/relative, sha)
    raw = {}
    for line in (directory/'delta.txt').read_text().splitlines():
        kind, a, b, lane, value = line.split()
        raw[':'.join((kind, a, b, lane))] = int(value)
    expected = {r['id']: r['candidate_cp'] for r in report['evaluation']['observations']}
    frames = native_frames(plan, output, dataset['rows'], params=params)
    for row, frame in zip(dataset['rows'], frames):
        if check_frame(row, frame, raw) != expected[row['id']]:
            raise ValueError('Exported table differs from learned sidecar')
    load_dataset(output)
    if any(digest(path) != sha for path, sha in bound_inputs.items()):
        raise ValueError('Candidate inputs changed during export')
    result = dict(schema='rakuyou-hybrid-export-v1', arm=arm,
                  arm_report_sha256=digest(directory/'report.json'),
                  params_sha256=digest(params), changed_bytes=changed,
                  zero_export_sha256=digest(target/'zero-params.bin'),
                  exporter_sha256=digest(EXPORTER), layout=layout,
                  static_checks=len(dataset['rows']), searches=0, deployed=False,
                  runtime_sha256={str(p.relative_to(target)): digest(p)
                                  for p in target.rglob('*') if p.is_file()})
    seal(directory/'export-audit.json', result)
    print(f'Isolated {arm} engine: {target/"bin/release"}; {len(frames)} static checks passed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--arm', choices=tuple(ARMS), required=True)
    args = parser.parse_args()
    export(args.output, args.arm)


if __name__ == '__main__':
    main()
