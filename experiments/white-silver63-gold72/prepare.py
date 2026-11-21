"""Prepare isolated books and a frozen runtime; never alter the installed book."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.analysis.paired_selfplay import UsiEngine
from tools.books.build_operational_shin_book import compile_operational_book, MOVE
OUT = ROOT / 'results/white-silver63-gold72'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def legal(e, moves):
    e.send('position startpos' + (' moves ' + ' '.join(moves) if moves else ''))
    e.send('legalmoves'); e.send('d')
    found = set()
    while True:
        line = e.lines.get(timeout=10)
        if line.startswith('move: '): return found
        words = line.split()
        if words and all(MOVE.fullmatch(w) for w in words): found.update(words)

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    names = ('match','params.bin','progress.bin','probability.bin')
    hashes = {n:digest(ROOT/'bin'/n) for n in names}
    runtime = OUT/'runtime'; manifest = runtime/'manifest.json'
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        if saved != hashes or any(digest(runtime/'bin'/n)!=h for n,h in saved.items()):
            raise ValueError('Frozen runtime or source changed; keep this run isolated')
    else:
        (runtime/'bin').mkdir(parents=True, exist_ok=False)
        for n in names: shutil.copy2(ROOT/'bin'/n, runtime/'bin'/n)
        (runtime/'lib').symlink_to(ROOT/'lib', target_is_directory=True)
        manifest.write_text(json.dumps(hashes,indent=2)+'\n')
    base=json.loads((ROOT/'books/shin-yonenaga-book.json').read_text())
    trial=json.loads(Path(__file__).with_name('trial.json').read_text())
    assert not ({tuple(x['moves']) for x in base['entries']} & {tuple(x['moves']) for x in trial['entries']})
    candidate={**base,'entries':base['entries']+trial['entries']}
    for arm, data in [('baseline',base),('candidate',candidate)]:
        src=OUT/f'{arm}-source.json';src.write_text(json.dumps(data,indent=2)+'\n')
        (OUT/f'{arm}.txt').write_text(compile_operational_book(src))
    e=UsiEngine(runtime/'bin/match',True,True,1,64,None,44,OUT/'candidate.txt')
    try:
        for entry in candidate['entries']:
            moves=entry['moves']
            for n,m in enumerate(moves+[entry['book_move']]): assert m in legal(e,moves[:n]),(entry['id'],n,m)
            assert e.choose_move(moves,1,30)[::2]==(entry['book_move'],'dedicated_book'),entry['id']
        for start in trial['starts']:
            for n,m in enumerate(start['moves']): assert m in legal(e,start['moves'][:n])
        for entry,replies in [(trial['entries'][0],['5f6e','6i5h']), (trial['entries'][1],['4g4f','3i2h','1g1f'])]:
            for reply in replies:
                moves=entry['moves']+[entry['book_move'],reply]
                assert reply in legal(e,moves[:-1])
                assert e.choose_move(moves,1,30)[2]=='search'
        e.send('setoption name OwnBook value false')
        assert e.choose_move(trial['entries'][0]['moves'],1,30)[2]=='search'
    finally:e.close()
    print('Prepared baseline67/candidate69; frozen engine/data, legality/hits/fallback/OFF checked')
    return runtime/'bin/match'

if __name__=='__main__':prepare()
