# 新米長玉と通常のRakuyouの比較対局

`tools/paired_selfplay.py` はRakuyouを2つ起動し、新米長玉をオンにした側と
オフにした通常側を対戦させます。1組ごとに先後を交代します。将棋所は使いません。

```sh
python3 tools/paired_selfplay.py --depth 5
```

強さを比較する最初の実験では、深さ15で50組（100局）を実行します。

```sh
python3 tools/paired_selfplay.py \
  --depth 15 \
  --threads 1 \
  --hash 128 \
  --shin-book off \
  --pairs 50
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
