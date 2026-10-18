# 学習関連レポート

[実験レポート全体](../README.md)

[自己学習の全体レビュー：厚みの個性と棋力、次の優先順位](2026-10-14-overall-learning-review.md)

[探索評価・勝敗・混合の同条件比較と実行手順](data/2026-10-15-hybrid-learning-plan.md)

[探索・勝敗・混合：初回結果と停止理由](data/2026-10-16-hybrid-learning-result.md)

[探索教師候補の指し手比較：計画と実行手順](data/2026-10-16-hybrid-behavior-plan.md)

[探索教師候補の指し手比較：24局面中6局面で変化](data/2026-10-17-hybrid-behavior-result.md)

[探索教師候補と現行版：８開始局面・16局の対局計画](data/2026-10-17-hybrid-match-plan.md)

[探索教師候補の16局試走：６勝８敗２分](data/2026-10-17-hybrid-match-result.md)

[負け４局の検討：打込み・大駒交換と攻防の見積り](data/2026-10-17-hybrid-match-loss-review.md)

[負け２局面の深さ15・20診断：実行手順](data/2026-10-17-hybrid-diagnostic-plan.md)

[負け２局面の診断結果：深さによる変化と次の方針](data/2026-10-17-hybrid-diagnostic-result.md)

[100cp境界の診断：上限内にも改善方向が残っていた](data/2026-10-17-constraint-direction-audit.md)

[上限内で方向を変える更新器：旧方式との比較・実行手順](data/2026-10-17-constrained-training-plan.md)

[制約内更新の初回結果：係数境界での減速と修正方針](data/2026-10-17-constrained-training-result.md)

[制約付き更新v2：係数の個別制限と局面補正・実行手順](data/2026-10-17-constrained-training-v2-plan.md)

[制約付き更新v2の結果：境界後も改善、探索教師候補を次の確認へ](data/2026-10-17-constrained-training-v2-result.md)

[探索教師v2の指し手比較：保存結果を再利用した24局面の実行手順](data/2026-10-17-projected-behavior-plan.md)

[探索教師v2の指し手比較結果：旧候補から４局面で変化](data/2026-10-17-projected-behavior-result.md)

[探索教師v2と現行版：16局対局の実行手順](data/2026-10-17-projected-match-plan.md)

[探索教師v2の16局試走：９勝５敗２未決着](data/2026-10-18-projected-match-result.md)

[探索教師v2の改善２局・悪化１局：端攻め、玉の脱出、守備駒の交換](data/2026-10-18-projected-match-review.md)

[探索教師v2：別の開始８局面による16局試走の実行手順](data/2026-10-18-alternate-match-plan.md)

[別開始局面の16局結果：７勝８敗１分と新米長玉側への偏り](data/2026-10-18-alternate-match-result.md)

[対局開始局面と運用定跡の照合：手順のずれと次の比較案](data/2026-10-18-start-book-audit.md)

[運用定跡の入口からの14局比較：計画と実行手順](data/2026-10-18-book-match-plan.md)

[運用定跡からの14局結果：６勝６敗２分](data/2026-10-18-book-match-result.md)

[定跡入口の４局検討：支えの働きと交換後の守備](data/2026-10-18-book-match-review.md)

[学習データの攻防範囲：交換と交換後の直接教師](data/2026-10-18-training-coverage.md)

[時間を離した局面追加：625局面の教師作成と実行手順](data/2026-10-18-temporal-teachers-plan.md)

[追加教師の結果：619採用・６除外と対局ごとの重み](data/2026-10-18-temporal-teachers-result.md)

[対局均等重みの学習：750局面・探索教師のみの実行手順](data/2026-10-18-temporal-training-plan.md)

[時間を離した局面追加の結果：適合は進んだが検証の改善は縮小](data/2026-10-18-temporal-training-result.md)

## 分類

| テーマ | 目次 |
| --- | --- |
| 共通の仕組み | [入力・勾配・丸め・更新器・保存](framework/README.md) |
| データ・教師 | [由来・教師生成・固定末端・集合拡大](data/README.md) |
| 手番3係数 | [手番評価の学習と探索比較](tempo/README.md) |
| 玉周囲の安全度 | [玉周囲8マス・4特徴](king-safety/README.md) |
| 金銀連結 | [厚みの入口・1特徴](gold-silver/README.md) |

## 主な実験レポート

| テーマ | 対象 | レポート |
| --- | --- | --- |
| 手番 | 序盤・中盤・終盤の3係数 | [手番の探索比較](tempo/2026-10-11-tempo-final-review-and-king-safety-proposal.md) |
| 玉周囲の安全度 | 支え・孤立・利き負け、4特徴 | [安全度の保存結果の診断](king-safety/2026-10-11-king-safety-saved-result-diagnosis.md) |
| 金銀連結 | 金・生銀の相互の利きと両端の守りの余裕 | [金銀連結の探索比較](gold-silver/2026-10-12-pair-final-search-review.md) |

金銀連結は前線の直接の支えも対象にする。厚み全体、長い連結、前進距離、攻撃成果は含まない。
共通の仕組みの動作確認と、特徴の有効性・棋力・運用採用は別の検証事項。

## 保存物

入力・探索ログ・候補・checkpoint・監査JSONはGit管理外の `results/learning-pilot/` に保存する。
保存場所・SHA・コードの版、データ件数や候補形式は各実験レポートに記録されている。

参照計画：[初回手番](../configs/tempo-pilot-v1.json)、
[新教師の手番](../configs/refreshed-tempo-pilot-v1.json)、[教師更新](../configs/teacher-refresh-v1.json)。
ビルド・実行方法は [開発手順](../../development.md) を参照。
