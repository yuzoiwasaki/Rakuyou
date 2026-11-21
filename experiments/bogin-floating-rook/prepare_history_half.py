#!/usr/bin/env python3
"""Build an isolated engine that halves shared response history once per search."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'results/history-half'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    inputs = [ROOT/'Makefile', ROOT/'bin/match', Path(__file__),
              ROOT/'books/shin-yonenaga-book-v1.txt']
    inputs += [p for p in sorted((ROOT/'src').rglob('*')) if p.is_file()]
    hashes = {str(p.relative_to(ROOT)):digest(p) for p in inputs}
    manifest = WORK/'build-manifest.json'
    build = WORK/'build'
    binary = build/'bin/match'
    if manifest.exists():
        old = json.loads(manifest.read_text())
        if old['input_sha256'] != hashes or digest(binary) != old['binary_sha256']:
            raise ValueError('History-half build inputs/binary changed; preserve existing runs before rebuilding')
        return binary
    WORK.mkdir(parents=True,exist_ok=True)
    build.mkdir(exist_ok=False)
    shutil.copytree(ROOT/'src',build/'src')
    shutil.copy2(ROOT/'Makefile',build/'Makefile')
    shutil.copytree(ROOT/'obj/match',build/'obj/match')
    (build/'lib').symlink_to(ROOT/'lib',target_is_directory=True)
    (build/'books').mkdir()
    shutil.copy2(ROOT/'books/shin-yonenaga-book-v1.txt',build/'books/shin-yonenaga-book-v1.txt')
    (build/'bin').mkdir()
    for name in ('params.bin','progress.bin','probability.bin','book.bin'):
        (build/'bin'/name).symlink_to(ROOT/'bin'/name)

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

  void Halve() {
    for (Square s : Square::all_squares()) {
      for (Piece p : Piece::all_pieces()) table_[s][p] /= 2;
    }
  }

 private:
  ArrayMap<int16_t, Square, Piece> table_;''')
    replace('stats.h',''' private:
  std::unique_ptr<ArrayMap<HistoryStats, Square, Piece>> table_;''','''  void Halve() {
    for (Square s : Square::all_squares()) {
      for (Piece p : Piece::all_pieces()) (*table_)[s][p].Halve();
    }
  }

 private:
  std::unique_ptr<ArrayMap<HistoryStats, Square, Piece>> table_;''')
    replace('thread.cc','''                                       uint64_t nodes_limit) {
  // ワーカースレッドの探索を開始する''','''                                       uint64_t nodes_limit) {
  // Once per actual search, before any worker starts. Keep TT and probability cache.
  shared_data_.countermoves_history.Halve();
  // ワーカースレッドの探索を開始する''')
    with (WORK/'build.log').open('w') as log:
        subprocess.run(['make','-j2','TARGET=match','executable'],cwd=build,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    assert all(digest(ROOT/name)==h for name,h in hashes.items())
    manifest.write_text(json.dumps({'input_sha256':hashes,'binary_sha256':digest(binary),
        'policy':'Halve shared countermove history once at ParallelSearch entry before workers. No change for book replies; TT/probability cache retained.',
        'patched_sources':{name:digest(build/'src'/name) for name in ('stats.h','thread.cc')}},indent=2)+'\n')
    print('Isolated history-half engine ready:',binary,flush=True)
    return binary


if __name__ == '__main__':
    prepare()
