"""Rebuild the adopted baseline separately, preserving frozen experiment inputs."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New, nonexistent build directory')
    args = parser.parse_args()
    out = args.output.resolve()
    hashes = json.loads((HERE / 'base-hashes.json').read_text())
    for name, expected in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Base source changed; review patch before rebuilding: ' + name)
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'source'
    source.mkdir()
    shutil.copytree(ROOT / 'src', source / 'src')
    shutil.copy2(ROOT / 'Makefile', source / 'Makefile')
    (source / 'lib').symlink_to(ROOT / 'lib', target_is_directory=True)
    subprocess.run(['patch', '-p1', '--batch', '-i', str(HERE / 'adoption.patch')],
                   cwd=source, check=True)
    runtime = out / 'runtime'
    runtime.mkdir()
    for name in ('params.bin', 'progress.bin', 'probability.bin', 'book.bin'):
        (runtime / name).symlink_to(ROOT / 'bin' / name)
    shutil.copy2(ROOT / 'books/shin-yonenaga-book-v1.txt', runtime / 'shin-yonenaga-book-v1.txt')
    command = ['make', 'TARGET=development', 'executable', '-j2',
               'output_file=../runtime/release',
               'LDFLAGS=-Llib/libomp-x86_64/lib -Wl,-rpath,' + str(ROOT / 'lib/libomp-x86_64/lib')]
    with (out / 'build.log').open('x') as log:
        subprocess.run(command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    launcher = runtime / 'rakuyou'
    launcher.write_text('#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\nexec ./release "$@"\n')
    launcher.chmod(0o755)
    manifest = {'binary_sha256': hashlib.sha256((runtime / 'release').read_bytes()).hexdigest(),
                'patch_sha256': hashlib.sha256((HERE / 'adoption.patch').read_bytes()).hexdigest(),
                'base_source_hashes': hashes}
    (out / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(runtime / 'rakuyou')


if __name__ == '__main__':
    main()
