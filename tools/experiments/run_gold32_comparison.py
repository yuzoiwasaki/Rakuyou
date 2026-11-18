#!/usr/bin/env python3
"""Branch-only comparison from the reviewed position before White's gold move."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.paired_selfplay import UsiEngine, play_game, save_document
from tools.experiments.build_white_king62_book import SOURCE


class FixedStart:
    def __init__(self, engine, prefix):
        self.engine, self.prefix = engine, prefix

    def __getattr__(self, name):
        return getattr(self.engine, name)

    def choose_move(self, moves, depth, timeout):
        if len(moves) < len(self.prefix):
            if moves != self.prefix[:len(moves)]:
                raise ValueError('Fixed start mismatch')
            return self.prefix[len(moves)], None, 'fixed_start'
        return self.engine.choose_move(moves, depth, timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--games', type=int, default=10, help='Games per arm')
    parser.add_argument('--depth', type=int, default=15)
    parser.add_argument('--max-plies', type=int, default=256, help='Total including fixed 27 plies')
    parser.add_argument('--hash', type=int, default=512, dest='hash_mb')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'results'/('gold32-comparison-'+datetime.now().strftime('%Y%m%d-%H%M%S')))
    args = parser.parse_args()
    entries = json.loads(SOURCE.read_text())['entries']
    prefix = next(e['moves'] for e in entries if e['id']=='gold32-trial-ply28')
    if args.games < 1 or args.depth < 1 or args.hash_mb < 1 or args.max_plies <= len(prefix):
        parser.error('Positive settings and max-plies greater than 27 required')
    local = ROOT/'results/white-king62'
    manifest = json.loads((local/'gold32-match-manifest.json').read_text())
    books = {'previous':local/'before-gold32-book.txt', 'candidate':local/'gold32-candidate-book.txt'}
    for book in books.values():
        if hashlib.sha256(book.read_bytes()).hexdigest() != manifest[book.name]:
            raise SystemExit(f'Frozen book mismatch: {book}')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for arm, book in books.items():
        output = args.output_dir/(arm+'.json')
        doc = {'created_at':datetime.now().astimezone().isoformat(), 'requested_games':args.games,
               'settings':{'shin_side':'white','arm':arm,'engine':str(ROOT/'bin/match'),
                           'depth':args.depth,'threads_per_engine':1,'hash_mb_per_engine':args.hash_mb,
                           'book_max_ply':36,'max_plies':args.max_plies,'timeout_seconds':300,
                           'shin_book_file':str(book),'book_sha256':manifest[book.name],
                           'fixed_start_moves':prefix,'normal_book':False,'shin_book':True,
                           'note':'Known 27-ply start repeated; descriptive style review, not independent strength samples. Engines retained within each arm; TT not cleared.'},
               'games':[],'errors':[]}
        engines = {}
        try:
            for name, shin in [('normal',False),('shin_yonenaga',True)]:
                e = UsiEngine(ROOT/'bin/match',shin,shin,1,args.hash_mb,None,36,book if shin else None)
                engines[name] = FixedStart(e,prefix)
            for index in range(args.games):
                print(f'{arm} {index+1}/{args.games}',flush=True)
                game = play_game(engines,'normal','shin_yonenaga',args.depth,args.max_plies,300)
                game['game_number'] = index+1
                doc['games'].append(game)
                save_document(doc,output)
                hits=[r['ply'] for r in game['records'] if r['source']=='dedicated_book']
                print(f"  {game['reason']}; winner={game['winner']}; book={hits}",flush=True)
        except Exception as exc:
            doc['errors'].append({'type':type(exc).__name__,'message':str(exc)})
            save_document(doc,output)
            raise
        finally:
            for engine in engines.values():
                engine.close()
        print(arm,doc['summary']['players']['shin_yonenaga'],flush=True)
    print('Saved:',args.output_dir,flush=True)


if __name__=='__main__':
    main()
