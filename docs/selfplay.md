# 比較対局と局面解析

先後１局ずつの簡易対局：

```sh
make match -j2
python3 tools/analysis/paired_selfplay.py --depth 15 --threads 1 --hash 64 --pairs 1
```

比較には既定で `bin/match` を使用します。通常版と同じ最適化・内部検査無効のビルドです。`bin/development` は重い内部検査を行うため、長時間の対局には使いません。通常版は棋風が固定されているため、通常側OFFとの比較には使えません。

採用側は新米長玉ON・support10・D10、通常側は新米長玉OFF・support0・D0です。通常側は標準定跡を使い、採用側は既定で定跡OFFです。採用側にも定跡を使う場合は `--shin-book on --shin-book-file books/shin-yonenaga-book-v1.txt --book-max-ply 32` を指定します。

このツールの`--book-max-ply`は両側共通です。過去の結果と比較するときは通常側の上限も揃えてください。

このツールは固定深さの簡易確認用です。秒読み10秒の実験ランナーではありません。手数上限を引き分けとして集計し、独立した合法手・千日手判定器を備えていないため、集計をそのまま棋力の証明に使わないでください。正式な比較実験の条件や判定器は実験ブランチで準備します。

結果はGit管理外の `results/` へ保存します。終了済み対局から再開する場合：

```sh
python3 tools/analysis/paired_selfplay.py --resume results/example.json
```

再開には同じ実行ファイル・設定を使ってください。以前のバージョンの棋譜に新しい版の対局を継ぎ足さないでください。失敗した対局は再開時に再試行する仕様です。

局面解析には `tools/analysis/analyze_positions.py` を使用できます。入力形式・オプションは `--help` を参照してください。局面解析の既定は `bin/release`・新米長玉ONです。OFF/0/0を調べる場合は `--engine bin/match --shin-yonenaga-gyoku off` を指定してください。候補手の読み筋は予測であり、強制手順ではありません。
