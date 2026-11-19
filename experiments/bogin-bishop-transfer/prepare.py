#!/usr/bin/env python3
"""Build and verify the isolated bishop-transfer book (not the installed book)."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.books.build_operational_shin_book import compile_operational_book, MOVE
from tools.analysis.paired_selfplay import UsiEngine


def legal(engine, moves):
    engine.send('position startpos moves ' + ' '.join(moves))
    engine.send('legalmoves')
    engine.send('d')
    found = set()
    while True:
        line = engine.lines.get(timeout=10)
        if line.startswith('move: '):
            return found
        words = line.split()
        if words and all(MOVE.fullmatch(w) for w in words):
            found.update(words)


def main():
    out = ROOT / 'results/bogin-bishop-transfer'
    out.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'books/shin-yonenaga-book.json'
    baseline = json.loads(source.read_text())
    additions = json.loads(Path(__file__).with_name('entries.json').read_text())['entries']
    candidate = {**baseline, 'entries': baseline['entries'] + additions}
    combined = out / 'candidate-source.json'
    combined.write_text(json.dumps(candidate, indent=2) + '\n')
    baseline_book = out / 'baseline-book.txt'
    candidate_book = out / 'candidate-book.txt'
    baseline_book.write_text(compile_operational_book(source))
    candidate_book.write_text(compile_operational_book(combined))
    engine = UsiEngine(ROOT / 'bin/match', True, True, 1, 64, None, 40, candidate_book)
    try:
        for entry in candidate['entries']:
            moves = entry['moves']
            for n, move in enumerate(moves + [entry['book_move']]):
                assert move in legal(engine, moves[:n]), (entry['id'], n, move)
            move, _, origin = engine.choose_move(moves, 1, 30)
            assert (move, origin) == (entry['book_move'], 'dedicated_book'), entry['id']
        # An immediate eighth-file attack or silver advance must return to search.
        first = additions[0]['moves'] + [additions[0]['book_move']]
        for reply in ('P*8f', '8e7f'):
            assert reply in legal(engine, first)
            assert engine.choose_move(first + [reply], 1, 30)[2] == 'search'
        reordered = first + ['6a5b', '3g3f', '3a4b']
        assert engine.choose_move(reordered, 1, 30)[::2] == ('2i3g', 'dedicated_book')
        # S53 makes immediate B79 inferior; do not force the relocation here.
        assert engine.choose_move(reordered + ['2i3g', '4b5c'], 1, 30)[2] == 'search'
        engine.send('setoption name BookMaxPly value 32')
        assert engine.choose_move(additions[-1]['moves'], 1, 30)[2] == 'search'
    finally:
        engine.close()
    manifest = {'book_max_ply': 40, 'baseline_entries': len(baseline['entries']),
                'candidate_entries': len(candidate['entries']),
                'added_plies': [len(e['moves']) + 1 for e in additions],
                'checks': 'All entries legal and hit; early attacks fall back; ply cap honored',
                'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (source, Path(__file__).with_name('entries.json'),
                                     baseline_book, candidate_book, ROOT / 'bin/match')}}
    (out / 'book-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
