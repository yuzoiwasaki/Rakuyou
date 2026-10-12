# 実験レポート

Rakuyouの自己対局・序盤解析・学習実験の記録です。

## テーマ別の入口

| テーマ | 目次 |
| --- | --- |
| 学習全体 | [学習レポート](learning/README.md) |
| 学習の仕組み | [入力・勾配・丸め・更新器・保存](learning/framework/README.md) |
| 学習データ・教師 | [由来・教師生成・集合拡大](learning/data/README.md) |
| 手番の学習 | [手番3係数](learning/tempo/README.md) |
| 玉の安全度 | [玉周囲8マス・4特徴](learning/king-safety/README.md) |
| 金銀連結 | [厚みの入口・最終確認](learning/gold-silver/README.md) |
| 先手定跡 | [先手の検討・比較・判断](books/black/README.md) |
| 後手定跡 | [後手の検討・比較・判断](books/white/README.md) |
| 自己対局 | [対局比較・序盤集計](selfplay/README.md) |
| 構想・重点解析 | [本家系・7筋構想・対四間飛車](openings/README.md) |

設定JSONは `configs/`、局面JSONは [positions/](positions/README.md)、
棋譜・探索結果の生データはGit管理外の `results/` に保存しています。

## 定跡の資料

- [定跡一覧・使い方](../../books/README.md)
- [先手の独立レビューと採用判断](books/black/2026-10-10-black-book-independent-review.md)
- [後手v2の比較結果と採用判断](books/white/2026-10-03-v2-bounded-white-improvement-cycle.md)

## 後手版の主要検証

- [４パターン・後手固定400局とhighレビュー](books/white/2026-10-02-fixed-white-four-books-depth15.md)
- [端歩待機と７筋構想の重点解析](books/white/2026-10-02-edge-wait-seventh-file-analysis.md)
- [早い△７二銀と７筋試験定跡の準備](books/white/2026-10-02-early-silver72-and-seventh-trial.md)
- [７筋試験定跡100局と追加検証：運用採用は見送り](books/white/2026-10-02-seventh-edge-white-only-depth15.md)

## 自己対局と序盤分析

- [新米長玉 定跡なし対通常 深さ15](selfplay/2026-09-26-shin-book-off-vs-normal-depth15.md)
- [新米長玉 定跡あり対通常 深さ15](selfplay/2026-09-26-shin-book-on-vs-normal-depth15.md)
- [自己対局200局の序盤分析](selfplay/2026-09-26-selfplay-opening-analysis.md)
- [後手新米長玉・第一版専用定跡対通常 深さ15](selfplay/2026-09-28-shin-dedicated-white-book-v1-vs-normal-depth15.md)
- [後手新米長玉・第一版専用定跡の100局再試行](selfplay/2026-09-29-shin-dedicated-white-book-v1-repeat-vs-normal-depth15.md)
- [後手新米長玉・第二版試験定跡対通常 深さ15](selfplay/2026-09-28-shin-dedicated-white-book-v2-vs-normal-depth15.md)
- [後手新米長玉・第二版試験定跡の100局再試行](selfplay/2026-09-29-shin-dedicated-white-book-v2-repeat-vs-normal-depth15.md)

## 対四間飛車の重点解析

- [対先手四間飛車 重点局面解析](openings/2026-09-26-anti-fourth-file-rook-focused-analysis.md)

## 本家系・歴史的手順

- [本家系の銀盛り上がり構想](openings/2026-09-27-historical-line-analysis.md)

## 専用定跡候補

- [後手v2の一区切りに向けた頻出局面の選別と試験版](books/white/2026-10-03-v2-bounded-white-improvement-cycle.md)
- [Astraによる後手新米長玉定跡の独立レビュー（今後の検証方針）](books/white/2026-10-03-astra-white-book-independent-review.md)
- [後手新米長玉・最初の専用定跡候補](books/white/2026-09-27-first-white-book-candidates.md)
- [第一版専用定跡・定跡出口の勝敗と候補手](books/white/2026-09-28-first-white-book-post-exit-analysis.md)
- [第一版専用定跡・頻出合流局面の全候補再解析](books/white/2026-09-28-first-white-book-post-exit-depth28-30.md)
- [第二版専用定跡・頻出出口の勝敗と直接解析](books/white/2026-09-29-shin-dedicated-white-book-v2-post-exit-followup.md)
- [第二版専用定跡・２試行の分岐整理と重点局面解析](books/white/2026-09-29-shin-dedicated-white-book-v2-two-run-branch-review.md)

## オリジナル系

- [オリジナル7筋構想](openings/2026-09-27-original-seventh-file-analysis.md)
- [△７四歩～△７三銀案の標準定跡到達性](openings/2026-09-28-original-seventh-standard-book-recheck.md)

## データの置き場所

- `positions/`: 解析する局面を定義した小さなJSON。実験系統ごとに分類してGitで管理します。
- `results/`: 解析・自己対局の生JSON。大きくなるためGit管理外に置き、重要なデータはレポートのSHA-256で識別します。
- `local/`: 歴史的棋譜など、ローカルだけで参照するデータを置きます。
