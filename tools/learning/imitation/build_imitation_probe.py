#!/usr/bin/env python3
"""Build an isolated static KP/PP probe via existing Makefile overrides."""
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:_sys.path.insert(0,str(_RepoPath(__file__).resolve().parents[3]))
import json
import subprocess
from tools.learning.data.prepare_learning_data import ROOT,digest

OUTPUT=ROOT/'results/imitation-tools/imitation-probe'


def build():
    if OUTPUT.exists():raise FileExistsError('Refuse to overwrite the imitation probe')
    sources=sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'src').glob('*.cc') if p.name!='main.cc')
    sources.append('tools/learning/native/imitation_probe.cc')
    command=['make','TARGET=gold-silver-pair-probe','executable','-j2',
             'sources='+' '.join(sources),'output_file='+OUTPUT.relative_to(ROOT).as_posix(),
             'object_dir=results/layout-build-check/obj']
    subprocess.run(command,cwd=ROOT,check=True)
    paths=[ROOT/'Makefile',ROOT/'tools/learning/native/learning_data_probe.cc',ROOT/'tools/learning/native/imitation_probe.cc']
    report=dict(command=command,probe_sha256=digest(OUTPUT),inputs={p.relative_to(ROOT).as_posix():digest(p) for p in paths},
                searches=0,updates=0)
    with (OUTPUT.parent/'build-report.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
    return report


if __name__=='__main__':build()
