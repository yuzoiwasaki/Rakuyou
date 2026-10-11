# 実験レポート

Rakuyouの自己対局と序盤解析の記録です。

## 現在地

- [新教師での手番学習：36／18件・20更新、候補選択・運用は基準維持](2026-10-11-refreshed-tempo-pilot-result.md)

- [新教師36／18件の学習runnerと更新0検証：計画固定・実学習は無効](2026-10-11-refreshed-runner-validation.md)

- [新教師の接続・54固定末端・更新0dry-run：再学習は未実施](2026-10-11-refreshed-pilot-preparation.md)

- [由来を固定した教師生成と監査：54局面すべて受入、学習は未実施](2026-10-11-teacher-refresh-generation.md)

- [教師生成runnerと探索0 dry-run：54局面・SHA／保存検証、実探索は未実施](2026-10-11-teacher-refresh-dry-run.md)

- [教師更新の設計と54局面準備：由来・条件固定、探索と学習は未実施](2026-10-11-teacher-refresh-plan.md)

- [初回学習パイロットの一区切り：候補側も再現、運用は基準維持、次の課題](2026-10-11-tempo-pilot-closure.md)

- [基準評価の再現性確認：3局面・6検索、cp／選択手／PV／nodes一致](2026-10-11-tempo-baseline-repeatability.md)

- [通常探索比較の結果：12局面・24探索、選択手2局面で変化、採用保留](2026-10-11-tempo-full-search-comparison.md)

- [通常探索比較の準備：分離した基準・候補環境と固定12局面、探索未実施](2026-10-11-tempo-full-search-preparation.md)

- [選定済み候補の再静止探索：validation32・test32、PV不変・運用据え置き](2026-10-11-selected-tempo-qsearch-review.md)
- [初回学習：手番3係数・64局面・20更新の結果（運用は据え置き）](2026-10-11-first-tempo-learning-pilot.md)
- [学習準備の現在地・最初の20更新実験と懸念点](2026-10-11-learning-checkpoint-summary.md)
- [既存棋譜・探索データを使う追加学習：実装調査と小規模実験案](2026-10-11-learning-feasibility-plan.md)
  （更新なしのデータ準備まで。学習・現行データ上書きは未実施）
- [学習候補の由来確認：47runの保存SHA照合と過去評価データの制約](2026-10-11-learning-provenance-review.md)
- [更新なしの入力reader：1,536局面の照合・固定ベースとゼロ差分検証](2026-10-11-learning-input-validation.md)
- [手番3係数：損失・符号・進行度と解析勾配の数値検証](2026-10-11-tempo-gradient-validation.md)
- [実エンジンの整数丸め：メモリ上の手番摂動と20,480評価の照合](2026-10-11-tempo-rounding-validation.md)
- [静止探索の固定末端：64局面の符号・評価・進行度・勾配の接続検証](2026-10-11-qsearch-leaf-validation.md)
- [手番更新器の合成検証と64局面・最大20更新のパイロット案](2026-10-11-tempo-updater-validation.md)
- [別名候補paramsの保存・再読込とvalidation64件の固定末端準備](2026-10-11-candidate-export-validation.md)
- [実験runnerの更新0 dry-runと61ファイルのローカルバックアップ](2026-10-11-tempo-pilot-dry-run.md)
- 後手第一運用版はv2の既存11局面。[定跡一覧・使い方](../../books/README.md)
  に運用／比較用／保留を整理しています。過去の実験は削除していません。
- [後手の一区切り：200局比較・７局確認・v2採用判断](2026-10-03-v2-bounded-white-improvement-cycle.md)
- [次の段階：先手300局の入口集計と先手定跡の着手方針](2026-10-03-black-book-start-plan.md)
- [先手300局の監査・試験定跡300局比較・銀先行探索と４局面試験版](2026-10-03-black-300-game-branch-review.md)
- [先手定跡の独立レビュー：1,200局再集計・暫定運用提案と▲７六歩型の再検討](2026-10-10-black-book-independent-review.md)

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
