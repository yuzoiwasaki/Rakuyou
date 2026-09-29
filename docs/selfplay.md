# 新米長玉と通常のRakuyouの比較対局

`tools/paired_selfplay.py` はRakuyouを2つ起動し、新米長玉をオンにした側と
オフにした通常側を対戦させます。既定では1組ごとに先後を交代します。
`--shin-side black|white` で新米長玉の手番を固定できます。将棋所は使いません。

```sh
python3 tools/paired_selfplay.py --depth 5
```

強さを比較する最初の実験では、深さ15で50組（100局）を実行します。

```sh
python3 tools/paired_selfplay.py \
  --depth 15 \
  --threads 1 \
  --hash 512 \
  --shin-book off \
  --pairs 50
```

後手専用定跡を後手100局で検証するときは、`--pairs` の代わりに `--games` を
指定します。`black` は新米長玉が先手、`white` は後手です。通常側はどちらの
手番でも標準定跡を使います。

```sh
python3 tools/paired_selfplay.py \
  --depth 15 --threads 1 --hash 512 \
  --shin-book on \
  --shin-book-file books/shin-yonenaga-white-book.txt \
  --shin-side white --games 100 \
  --output results/shin-v1-white-only-depth15-100games.json
```

既定値では各エンジンを1スレッド、ハッシュ128 MBで動かし、結果を
`results/shin-book-off-vs-normal-日時.json` などに保存します。JSONには設定、勝敗、USI形式の
指し手、指し手の取得元（固定初手・定跡・通常探索）、各手で最後に出力された
評価値と読み筋が入ります。

各局が終わるたびにJSONを一時ファイルへ書き、完成後に置き換えます。途中で
`Ctrl-C` を押しても、完了済みの対局は残ります。表示されたファイルを指定すると、
保存済みの条件と結果から再開できます。

```sh
python3 tools/paired_selfplay.py --resume results/shin-book-off-vs-normal-日時.json
```

再開時に全体の組数を増やすこともできます。

```sh
python3 tools/paired_selfplay.py \
  --resume results/shin-book-off-vs-normal-日時.json \
  --pairs 200
```

先後固定の結果も `--resume` で再開でき、`--games` で目標局数を増やせます。
再開時は保存済みの手番設定を使用します。先後交代のJSONには `requested_pairs`、
固定のJSONには `requested_games` と `settings.shin_side` を保存します。
固定対局の各局には `game_number` を記録し、`summary.pairs_completed` は
`null` です。古い先後交代JSONも引き続き再開できます。

JSONの `summary` には勝敗、スコア率、先後別成績、平均手数、終局理由、
指し手の取得元が集計されます。実行中は経過時間と推定残り時間を表示します。
エンジン終了や応答待ちの失敗は `errors` に保存され、次回の再開時に同じ対局から
再試行します。

負荷や条件を変える場合は、例えば次のように指定します。

```sh
python3 tools/paired_selfplay.py --depth 10 --threads 2 --hash 256
```

通常側は比較対象として常に定跡を使います。新米長玉側は既定で定跡なしです。
新米長玉側も定跡ありにする場合は次のように指定します。

```sh
python3 tools/paired_selfplay.py --depth 10 --shin-book on
```

別の定跡ファイルを試す場合は `--book-file`、定跡を使う最大手数を変える場合は
`--book-max-ply` を指定できます。

```sh
python3 tools/paired_selfplay.py --book-file path/to/book.bin --book-max-ply 30
```

最初の後手新米長玉専用定跡は、レビュー済みの候補JSONから生成します。
主筋６局面と副枝３局面を採用し、順位が不安定な▲５八金左後の２候補は
含めません。候補JSONは根拠の記録、生成したテキストはエンジンが読む定跡です。

```sh
python3 tools/build_shin_book.py
make release
python3 test/test_shin_book.py
python3 tools/paired_selfplay.py \
  --depth 15 --threads 1 --hash 512 \
  --shin-book on \
  --shin-book-file books/shin-yonenaga-white-book.txt \
  --pairs 50
```

`--shin-book-file` は新米長玉側にだけ `ShinBookFile` を設定します。
通常側は引き続き `book.bin` を使い、専用定跡にない局面では新米長玉側は
標準定跡へ戻らず探索します。`--shin-book on` が必要です。生成ファイルは
`開始局面からのUSI手順 | 後手の定跡手` を１行ずつ記し、エンジンは手順で
再現した局面を照合します。対局JSONでは専用定跡手を `dedicated_book`、
通常側の標準定跡手を `book` と記録します。

第二版の試験用定跡は第一版に、▲７八銀 △８四歩後の▲６七銀と▲５八金左への
△２四歩だけを追加します。深さ30では両局面で首位でしたが、深さ28とは順位が
変わったため、棋力向上は未確認です。第一版の候補JSONと定跡ファイルは変更せず、
追加候補は別ファイルに記録します。次のコマンドで11局面の試験用定跡を生成し、
２局面で実際に`dedicated_book`として使われることを確認できます。

```sh
python3 tools/build_shin_book.py \
  --extension books/shin-yonenaga-white-v2-experiment.json
python3 test/test_shin_book.py
```

対局時は第一版と同じエンジン設定で、試験用定跡ファイルを明示します。

```sh
python3 tools/paired_selfplay.py \
  --depth 15 --threads 1 --hash 512 \
  --shin-book on \
  --shin-book-file books/shin-yonenaga-white-book-v2-experiment.txt \
  --pairs 50 \
  --output results/shin-dedicated-v2-vs-normal-depth15-100games.json
```

得点率は後手番50局を第一版と比較し、追加した２局面への到達数と定跡手の
使用数も確認します。第一版は`books/shin-yonenaga-white-book.txt`を指定して
同じ条件で再実行できます。

初版の終局判定は、エンジンの投了・入玉宣言と最大手数です。千日手などの厳密な
ルール判定はまだ行いません。比較時は深さ、スレッド数、ハッシュを変えずに実行します。
各局の `source_counts_by_player` を見ると、固定初手や定跡が実際に使われた回数を
プレイヤー別に確認できます。

複数の結果JSONから、先後別成績、頻出する序盤手順、序盤の評価低下候補を
Markdownにまとめるには `tools/analyze_selfplay.py` を使います。

```sh
python3 tools/analyze_selfplay.py \
  results/shin-book-off-vs-normal-depth15-100games.json \
  results/shin-book-on-vs-normal-depth15-100games.json \
  --output docs/experiments/2026-09-26-selfplay-opening-analysis.md
```

評価低下候補は、新米長玉エンジンによる評価を同じエンジンの2手後の評価と
比較します。その間に双方が1手ずつ指すため、悪手を確定する表ではありません。
深い再解析を行う局面を選ぶために使います。

選んだ局面だけを定跡なしのMultiPVで深く読むには、局面の指し手列をJSONに
保存して`tools/analyze_positions.py`へ渡します。

```sh
python3 tools/analyze_positions.py \
  docs/experiments/positions/anti-fourth-file-rook/anti-fourth-file-rook.json \
  --depth 20 \
  --multipv 3 \
  --threads 1 \
  --hash 512 \
  --output results/anti-fourth-file-rook-depth20-multipv3.json
```

結果は局面ごとに保存され、候補手、評価値、読み筋、探索深さ、ノード数、時間を
記録します。生JSONは`results/`に置き、判断に使った結果を実験レポートへ残します。
局面定義に`"searchmoves": ["7c7d"]`のような配列を加えると、指定した候補手だけを
強制探索できます。MultiPVに現れない構想の評価値を確認するときに使います。

深い探索の負荷を測るときは`--depth 40 --stop-after 900 --timeout 960`のように
指定できます。時間で停止した場合は、停止指示を送る**前**に全候補がそろっていた
最後の深さのMultiPVを保存し、結果の`stopped_early`を`true`にします。到達深さを確認してから
候補の順位を解釈してください。`candidate_bestmove`は保存した候補表の１位の手、
`bestmove`はエンジンが返したUSIの`bestmove`です。時間停止時は後者が停止後の
探索を反映し、二つの手が異なる場合があります。候補表の評価値と対応するのは
`candidate_bestmove`です。

通常側の主要応手を選ぶ場合は、新米長玉の評価補正を無効にします。

```sh
python3 tools/analyze_positions.py positions.json \
  --depth 24 --multipv 5 --shin-yonenaga-gyoku off \
  --output results/opponent-replies.json
```
