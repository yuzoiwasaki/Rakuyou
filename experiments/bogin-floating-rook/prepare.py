#!/usr/bin/env python3
"""Build and verify the isolated floating-rook book (not the installed book)."""
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
    out = ROOT / 'results/bogin-floating-rook'
    out.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'books/shin-yonenaga-book.json'
    baseline = json.loads(source.read_text())
    delta = json.loads(Path(__file__).with_name('entries.json').read_text())
    additions = delta['entries']
    replacements = {tuple(e['moves']): e for e in additions}
    overridden = [e['id'] for e in baseline['entries'] if tuple(e['moves']) in replacements]
    assert sorted(overridden) == sorted(delta['overrides']), overridden
    retained = [e for e in baseline['entries'] if tuple(e['moves']) not in replacements]
    candidate = {**baseline, 'entries': retained + additions}
    assert [e for e in candidate['entries'] if e['side'] == 'white'] == [e for e in baseline['entries'] if e['side'] == 'white']
    assert all(e['book_move'] not in ('4g4f', '3g3f', '3i2h') for e in additions)
    assert all(len(e['moves']) < 32 for e in additions)
    combined = out / 'candidate-source.json'
    combined.write_text(json.dumps(candidate, indent=2) + '\n')
    baseline_book = out / 'baseline-book.txt'
    candidate_book = out / 'candidate-book.txt'
    baseline_book.write_text(compile_operational_book(source))
    candidate_book.write_text(compile_operational_book(combined))
    engine = UsiEngine(ROOT / 'bin/match', True, True, 1, 64, None, 32, candidate_book)
    try:
        for entry in candidate['entries']:
            moves = entry['moves']
            for n, move in enumerate(moves + [entry['book_move']]):
                assert move in legal(engine, moves[:n]), (entry['id'], n, move)
            move, _, origin = engine.choose_move(moves, 1, 30)
            assert (move, origin) == (entry['book_move'], 'dedicated_book'), entry['id']
        root = additions[0]['moves']
        promotion = next(e for e in additions if e['id'] == 'floating_exchange_ply23')
        defended = next(e for e in additions if e['id'] == 'floating_exchange_ply23_after_g32')
        assert engine.choose_move(promotion['moves'], 1, 30)[::2] == ('2d2c+', 'dedicated_book')
        assert engine.choose_move(defended['moves'], 1, 30)[::2] == ('2d2f', 'dedicated_book')
        after_promotion = promotion['moves'] + ['2d2c+', '4a3b']
        assert '4a3b' in legal(engine, after_promotion[:-1])
        assert engine.choose_move(after_promotion, 1, 30)[2] == 'search'
        blocked = root + ['2g2f', '7b8c', '2f2e', '2b3c', '2h2f']
        exchanged = root + ['2g2f', '7b8c', '2f2e', '8c8d', '2e2d', '2c2d', '2h2d', '8d8e', '2d2f']
        for moves in (blocked + ['P*8f'], exchanged + ['P*8f'], root + ['2g2f', '5a4b']):
            assert moves[-1] in legal(engine, moves[:-1]), moves
            assert engine.choose_move(moves, 1, 30)[2] == 'search'
        # The move order G32 / S85 can transpose into the reviewed S38 entry.
        transposed = root + ['2g2f','7b8c','2f2e','8c8d','2e2d','2c2d','2h2d','4a3b','2d2f','8d8e']
        assert engine.choose_move(transposed, 1, 30)[::2] == ('3i3h', 'dedicated_book')
        # S42 is not equivalent to the bogin S83 shape: do not force R26 vs B33.
        s42 = next(e for e in additions if e['id'] == 'floating_s42_ply15')['moves']
        for reply in ('2b3c', 'P*8f'):
            moves = s42 + ['2g2f', '4a3b', '2f2e', reply]
            assert reply in legal(engine, moves[:-1])
            assert engine.choose_move(moves, 1, 30)[2] == 'search'
        moves = s42 + ['2g2f', '7a7b', '2f2e', '2b3c']
        assert engine.choose_move(moves, 1, 30)[::2] == ('3i3h', 'dedicated_book')
        # The common silver entry does not prescribe floating rook or right king.
        for reply in ('4a3b', '4c4d', '6c6d', '7b8c', 'P*8f'):
            continuation = moves + ['3i3h', reply]
            assert reply in legal(engine, continuation[:-1])
            assert engine.choose_move(continuation, 1, 30)[2] == 'search'
        engine.send('setoption name BookMaxPly value 18')
        assert engine.choose_move(moves, 1, 30)[2] == 'search'
        engine.send('setoption name BookMaxPly value 32')
        engine.send('setoption name OwnBook value false')
        assert engine.choose_move(additions[0]['moves'], 1, 30)[2] == 'search'
    finally:
        engine.close()
    manifest = {'book_max_ply': 32, 'overridden_baseline_entries': overridden, 'baseline_entries': len(baseline['entries']),
                'candidate_entries': len(candidate['entries']),
                'added_plies': [len(e['moves']) + 1 for e in additions],
                'checks': 'All entries legal and hit; early attacks fall back; transposition hit; OwnBook OFF honored',
                'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (source, Path(__file__).with_name('entries.json'),
                                     baseline_book, candidate_book, ROOT / 'bin/match')}}
    (out / 'book-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
