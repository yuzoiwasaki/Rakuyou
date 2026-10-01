#!/usr/bin/env python3
"""Audit fixed-White runs and print reproducible comparison data as JSON.

Intervals are descriptive normal approximations for independent game scores;
engine state persists between games, so they are not calibrated strength tests.
"""

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from paired_selfplay import summarize


MAINLINE = '7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 7a7b 6g6f 6b7a 7i7h 8c8d'.split()


def stats(games):
    scores = [0.5 if g['winner'] is None else float(g['winner'] == 'shin_yonenaga')
              for g in games]
    if not scores:
        return {'games': 0}
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / (n - 1) if n > 1 else 0
    se = math.sqrt(variance / n)
    return {'games': n, 'wins': scores.count(1), 'losses': scores.count(0),
            'draws': scores.count(0.5), 'rate': round(mean, 4),
            'se': se, 'approx_95_interval': (
                [round(max(0, mean - 1.96 * se), 4),
                 round(min(1, mean + 1.96 * se), 4)]
                if n >= 30 and variance > 0 else None)}


def groups(games, key):
    buckets = defaultdict(list)
    for game in games:
        value = key(game)
        if value is not None:
            buckets[value].append(game)
    return [{'key': k, **stats(v)} for k, v in
            sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0]))]


def audit(document):
    games = document['games']
    assert len(games) == document['requested_games'] == 100
    assert document['settings']['shin_side'] == 'white'
    assert not document['errors']
    summary = summarize(games, 'white')
    summary['errors'] = len(document['errors'])
    assert summary == document['summary']
    for number, game in enumerate(games, 1):
        assert game['game_number'] == number
        assert game['black'] == 'normal' and game['white'] == 'shin_yonenaga'
        records = game['records']
        assert game['moves'][1] == '5a6b'
        assert game['moves'] == [r['move'] for r in records
                                 if r['move'] not in ('resign', 'win')]
        counts = {'normal': Counter(), 'shin_yonenaga': Counter()}
        for ply, record in enumerate(records, 1):
            color = 'black' if ply % 2 else 'white'
            player = game[color]
            assert record['ply'] == ply and record['color'] == color
            assert record['player'] == player
            counts[player][record['source']] += 1
        assert {p: dict(c) for p, c in counts.items()} == game['source_counts_by_player']
        assert dict(counts['normal'] + counts['shin_yonenaga']) == game['source_counts']
        if game['reason'] == 'resign':
            assert records[-1]['move'] == 'resign'
            assert game['winner'] == ('normal' if records[-1]['player'] == 'shin_yonenaga'
                                      else 'shin_yonenaga')
        elif game['reason'] == 'max_plies':
            assert len(game['moves']) == document['settings']['max_plies']
            assert game['winner'] is None
        else:
            raise AssertionError('Unexpected termination reason')
        expected = ('draw' if game['winner'] is None else
                    'white_win' if game['winner'] == 'shin_yonenaga' else 'black_win')
        assert game['result'] == expected


def review(path):
    raw = path.read_bytes()
    document = json.loads(raw)
    audit(document)
    games = document['games']
    main = [g for g in games if g['moves'][:len(MAINLINE)] == MAINLINE]
    representative = {}
    for winner, label in [('shin_yonenaga', 'win'), ('normal', 'loss'), (None, 'draw')]:
        candidates = [g for g in games if g['winner'] == winner]
        if candidates:
            game = min(candidates, key=lambda g: len(g['moves']))
            representative[label] = {'game': game['game_number'],
                                     'plies': len(game['moves']),
                                     'opening': ' '.join(game['moves'][:24])}
    king = Counter()
    for game in games:
        square = '5a'
        stayed = True
        for record in game['records']:
            move = record['move']
            if record['player'] == 'shin_yonenaga' and move[:2] == square:
                square = move[2:4]
                if record['ply'] > 2 and int(square[0]) < 6:
                    stayed = False
            if record['ply'] in (20, 40):
                king[f'ply{record["ply"]}:{square}'] += 1
        king['never_left_files_6_9_after_opening'] += stayed
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'created_at': document['created_at'], 'updated_at': document['updated_at'],
            'settings': document['settings'], 'stats': stats(games),
            'summary': document['summary'],
            'unique_full_games': len({tuple(g['moves']) for g in games}),
            'book_moves_per_game': groups(games, lambda g: str(
                g['source_counts_by_player']['shin_yonenaga'].get('dedicated_book', 0)
                + g['source_counts_by_player']['shin_yonenaga'].get('book', 0))),
            'prefix4': groups(games, lambda g: ' '.join(g['moves'][:4])),
            'prefix6': groups(games, lambda g: ' '.join(g['moves'][:6]))[:12],
            'mainline': stats(main),
            'mainline_replies': groups(main, lambda g: ' '.join(g['moves'][14:16])),
            'after_v2_entry': groups(main, lambda g: ' '.join(g['moves'][14:18]))[:12],
            'seventh_file_early': stats([g for g in games if
                '7c7d' in g['moves'][3:20:2] and '7b7c' in g['moves'][3:24:2]]),
            'seventh_file_by40': stats([g for g in games if
                '7c7d' in g['moves'][3:40:2] and '7b7c' in g['moves'][3:40:2]]),
            'king': dict(king), 'representative': representative,
            'blocks25': [stats(games[i:i + 25]) for i in range(0, 100, 25)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='+', type=Path)
    args = parser.parse_args()
    reviews = [review(path) for path in args.inputs]
    common_settings = []
    for run in reviews:
        settings = dict(run['settings'])
        settings.pop('shin_book_file', None)
        settings['players'] = {p: dict(v) for p, v in settings['players'].items()}
        settings['players']['shin_yonenaga'].pop('OwnBook')
        common_settings.append(settings)
    assert all(s == common_settings[0] for s in common_settings)
    differences = []
    for i, left in enumerate(reviews):
        for right in reviews[i + 1:]:
            delta = left['stats']['rate'] - right['stats']['rate']
            se = math.hypot(left['stats']['se'], right['stats']['se'])
            differences.append({'left': left['path'], 'right': right['path'],
                                'difference': round(delta, 4),
                                'approx_95_interval': [round(delta - 1.96 * se, 4),
                                                      round(delta + 1.96 * se, 4)]})
    print(json.dumps({'runs': reviews, 'differences': differences},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
