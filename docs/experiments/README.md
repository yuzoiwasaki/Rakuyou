# 実験レポート

Rakuyouの自己対局と序盤解析の記録です。

## 現在地

- 後手第一運用版はv2の既存11局面。[定跡一覧・使い方](../../books/README.md)
  に運用／比較用／保留を整理しています。過去の実験は削除していません。
- [後手の一区切り：200局比較・７局確認・v2採用判断](2026-10-03-v2-bounded-white-improvement-cycle.md)
- [次の段階：先手300局の入口集計と先手定跡の着手方針](2026-10-03-black-book-start-plan.md)
- [先手300局の監査・15局面探索と７局面試験定跡](2026-10-03-black-300-game-branch-review.md)

## 後手版の主要検証

- [４パターン・後手固定400局とhighレビュー](2026-10-02-fixed-white-four-books-depth15.md)
- [端歩待機と７筋構想の重点解析](2026-10-02-edge-wait-seventh-file-analysis.md)
- [早い△７二銀と７筋試験定跡の準備](2026-10-02-early-silver72-and-seventh-trial.md)
- [７筋試験定跡100局と追加検証：運用採用は見送り](2026-10-02-seventh-edge-white-only-depth15.md)

## 自己対局と序盤分析

- [新米長玉 定跡なし対通常 深さ15](2026-09-26-shin-book-off-vs-normal-depth15.md)
- [新米長玉 定跡あり対通常 深さ15](2026-09-26-shin-book-on-vs-normal-depth15.md)
- [自己対局200局の序盤分析](2026-09-26-selfplay-opening-analysis.md)
- [後手新米長玉・第一版専用定跡対通常 深さ15](2026-09-28-shin-dedicated-white-book-v1-vs-normal-depth15.md)
- [後手新米長玉・第一版専用定跡の100局再試行](2026-09-29-shin-dedicated-white-book-v1-repeat-vs-normal-depth15.md)
- [後手新米長玉・第二版試験定跡対通常 深さ15](2026-09-28-shin-dedicated-white-book-v2-vs-normal-depth15.md)
- [後手新米長玉・第二版試験定跡の100局再試行](2026-09-29-shin-dedicated-white-book-v2-repeat-vs-normal-depth15.md)

## 対四間飛車の重点解析

- [対先手四間飛車 重点局面解析](2026-09-26-anti-fourth-file-rook-focused-analysis.md)

## 本家系・歴史的手順

- [本家系の銀盛り上がり構想](2026-09-27-historical-line-analysis.md)

## 専用定跡候補

- [後手v2の一区切りに向けた頻出局面の選別と試験版](2026-10-03-v2-bounded-white-improvement-cycle.md)
- [Astraによる後手新米長玉定跡の独立レビュー（今後の検証方針）](2026-10-03-astra-white-book-independent-review.md)
- [後手新米長玉・最初の専用定跡候補](2026-09-27-first-white-book-candidates.md)
- [第一版専用定跡・定跡出口の勝敗と候補手](2026-09-28-first-white-book-post-exit-analysis.md)
- [第一版専用定跡・頻出合流局面の全候補再解析](2026-09-28-first-white-book-post-exit-depth28-30.md)
- [第二版専用定跡・頻出出口の勝敗と直接解析](2026-09-29-shin-dedicated-white-book-v2-post-exit-followup.md)
- [第二版専用定跡・２試行の分岐整理と重点局面解析](2026-09-29-shin-dedicated-white-book-v2-two-run-branch-review.md)

## オリジナル系

- [オリジナル7筋構想](2026-09-27-original-seventh-file-analysis.md)
- [△７四歩～△７三銀案の標準定跡到達性](2026-09-28-original-seventh-standard-book-recheck.md)

## データの置き場所

- `positions/`: 解析する局面を定義した小さなJSON。実験系統ごとに分類してGitで管理します。
- `results/`: 解析・自己対局の生JSON。大きくなるためGit管理外に置き、重要なデータはレポートのSHA-256で識別します。
- `local/`: 歴史的棋譜など、ローカルだけで参照するデータを置きます。
