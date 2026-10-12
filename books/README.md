# 新米長玉定跡

現行は **先手▲７六歩・右側構想6局面＋後手v2の11局面** の共通暫定版。
通常は [shin-yonenaga-book-v1.txt](shin-yonenaga-book-v1.txt) を使用する。

## 現行ファイル

| 用途 | ファイル | 局面数 |
| --- | --- | ---: |
| 先後共通・暫定第一運用版 | [共通v1](shin-yonenaga-book-v1.txt) | 17 |
| 先手単独・生成時の照合用 | [▲７六歩・右側構想](shin-yonenaga-black-book-pawn76-right-side-experiment.txt) | 6 |
| 後手単独・生成時の照合用 | [後手v2](shin-yonenaga-white-book-v2-experiment.txt) | 11 |

単独版の名前に `experiment` が残るが、上表は現在の運用対象。

## 使い方

将棋所等では、`ShinYonenagaGyoku` と `OwnBook` をON、`BookMaxPly` を20にし、
`ShinBookFile` で `books/shin-yonenaga-book-v1.txt` を選択する。
既存設定は自動的に切り替わらない。変更後はエンジンを再起動する。

盤面・持駒・手番が登録局面と一致すると定跡を使い、未登録局面は探索へ抜ける。
標準定跡による補完はない。初手▲４八玉／△６二玉はエンジン側の機能で、17局面には含めない。
玉戻りも合法のまま。通常側の標準定跡は `BookFile` で別に指定する。

## 生成元と確認

生成元JSONは [sources/](sources/README.md) に先後別で保存する。
リポジトリ直下で、書込みなしの確認は次の通り。

```sh
python3 tools/books/build_operational_shin_book.py --check
```

再生成する場合は同コマンドから `--check` を外す。
選択したJSONをコンパイルし、既存の単独版との一致と先手6／後手11局面を確認して結合する。
共通txtのSHA-256は
`d080bc78583695da22641509ca93682653baa4761cb633f4f144ec1aef7c7e07`。

## 保留候補と履歴

- [experiments/](experiments/README.md)：▲３六歩追加、旧▲２五歩の別構想、後手△２五歩、７筋構想。
  JSONと生成txtを先後別に保存。
- [archive/](archive/README.md)：終了した旧系列の生成元JSON。
  JSONから旧定跡を再生成できる。
- [先手の採用判断](../docs/experiments/books/black/2026-10-10-black-book-independent-review.md)と
  [後手の採用判断](../docs/experiments/books/white/2026-10-03-v2-bounded-white-improvement-cycle.md)：
  対局結果、手順、比較条件は各実験レポートを参照。
