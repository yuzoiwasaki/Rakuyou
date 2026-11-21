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

## 通常版の設定

通常版は新米長玉ON・support10・D10で固定しています。この３項目は将棋所の設定画面に表示せず、古いGUI設定からOFFや0が送られても無視します。内部の評価処理は採用版と同じです。

| USI設定 | 既定値 |
| --- | --- |
| OwnBook | true |
| BookMaxPly | 44 |
| ShinBookFile | shin-yonenaga-book-v1.txt |

定跡を使うか・どの定跡を使うかは引き続き選択できます。OwnBookをOFFにしても最初の▲４八玉／△６二玉は残ります。将棋所が古い項目を表示する場合は、実行ファイルを更新したうえでエンジンを再登録してください。以前の日付付き実行ファイルにはこの変更は適用されません。

既存のGUI設定にBookMaxPly=20や32が保存されている場合は44へ変更してください。
ShinBookFileで以前の試作ファイルを指定している場合は、正式な`shin-yonenaga-book-v1.txt`へ切り替えます。

## 開発用ビルド

```sh
make development -j2
```

`bin/development` は `Rakuyou (development)` と表示され、`ShinYonenagaGyoku`、`ExperimentalSupportChainBonus`、`KingContactDeficitBonus` を公開します。既定値はON/10/10です。通常側と比較する場合はOFF/0/0にします。設定は探索前に指定し、比較には新しいプロセスを使います。

`development` は内部検査を有効にしたデバッグ用です。大量の対局には、通常版と同じ `-O3 -DNDEBUG` の比較対局用ビルドを使用します。

```sh
make match -j2
```

`bin/match` は `Rakuyou (match)` と表示され、developmentと同じ比較設定を公開します。評価・探索のロジックは変更しません。

Makefileのdevelopmentとmatchターゲットが `RAKUYOU_DEVELOPMENT_OPTIONS` を定義します。通常ビルドとはオブジェクトの保存先も分離しています。supportのUSI名は比較ツールの互換性のため維持しています。

[定跡の生成・確認](../books/README.md)と[比較対局](selfplay.md)も参照してください。

## 検証

```sh
make release development match -j2
make support-chain-test move-feature-recapture-test movepick-terminal-test -j2
python3 -m unittest discover -s test -t .
python3 tools/books/build_operational_shin_book.py --check
results/move-feature-tools/recapture-test bin/params.bin
results/move-feature-tools/terminal-test bin/params.bin
```

Pythonの実エンジン検査には `bin/release`、`bin/development`、`bin/match` と評価データが必要です。ネイティブ検査はassert有効で、全評価・差分更新・巻き戻し、取り返し、合法手のない局面を確認します。採用評価の回帰検査はsupport/Dの４設定を保存済みの基準値と照合します。

## ブランチ運用

`main` は採用済みのコードと必要な資料だけを置きます。実装前に変更内容を説明し、mainへの直接コミットか、作業ブランチとPRを使うかをユーザーと相談します。軽微な変更は、了承を得てmainへ直接コミットできます。

新機能や評価関数の変更は原則として `feature/<目的>`、`fix/<目的>`、`experiment/<目的>` 等の作業ブランチで、安定したmainと並行して開発します。PRで検証結果と差分をレビューし、ユーザーと相談して明示的な了承を得てからマージします。実装完了やテスト通過だけで自動的にマージしません。

```sh
git switch main
git switch -c feature/example
# 実装・検証・コミット後にPRを作成し、レビュー・相談・了承を経てmainへマージ
```

不採用の実験コード・レポートは実験ブランチに残し、mainへ持ち込みません。棋譜・ログ・生成物はGit管理外の `results/` へ保存します。READMEはプロジェクトの短い紹介に留めます。

過去の検証資料は、該当PRと `archive/` ブランチを参照してください。個別の退避先はPRに記載します。旧実験の再実行には、当時のソースとローカル生成物が必要です。
