# 開発手順

## ビルドと起動

Apple Siliconではx86_64（Rosetta）でビルドします。初回はCMakeを用意してOpenMPランタイムをビルドします。

```sh
make libomp-x86_64
make release -j2
```

実行ファイルは `bin/release` です。`params.bin`、`progress.bin`、`probability.bin`、`book.bin` を `bin/` に配置してください。データは[技巧の配布物](https://github.com/gikou-official/Gikou/releases)から取得できます。評価データはGit管理しません。

```sh
tools/run-engine.sh
```

GUIにも `tools/run-engine.sh` を登録できます。起動ディレクトリを `bin/` に揃えるためのランチャーです。ビルド時に専用定跡も `bin/` へコピーします。

## 設定

新米長玉とsupport10・D10は通常ビルドに統合済みです。日付付きパッチを別途適用する必要はありません。

| USI設定 | 既定値 |
| --- | --- |
| ShinYonenagaGyoku | true |
| ExperimentalSupportChainBonus | 10 |
| KingContactDeficitBonus | 10 |
| OwnBook | true |
| BookMaxPly | 20 |
| ShinBookFile | shin-yonenaga-book-v1.txt |

supportは歩と金銀の支持関係、Dは玉周辺の敵の利き超過に関する評価項です。supportのUSI名は既存GUI設定との互換性のため維持しています。通常側と比較する場合は新米長玉OFFに加えてsupportとDを両方0にしてください。GUIに保存された旧設定は自動更新されないため、採用版では10/10を確認してください。設定は探索前に指定し、比較には新しいプロセスを使います。

[定跡の生成・確認](../books/README.md)と[比較対局](selfplay.md)も参照してください。

## 検証

```sh
make support-chain-test move-feature-recapture-test movepick-terminal-test -j2
python3 -m unittest discover -s test -t .
python3 tools/books/build_operational_shin_book.py --check
results/move-feature-tools/recapture-test bin/params.bin
results/move-feature-tools/terminal-test bin/params.bin
```

Pythonの実エンジン検査には `bin/release` と評価データが必要です。ネイティブ検査はassert有効で、全評価・差分更新・巻き戻し、取り返し、合法手のない局面を確認します。採用評価の回帰検査はsupport/Dの４設定を保存済みの基準値と照合します。

## ブランチ運用

`main` は採用済みのコードと必要な資料だけを置きます。変更前に `feature/<目的>`、`fix/<目的>`、`experiment/<目的>` 等の作業ブランチを作り、検証した変更だけをレビューしてマージします。

```sh
git switch main
git switch -c feature/example
# 実装・検証・コミット後、差分をレビューしてmainへマージ
```

不採用の実験コード・レポートは実験ブランチに残し、mainへ持ち込みません。棋譜・ログ・生成物はGit管理外の `results/` へ保存します。READMEはプロジェクトの短い紹介に留めます。

整理前の実験資料は `archive/pre-adoption-cleanup-2026-11-15`（`f488a64`）にあります。必要なら別worktreeで参照できます。旧実験は当時のソース・ローカル生成物を前提にしており、新mainでそのまま再実行するものではありません。履歴の書き換えはしていません。
