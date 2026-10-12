"""Regenerate retired book fixtures in temporary storage, pinned to original bytes."""

# Permit direct CLI execution as well as package imports.
import sys as _sys
from pathlib import Path as _RepoPath
if not __package__:
    _sys.path.insert(0, str(_RepoPath(__file__).resolve().parents[2]))
import atexit
import hashlib
import tempfile
from pathlib import Path
from tools.books.build_shin_book import compile_book

_DIRECTORY=tempfile.TemporaryDirectory(prefix='rakuyou-book-tests-')
atexit.register(_DIRECTORY.cleanup)
EXPECTED_SHA256={'shin-yonenaga-black-pawn26-experiment.json': '6218cbbcd7768ecd3c0e90aec650ec080e8a02dfcf14555e76edd23775ed00b1', 'shin-yonenaga-black-conditional-experiment.json': 'e08bb43bfd6c557ff402e8407b68f72443925228080d4774c60d0e2a4f72a0f7', 'shin-yonenaga-black-silver38-experiment.json': '6cbb021417a755d193eeb66de3cfd26575bfbaf711cb1f89382e80ed712bf0c0', 'shin-yonenaga-black-silver38-silver32-experiment.json': '42622adc1fb4cc479bd70af352e296b4b5fa413f91ccad9ea4fc161866ea5a17', 'shin-yonenaga-black-silver38-silver32-pawn76-experiment.json': '284850ec7495a4d1889c79d393fe75e775cc56dc3cfe7b7ec7af2b0df1b9c299', 'shin-yonenaga-black-silver38-silver32-pawn25-silver68-experiment.json': '1fb65e90a39cd882e7689e28c5a9cbcba33775c4a2fd712cabf5f71db2ab67a9', 'shin-yonenaga-white-candidates.json': 'b5bdc56d18663949f76dad48353a96c00bcd4d29e70f80336a93c35c2cd3690f'}


def generated_book(source,side='black',experimental=True):
    content=compile_book(source,experimental=experimental,side=side)
    if hashlib.sha256(content.encode()).hexdigest()!=EXPECTED_SHA256[source.name]:
        raise ValueError('Retired book differs from its saved original')
    output=Path(_DIRECTORY.name)/(source.stem+'.txt')
    output.write_text(content)
    return output
