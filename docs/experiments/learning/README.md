# 学習関連レポート

[実験レポート全体](../README.md)

[自己学習の全体レビュー：厚みの個性と棋力、次の優先順位](2026-10-14-overall-learning-review.md)

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
