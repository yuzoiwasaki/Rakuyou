# 定跡オン・オフの比較対局

`tools/paired_selfplay.py` は、Rakuyouを2つ起動し、定跡オンと定跡オフを
先後交代で2局対戦させます。将棋所は使いません。

```sh
python3 tools/paired_selfplay.py --depth 5
```

既定値では各エンジンを1スレッド、ハッシュ128 MBで動かし、結果を
`results/book-on-vs-off-日時.json` に保存します。JSONには設定、勝敗、USI形式の
指し手、指し手の取得元（固定初手・定跡・通常探索）、各手で最後に出力された
評価値と読み筋が入ります。

負荷や条件を変える場合は、例えば次のように指定します。

```sh
python3 tools/paired_selfplay.py --depth 10 --threads 2 --hash 256
```

別の定跡ファイルを試す場合は `--book-file`、定跡を使う最大手数を変える場合は
`--book-max-ply` を指定できます。

```sh
python3 tools/paired_selfplay.py --book-file path/to/book.bin --book-max-ply 30
```

初版の終局判定は、エンジンの投了・入玉宣言と最大手数です。千日手などの厳密な
ルール判定はまだ行いません。比較時は深さ、スレッド数、ハッシュを変えずに実行します。
各局の `source_counts` を見ると、定跡オン側が実際に定跡手を使ったか確認できます。
