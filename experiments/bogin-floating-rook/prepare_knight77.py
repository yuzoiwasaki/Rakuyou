#!/usr/bin/env python3
"""Prepare a separate late-opening knight/bishop formation trial."""
import json
from pathlib import Path
from prepare import ROOT, legal, compile_operational_book, main as prepare_base
from tools.analysis.paired_selfplay import UsiEngine


def prepare():
    out = ROOT / 'results/bogin-floating-rook'
    baseline = json.loads((out / 'candidate-source.json').read_text())
    trial = json.loads(Path(__file__).with_name('knight77.json').read_text())
    additions = trial['entries']
    assert not ({tuple(e['moves']) for e in baseline['entries']} & {tuple(e['moves']) for e in additions})
    assert len({tuple(e['moves']) for e in additions}) == len(additions)
    assert all(e['side'] == 'black' and e['book_move'] in ('8i7g', '9g9f', '8h9g') for e in additions)
    assert all(len(e['moves']) < trial['book_max_ply'] for e in additions)
    source = out / 'knight77-source.json'
    book = out / 'knight77-book.txt'
    source.write_text(json.dumps({**baseline, 'entries': baseline['entries'] + additions}, indent=2) + '\n')
    book.write_text(compile_operational_book(source))
    engine = UsiEngine(ROOT / 'bin/match', True, True, 1, 64, None, trial['book_max_ply'], book)
    try:
        for entry in baseline['entries'] + additions:
            moves = entry['moves']
            for n, move in enumerate(moves + [entry['book_move']]):
                assert move in legal(engine, moves[:n]), (entry['id'], n, move)
            assert engine.choose_move(moves, 1, 30)[::2] == (entry['book_move'], 'dedicated_book'), entry['id']
        for start in trial['starts']:
            for n, move in enumerate(start['moves']):
                assert move in legal(engine, start['moves'][:n]), start['id']
        # The two actual move orders converge after ...G52 / ...P15.
        alternate = next(e for e in additions if e['id'] == 'n77_edge_first39')
        transposed = alternate['moves'] + ['8i7g', '6a5b']
        assert engine.choose_move(transposed, 1, 30)[::2] == ('9g9f', 'dedicated_book')
        main = next(e for e in additions if e['id'] == 'n77_main39')
        # Do not force the formation against a new central pawn advance.
        attacked = main['moves'] + ['8i7g', '6d6e']
        assert '6d6e' in legal(engine, attacked[:-1])
        assert engine.choose_move(attacked, 1, 30)[2] == 'search'
        p96 = next(e for e in additions if e['id'] == 'n77_p96_after_p1541')
        blocked = p96['moves'] + ['9g9f', '2b3c']
        assert '2b3c' in legal(engine, blocked[:-1])
        assert engine.choose_move(blocked, 1, 30)[2] == 'search'
        engine.send('setoption name BookMaxPly value 32')
        assert engine.choose_move(main['moves'], 1, 30)[2] == 'search'
        engine.send('setoption name BookMaxPly value 44')
        engine.send('setoption name OwnBook value false')
        assert engine.choose_move(main['moves'], 1, 30)[2] == 'search'
    finally:
        engine.close()
    print(f"Knight77 trial: {len(baseline['entries'])} baseline + {len(additions)} additions; native legality/hits/transposition/fallback/cap/OFF checked")
    return book


if __name__ == '__main__':
    prepare_base()
    prepare()
