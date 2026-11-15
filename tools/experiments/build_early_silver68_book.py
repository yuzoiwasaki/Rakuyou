#!/usr/bin/env python3
"""Build the trial book without changing the operational book."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.books.build_shin_book import compile_book
SOURCE = ROOT / 'books/sources/black/early-silver68-pawn46.json'
BASE = ROOT / 'books/shin-yonenaga-book-v1.txt'
OUTPUT = ROOT / 'books/early-silver68-pawn46-trial.txt'


def rows(text):
    return [line for line in text.splitlines() if line and not line.startswith('#')]


def build():
    original = rows(BASE.read_text())
    added = rows(compile_book(SOURCE, experimental=True, side='black'))
    keys = {line.split(' | ')[0] for line in added}
    replaced = [line for line in original if line.split(' | ')[0] in keys]
    if replaced != ['5i4h 3c3d | 7g7f']:
        raise ValueError('unexpected operational book replacement')
    combined = [line for line in original if line not in replaced] + added
    return '# Trial only: early silver68; reviewed pawn46 and silver38-to47\n' + '\n'.join(combined) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = build()
    if args.check:
        if OUTPUT.read_text() != content:
            raise SystemExit('Trial book differs from sources')
        print('Trial book matches sources')
    else:
        OUTPUT.write_text(content)
        print(OUTPUT.relative_to(ROOT))
