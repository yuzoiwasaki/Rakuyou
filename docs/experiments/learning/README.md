# 学習関連レポート

[実験レポート全体](../README.md)

## 分類

| テーマ | 目次 |
| --- | --- |
| 共通の仕組み | [入力・勾配・丸め・更新器・保存](framework/README.md) |
| データ・教師 | [由来・教師生成・固定末端・集合拡大](data/README.md) |
| 手番3係数 | [手番評価の学習と探索比較](tempo/README.md) |
| 玉周囲の安全度 | [玉周囲8マス・4特徴](king-safety/README.md) |
| 金銀連結 | [厚みの入口・1特徴](gold-silver/README.md) |

## 実験の結論

| テーマ | 対象 | 結論・最終レポート |
| --- | --- | --- |
| 手番 | 序盤・中盤・終盤の3係数 | [現行評価維持](tempo/2026-10-11-tempo-final-review-and-king-safety-proposal.md) |
| 玉周囲の安全度 | 支え・孤立・利き負け、4特徴 | [基準維持と保存結果の診断](king-safety/2026-10-11-king-safety-saved-result-diagnosis.md) |
| 金銀連結 | 金・生銀の相互の利きと両端の守りの余裕 | [最終探索確認・採用保留](gold-silver/2026-10-12-pair-final-search-review.md) |

金銀連結は前線の直接の支えも対象にする。厚み全体、長い連結、前進距離、攻撃成果は含まない。
共通の仕組みの動作確認と、特徴の有効性・棋力・運用採用は別の検証事項。

## データと保存形式

- 初回手番実験は学習64／検証64件。現行基準の新教師を使った手番・玉安全度・初回金銀連結は36／18件。
- 金銀連結の拡大集合は有効143／35件。新検証は既存検証run内の未使用対局。
- 教師は探索cp。手数上限drawは正式裁定済みdrawとは区別し、勝敗損失は無効。
- 手番・玉安全度の候補は別名params、金銀連結の候補は実験用2係数sidecar。
  金銀連結sidecarは通常releaseの読込形式ではない。
- 入力・探索ログ・候補・checkpoint・監査JSONはGit管理外の `results/learning-pilot/`。
  保存場所・SHA・コードの版は各レポートに記録されている。

参照計画：[初回手番](../configs/tempo-pilot-v1.json)、
[新教師の手番](../configs/refreshed-tempo-pilot-v1.json)、[教師更新](../configs/teacher-refresh-v1.json)。
ビルド・実行方法は [開発手順](../../development.md) を参照。
