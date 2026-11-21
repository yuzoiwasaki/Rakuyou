#!/usr/bin/env python3
"""Isolate carried search state in a disposable copy, never the installed engine."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from run_matches import MatchEngine, save


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for key in list(os.environ):
        if key.startswith('RAKUYOU'):
            del os.environ[key]
    work = ROOT / 'results/floating-rook-s42/depth-diagnostic/carried-state'
    work.mkdir(parents=True, exist_ok=False)
    build = work / 'build'
    build.mkdir()
    shutil.copytree(ROOT / 'src', build / 'src')
    shutil.copy2(ROOT / 'Makefile', build / 'Makefile')
    # Reuse objects only in the disposable copy. Make tracks changed dependencies.
    shutil.copytree(ROOT / 'obj/match', build / 'obj/match')
    (build / 'lib').symlink_to(ROOT / 'lib', target_is_directory=True)
    (build / 'books').mkdir()
    shutil.copy2(ROOT / 'books/shin-yonenaga-book-v1.txt', build / 'books/shin-yonenaga-book-v1.txt')
    (build / 'bin').mkdir()
    for name in ('params.bin', 'progress.bin', 'probability.bin', 'book.bin'):
        (build / 'bin' / name).symlink_to(ROOT / 'bin' / name)
    originals = {str(p.relative_to(ROOT)): digest(p) for p in
                 [ROOT / 'bin/match', ROOT / 'Makefile', *sorted((ROOT / 'src').rglob('*'))]
                 if p.is_file()}

    def replace(name, before, after):
        path = build / 'src' / name
        text = path.read_text()
        assert text.count(before) == 1, name
        path.write_text(text.replace(before, after))

    replace('thinking.h', '  void StartNewGame();',
            '  void StartNewGame();\n  void DiagnosticClearSearchState(int mask);')
    replace('thinking.cc', 'void Thinking::StartNewGame() {', '''void Thinking::DiagnosticClearSearchState(int mask) {
  if (mask & 1) shared_data_.hash_table.Clear();
  if (mask & 2) shared_data_.countermoves_history.Clear();
  if (mask & 4) MoveProbability::SetCacheTableSize(
      ProbabilityCacheTable::kDefaultSize * usi_options_["Threads"]);
}

void Thinking::StartNewGame() {''')
    replace('usi.cc', '  } else if (type == "usinewgame") {', '''  } else if (type == "diagnostic_clear") {
    int mask = 0;
    is >> mask;
    thinking->DiagnosticClearSearchState(mask);
    SYNCED_PRINTF("info string diagnostic_clear_done %d\\n", mask);

  } else if (type == "usinewgame") {''')
    with (work / 'build.log').open('w') as log:
        subprocess.run(['make', '-j2', 'TARGET=match', 'executable'], cwd=build,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    print('Disposable diagnostic build ready', flush=True)
    source = ROOT / 'results/floating-rook-knight77-10games.json'
    game = next(g for g in json.loads(source.read_text())['games'] if g['id'] == 'gold_first38-candidate')
    book = source.with_suffix('.books') / 'candidate.txt'
    expected = next(r['analysis'] for r in game['records'] if r['ply'] == 55)
    data = {'original_sha256': originals, 'diagnostic_binary_sha256': digest(build / 'bin/match'),
            'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                             (source, book, Path(__file__), ROOT/'bin/params.bin', ROOT/'bin/progress.bin', ROOT/'bin/probability.bin')},
            'settings': {'depth':15, 'byoyomi_ms':10000, 'hash_mb':512, 'threads':1,
                         'target_ply':55, 'mask_bits':{'1':'transposition table', '2':'shared countermove history', '4':'move probability cache'},
                         'procedure':'Fresh process per case; replay actual Shin roots39..53 with frozen book; clear selected state only before55; normal replies replayed'},
            'cases': []}
    for mask in range(8):
        e = MatchEngine(build / 'bin/match', True, True, 1, 512, None, 44, book)
        e.byoyomi = 10000
        e.new_game()
        prelude = []
        try:
            for ply in range(39,55,2):
                move, info, origin = e.choose_move(game['moves'][:ply-1],15,40)
                assert move == game['moves'][ply-1], (mask,ply,move)
                previous = next(r for r in game['records'] if r['ply']==ply)
                if info:
                    assert (info['score'], info['pv']) == (previous['analysis']['score'], previous['analysis']['pv']), (mask,ply)
                prelude.append({'ply':ply,'move':move,'analysis':info,'source':origin})
            e.send(f'diagnostic_clear {mask}')
            ack = e.wait_for(f'info string diagnostic_clear_done {mask}',10)
            move, info, origin = e.choose_move(game['moves'][:54],15,40)
            if mask == 0:
                assert (move,info['score'],info['pv']) == ('6d5c',expected['score'],expected['pv'])
                assert re.search(r' nodes (\d+)',info['raw']).group(1) == re.search(r' nodes (\d+)',expected['raw']).group(1)
            data['cases'].append({'mask':mask,'ack':ack,'prelude':prelude,'move':move,'analysis':info})
            save(work/'report.json',data)
            print(mask,move,info['score'],info['raw'],flush=True)
        finally:
            e.close()
    assert all(digest(ROOT/name)==value for name,value in originals.items())
    data['original_files_unchanged'] = True
    save(work/'report.json',data)
    print('Original sources and bin/match unchanged; all replay preludes and mask0 baseline verified',flush=True)


if __name__ == '__main__':
    main()
