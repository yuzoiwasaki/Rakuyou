# 実験レポート

Rakuyouの自己対局と序盤解析の記録です。

## 自己対局と序盤分析

- [新米長玉 定跡なし対通常 深さ15](2026-09-26-shin-book-off-vs-normal-depth15.md)
- [新米長玉 定跡あり対通常 深さ15](2026-09-26-shin-book-on-vs-normal-depth15.md)
- [自己対局200局の序盤分析](2026-09-26-selfplay-opening-analysis.md)
- [後手新米長玉・第一版専用定跡対通常 深さ15](2026-09-28-shin-dedicated-white-book-v1-vs-normal-depth15.md)

## 対四間飛車の重点解析

- [対先手四間飛車 重点局面解析](2026-09-26-anti-fourth-file-rook-focused-analysis.md)

## 本家系・歴史的手順

- [本家系の銀盛り上がり構想](2026-09-27-historical-line-analysis.md)

## 専用定跡候補

- [後手新米長玉・最初の専用定跡候補](2026-09-27-first-white-book-candidates.md)
- [第一版専用定跡・定跡出口の勝敗と候補手](2026-09-28-first-white-book-post-exit-analysis.md)

## オリジナル系

- [オリジナル7筋構想](2026-09-27-original-seventh-file-analysis.md)

## データの置き場所

- `positions/`: 解析する局面を定義した小さなJSON。実験系統ごとに分類してGitで管理します。
- `results/`: 解析・自己対局の生JSON。大きくなるためGit管理外に置き、重要なデータはレポートのSHA-256で識別します。
- `local/`: 歴史的棋譜など、ローカルだけで参照するデータを置きます。
