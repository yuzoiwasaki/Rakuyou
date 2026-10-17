"""Build only the standalone referee; never rebuild the operational engine."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ['square', 'bitboard', 'extended_board', 'position', 'move', 'movegen', 'hand', 'zobrist']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output=None):
    output = Path(output or ROOT / 'results/match-tools-v2/match-referee').resolve()
    if not output.is_relative_to((ROOT / 'results').resolve()):
        raise ValueError('referee output must be inside repository results/')
    if output.exists() or (output.parent / 'build.json').exists():
        raise FileExistsError('refuse to overwrite an existing referee or build manifest')
    output.parent.mkdir(parents=True, exist_ok=True)
    objdir = output.parent / 'objects'
    objdir.mkdir(exist_ok=True)
    flags = ['-std=c++11', '-O2', '-g', '-msse4.2', '-Isrc']
    if platform.system() == 'Darwin':
        sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
        flags += ['-arch', 'x86_64', '-I' + sdk + '/usr/include/c++/v1']
    compiler = 'c++'
    commands, inputs, objects = [], [], []
    # Own isolated objects bind all implementations to current source, never touch
    # learning-probe objects or operational engine build outputs.
    sources = [ROOT / ('src/' + name + '.cc') for name in SOURCES]
    sources += [ROOT / 'tools/learning/native/match_referee.cc']
    for source in sources:
        obj = objdir / (source.stem + '.o')
        command = [compiler, *flags, '-c', str(source), '-o', str(obj)]
        subprocess.run(command, cwd=ROOT, check=True)
        commands.append(command)
        inputs.append({'source': str(source.relative_to(ROOT)), 'source_sha256': sha(source),
                       'object': str(obj.relative_to(output.parent)), 'object_sha256': sha(obj)})
        objects.append(str(obj))
    command = [compiler, *flags, *objects, '-o', str(output)]
    subprocess.run(command, cwd=ROOT, check=True)
    commands.append(command)
    manifest = {'schema': 'match-referee-build-v1', 'binary_sha256': sha(output),
                'build_recipe_sha256': sha(Path(__file__)),
                'compiler': subprocess.check_output([compiler, '--version'], text=True),
                'inputs': inputs, 'headers': {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'src').glob('*.h'))},
                'commands': commands, 'search_or_engine_build': False}
    (output.parent / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    print(build(parser.parse_args().output))
