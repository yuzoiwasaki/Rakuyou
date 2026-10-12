# 開発手順

## ビルド

技巧は SSE 4.2 前提のため、Apple Silicon では x86_64 (Rosetta) でビルドします。
初回は `brew install cmake` で CMake を用意し、OpenMP ランタイムをビルドします。

```sh
make libomp-x86_64
make release
```

実行ファイルは `bin/release` です。評価データがない場合は、[技巧の Releases](https://github.com/gikou-official/Gikou/releases)
から Windows 版 zip を取得し、`params.bin` など必要なデータを `bin/` に置きます。`gikou.exe` は使いません。

## ツールとテスト

[tools/](../tools/) は定跡・解析・学習に、[test/](../test/) は対応するテストに分類しています。
Python テストはリポジトリのルートから実行します。

```sh
python3 -m unittest discover -s test -t .
```

一部のツールやテストは、`bin/` の評価データ、個別にビルドするprobe、または
Git管理外の `results/` 内データを参照します。学習用probeは通常エンジンとは別の
実行ファイルとして `results/` に出力されます。

## 学習データ

学習ツールは `tools/learning/` にあります。入力・教師・特徴・更新方法ごとの説明と
実験結果は[学習レポートの目次](experiments/learning/README.md)を参照してください。
個別の実験手順や設定は対応するレポートに記録します。

学習用の棋譜、評価データ、候補、checkpoint、監査結果は `results/` に保存します。
入力と重要な出力のSHA-256を記録し、既存ファイルを上書きしない新しい出力先を使います。
`bin/` の現行評価データは実験出力先にせず、元データは別のバックアップを確認するまで
削除しません。通常の Gikou `--learn` は評価パラメータを再初期化します。学習方式や
実験設定の詳細は[学習レポートの目次](experiments/learning/README.md)から確認してください。
