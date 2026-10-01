#!/usr/bin/env python3
"""Replay White-run piece placement to audit repetition and opening structures.

This checks ownership, captures, promotions and hands, not full move legality
or perpetual-check adjudication. Four occurrences include board, hands and turn.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from review_white_runs import audit, stats


class Board:
    def __init__(self):
        self.pieces = {}
        for file, piece in zip(range(9, 0, -1), 'lnsgkgsnl'):
            self.pieces[f'{file}a'] = piece
            self.pieces[f'{file}i'] = piece.upper()
        for file in range(1, 10):
            self.pieces[f'{file}c'] = 'p'
            self.pieces[f'{file}g'] = 'P'
        self.pieces.update({'8b': 'r', '2b': 'b', '8h': 'B', '2h': 'R'})
        self.hands = [Counter(), Counter()]
        self.ply = 0

    def push(self, move):
        black = self.ply % 2 == 0
        color = 0 if black else 1
        target = move[2:4]
        if move[1] == '*':
            kind = move[0]
            assert self.hands[color][kind] > 0 and target not in self.pieces
            self.hands[color][kind] -= 1
            piece = kind if black else kind.lower()
        else:
            piece = self.pieces.pop(move[:2])
            assert piece[-1].isupper() == black
            if target in self.pieces:
                captured = self.pieces.pop(target)
                assert captured[-1].isupper() != black and captured[-1].upper() != 'K'
                self.hands[color][captured[-1].upper()] += 1
            if move.endswith('+'):
                assert not piece.startswith('+') and piece[-1].upper() in 'PLNSBR'
                piece = '+' + piece
        self.pieces[target] = piece
        self.ply += 1

    def sfen(self):
        rows = []
        for rank in 'abcdefghi':
            row = ''
            empty = 0
            for file in range(9, 0, -1):
                piece = self.pieces.get(f'{file}{rank}')
                if piece:
                    row += (str(empty) if empty else '') + piece
                    empty = 0
                else:
                    empty += 1
            row += str(empty) if empty else ''
            rows.append(row)
        hands = ''
        for color in range(2):
            for kind in 'RBGSNLP':
                count = self.hands[color][kind]
                if count:
                    hands += (str(count) if count > 1 else '')
                    hands += kind if color == 0 else kind.lower()
        return '/'.join(rows) + (' b ' if self.ply % 2 == 0 else ' w ') + (hands or '-')


def audit_positions(path):
    document = json.loads(path.read_text())
    audit(document)
    games = document['games']
    repetitions = []
    buckets = defaultdict(list)
    rook = defaultdict(list)
    end_positions = []
    for game in games:
        board = Board()
        occurrences = defaultdict(list)
        occurrences[board.sfen()].append(0)
        first_repeat = None
        reached = set()
        for ply, move in enumerate(game['moves'], 1):
            board.push(move)
            sfen = board.sfen()
            occurrences[sfen].append(ply)
            if len(occurrences[sfen]) == 4 and first_repeat is None:
                first_repeat = {'game': game['game_number'], 'ply': ply,
                                'occurrences': list(occurrences[sfen]),
                                'saved_winner': game['winner'],
                                'saved_reason': game['reason'], 'sfen': sfen}
            if ply <= 40:
                if (board.pieces.get('7c') == 's' and board.pieces.get('7d') == 'p'):
                    reached.add('silver73_pawn74_by40')
                    if board.pieces.get('7a') == 'k':
                        reached.add('king71_silver73_pawn74_by40')
                if board.pieces.get('1e') == 'p':
                    reached.add('pawn15_by40')
                if board.pieces.get('8b') == 'k' and board.pieces.get('8c') == 's':
                    reached.add('king82_silver83_by40')
                if ply == 24:
                    for square, piece in board.pieces.items():
                        if piece == 'r':
                            rook[square].append(game)
        for feature in reached:
            buckets[feature].append(game)
        if first_repeat:
            repetitions.append(first_repeat)
        end_positions.append({'game': game['game_number'],
                              'sfen': board.sfen() + f' {len(game["moves"]) + 1}'})
    return {'path': str(path),
            'four_occurrences': repetitions,
            'repeat_saved_results': stats([g for g in games if
                g['game_number'] in {r['game'] for r in repetitions}]),
            'features': {name: stats(group) for name, group in buckets.items()},
            'rook_at24': {square: stats(group) for square, group in rook.items()},
            'end_positions': end_positions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--include-end-positions', action='store_true')
    args = parser.parse_args()
    results = [audit_positions(path) for path in args.inputs]
    if not args.include_end_positions:
        for result in results:
            result.pop('end_positions')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
