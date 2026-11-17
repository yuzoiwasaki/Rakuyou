#!/usr/bin/env python3
"""Build a separate trial book; operational source and book stay untouched."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.books.build_operational_shin_book import SOURCE as BASE, compile_operational_book
SOURCE = ROOT / 'books/experiments/white-king62.json'
OUTPUT = ROOT / 'books/white-king62-trial.txt'


def build():
    data = json.loads(BASE.read_text())
    entries = data['entries']
    indices = {tuple(e['moves']): i for i, e in enumerate(entries)}
    overrides = 0
    for entry in json.loads(SOURCE.read_text())['entries']:
        key = tuple(entry['moves'])
        if key in indices:
            old = entries[indices[key]]
            if old['id'] != 'mainline_after_66_pawn' or old['book_move'] != '6b7a':
                raise ValueError('Unexpected operational entry replacement')
            entries[indices[key]] = entry
            overrides += 1
        else:
            indices[key] = len(entries)
            entries.append(entry)
    if overrides != 1:
        raise ValueError('Expected exactly the reviewed king-retreat replacement')
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'combined.json'
        source.write_text(json.dumps(data))
        return compile_operational_book(source).replace('operational book', 'king62 trial book', 1)


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
