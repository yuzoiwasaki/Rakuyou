#!/usr/bin/env python3
"""One-shot shared-history decay probes in a disposable diagnostic build."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from run_matches import MatchEngine, save


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for key in list(os.environ):
        if key.startswith('RAKUYOU'):
            del os.environ[key]
    previous = ROOT/'results/floating-rook-s42/depth-diagnostic/carried-state'
    provenance = json.loads((previous/'report.json').read_text())
    assert provenance['original_files_unchanged']
    assert all(digest(ROOT/name)==value for name,value in provenance['original_sha256'].items())
    assert digest(previous/'build/bin/match')==provenance['diagnostic_binary_sha256']
    work = ROOT/'results/floating-rook-s42/depth-diagnostic/history-decay'
    work.mkdir(parents=True,exist_ok=False)
    build = work/'build'
    shutil.copytree(previous/'build',build,symlinks=True)

    def replace(name,before,after):
        path=build/'src'/name
        text=path.read_text()
        assert text.count(before)==1,name
        path.write_text(text.replace(before,after))

    replace('stats.h','''  void Clear() {
    table_.clear();
  }

 private:
  ArrayMap<int16_t, Square, Piece> table_;''','''  void Clear() {
    table_.clear();
  }

  void DiagnosticDivide(int divisor) {
    for (Square s : Square::all_squares()) {
      for (Piece p : Piece::all_pieces()) table_[s][p] /= divisor;
    }
  }

 private:
  ArrayMap<int16_t, Square, Piece> table_;''')
    replace('stats.h',''' private:
  std::unique_ptr<ArrayMap<HistoryStats, Square, Piece>> table_;''','''  void DiagnosticDivide(int divisor) {
    for (Square s : Square::all_squares()) {
      for (Piece p : Piece::all_pieces()) (*table_)[s][p].DiagnosticDivide(divisor);
    }
  }

 private:
  std::unique_ptr<ArrayMap<HistoryStats, Square, Piece>> table_;''')
    replace('thinking.h','  void StartNewGame();','  void StartNewGame();\n  void DiagnosticDecayHistory(int divisor);')
    replace('thinking.cc','void Thinking::StartNewGame() {','''void Thinking::DiagnosticDecayHistory(int divisor) {
  if (divisor == 0) shared_data_.countermoves_history.Clear();
  else if (divisor == 2 || divisor == 4) shared_data_.countermoves_history.DiagnosticDivide(divisor);
}

void Thinking::StartNewGame() {''')
    replace('usi.cc','  } else if (type == "usinewgame") {','''  } else if (type == "diagnostic_decay") {
    int divisor = 1;
    is >> divisor;
    thinking->DiagnosticDecayHistory(divisor);
    SYNCED_PRINTF("info string diagnostic_decay_done %d\\n", divisor);

  } else if (type == "usinewgame") {''')
    with (work/'build.log').open('w') as log:
        subprocess.run(['make','-j2','TARGET=match','executable'],cwd=build,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Decay diagnostic build ready',flush=True)
    source=ROOT/'results/floating-rook-knight77-10games.json'
    batch=json.loads(source.read_text())
    fixtures=[('gold_first38-candidate',55),('edge_first38-candidate',79),
              ('edge42-candidate',57),('before_formation36-candidate',69),('gold_first38-baseline',73)]
    data={'settings':{'depth':15,'byoyomi_ms':10000,'threads':1,'hash_mb':512,
                      'divisors':{'1':'unchanged','2':'half','4':'quarter','0':'clear'},
                      'procedure':'Fresh process per case; replay actual Shin search roots; divide shared countermove history ONLY immediately before target. TT/probability cache retained. This is not per-turn decay or a strength test.'},
          'fixtures':fixtures,'cases':[], 'original_sha256':provenance['original_sha256'],
          'diagnostic_binary_sha256':digest(build/'bin/match'),
          'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in
                         (source,Path(__file__),Path(__file__).with_name('run_matches.py'),
                          ROOT/'tools/analysis/paired_selfplay.py',previous/'report.json',
                          ROOT/'bin/params.bin',ROOT/'bin/progress.bin',ROOT/'bin/probability.bin',
                          source.with_suffix('.books')/'baseline.txt',source.with_suffix('.books')/'candidate.txt')}}
    for ident,target in fixtures:
        g=next(g for g in batch['games'] if g['id']==ident)
        expected=next(r for r in g['records'] if r['ply']==target)
        book=source.with_suffix('.books')/f"{g['arm']}.txt"
        for divisor in (1,2,4,0):
            e=MatchEngine(build/'bin/match',True,True,1,512,None,44,book)
            e.byoyomi=10000;e.new_game();prelude=[]
            try:
                for record in g['records']:
                    if record['ply']>=target:break
                    if record['player']!='shin':continue
                    ply=record['ply'];move,info,origin=e.choose_move(g['moves'][:ply-1],15,40)
                    assert move==record['move'],(ident,divisor,ply,move)
                    if info:
                        assert (info['score'],info['pv'])==(record['analysis']['score'],record['analysis']['pv']),(ident,divisor,ply)
                    prelude.append({'ply':ply,'move':move,'analysis':info,'source':origin})
                e.send(f'diagnostic_decay {divisor}')
                ack=e.wait_for(f'info string diagnostic_decay_done {divisor}',10)
                move,info,origin=e.choose_move(g['moves'][:target-1],15,40)
                if divisor==1:
                    old=expected['analysis']
                    assert (move,info['score'],info['pv'])==(expected['move'],old['score'],old['pv'])
                    assert re.search(r' nodes (\d+)',info['raw']).group(1)==re.search(r' nodes (\d+)',old['raw']).group(1)
                data['cases'].append({'game':ident,'ply':target,'divisor':divisor,'ack':ack,'root_moves':g['moves'][:target-1],
                                      'move':move,'analysis':info,'prelude':prelude})
                save(work/'report.json',data)
                print(ident,target,divisor,move,info['score'],flush=True)
            finally:e.close()
    assert all(digest(ROOT/name)==value for name,value in data['original_sha256'].items())
    data['original_files_unchanged']=True
    save(work/'report.json',data)
    print('All baseline selections/scores/PVs/nodes and all replay preludes matched; original files unchanged',flush=True)


if __name__=='__main__':
    main()
