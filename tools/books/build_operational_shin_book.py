#!/usr/bin/env python3
"""Generate the operational book from its single maintained source.

Native engine tests check legality and transposed-position collisions.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'books/shin-yonenaga-book.json'
OUTPUT = ROOT / 'books/shin-yonenaga-book-v1.txt'
MOVE = re.compile(r'(?:[1-9][a-i][1-9][a-i]\+?|[PLNSGBR]\*[1-9][a-i])\Z')


def compile_operational_book(source=SOURCE):
    data = json.loads(source.read_text(encoding='utf-8'))
    if data.get('initial_position') != 'startpos':
        raise ValueError('Expected startpos source')
    lines = ['# Rakuyou Shin-Yonenaga-Gyoku operational book',
             '# USI moves from startpos | book move']
    seen, ids = set(), set()
    for entry in data['entries']:
        side, moves, move = entry['side'], entry['moves'], entry['book_move']
        if side not in ('black', 'white') or not moves:
            raise ValueError('Expected an explicit side and nonempty move sequence')
        if len(moves) % 2 != (side == 'white'):
            raise ValueError(f"Wrong side to move: {entry['id']}")
        if not all(isinstance(m, str) and MOVE.fullmatch(m) for m in moves + [move]):
            raise ValueError(f"Invalid USI move: {entry['id']}")
        if tuple(moves) in seen or entry['id'] in ids:
            raise ValueError(f"Duplicate entry: {entry['id']}")
        seen.add(tuple(moves))
        ids.add(entry['id'])
        lines.extend([f"# {entry['id']}", f"{' '.join(moves)} | {move}"])
    if not seen:
        raise ValueError('Empty book')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify without writing')
    args = parser.parse_args()
    content = compile_operational_book()
    if args.check:
        if OUTPUT.read_text(encoding='utf-8') != content:
            parser.exit(1, 'Operational book differs; regenerate it.\n')
        print('Operational book matches source')
    else:
        OUTPUT.write_text(content, encoding='utf-8')
        print(f'Wrote {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
