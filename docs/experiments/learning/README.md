# 学習関連レポート

2026年10月12日時点の案内。共通の仕組み・データと、特徴ごとの実験をまとめる。
各実験は **結論・最終確認 → 学習結果 → 計画・準備** の順に読む。
元レポートは各段階の記録であり、「未実施」「次に行う」などの記述はその執筆時点の状態を表す。
現在の判断は下の一覧と各実験の最終レポートを参照する。

[実験レポート全体へ戻る](../README.md)

## 現在の判断

学習・探索の動作確認と、特徴の有効性・棋力・運用採用の判断を区別する。
共通の仕組みを検証できたことだけでは、評価特徴を採用する根拠にはならない。
全実験を一区切りとし、現行評価・定跡・25cp補正を維持している。
保存候補は保持するが、追加学習・調整・探索・対局を自動的に再開しない。

| テーマ | 試したもの | 現在の判断 | まず読むレポート |
| --- | --- | --- | --- |
| 手番 | 序盤・中盤・終盤の3係数 | 実験終了、現行評価維持 | [最終探索比較と終了判断](tempo/2026-10-11-tempo-final-review-and-king-safety-proposal.md) |
| 玉周囲の安全度 | 玉周囲8マスの支え・孤立・利き負け、4特徴 | 基準候補を維持、追加調整は保留 | [保存結果からの診断](king-safety/2026-10-11-king-safety-saved-result-diagnosis.md) |
| 金銀連結／厚みの入口 | 金・生銀が相互に利き、両端に守りの余裕があるペア数 | 最終確認まで終了、採用保留 | [再静止探索35局面・通常探索6局面](gold-silver/2026-10-12-pair-final-search-review.md) |

金銀連結は前線の直接の支えも対象にするが、厚み全体・長い連結・前進や攻撃成果を
まとめて学習したものではない。特徴の範囲は金銀連結の動機・計画レポートに記録している。

## 共通の学習の仕組み

[このテーマの全レポート](framework/README.md)

基準評価を保持したまま小さな差分を学習し、入力・数値計算・保存・再読込を検証した記録。
勾配・丸め・更新器の初期検証は手番3係数を使っている。別特徴への接続確認は各実験を参照。

| 調べたいこと | レポート |
| --- | --- |
| 技巧2の学習実装・形式、現行パラメータから始める方式 | [追加学習の実装調査・実験案](framework/2026-10-11-learning-feasibility-plan.md) |
| 元棋譜との照合・入力reader・ゼロ差分 | [1,536局面の入力検証](framework/2026-10-11-learning-input-validation.md) |
| 損失・符号・進行度・解析勾配 | [手番3係数の数値勾配検証](framework/2026-10-11-tempo-gradient-validation.md) |
| エンジンの整数丸めと微小な評価差 | [20,480評価の丸め照合](framework/2026-10-11-tempo-rounding-validation.md) |
| 固定静止探索末端と教師の接続 | [64局面の末端・符号・進行度検証](framework/2026-10-11-qsearch-leaf-validation.md) |
| 更新幅・係数・回数上限、状態・乱数の保存 | [更新器の合成検証](framework/2026-10-11-tempo-updater-validation.md) |
| 別名候補paramsの保存・再読込 | [候補出力とvalidation末端準備](framework/2026-10-11-candidate-export-validation.md) |
| 実行制御・バックアップ・更新0確認 | [runnerのdry-runと61ファイルの保存確認](framework/2026-10-11-tempo-pilot-dry-run.md) |
| 初回実学習直前までの到達点 | [学習準備のまとめ](framework/2026-10-11-learning-checkpoint-summary.md) |

候補の保存方式は特徴によって異なる。手番・玉安全度では別名params、金銀連結では
実験用2係数sidecarを使用した。金銀連結sidecarを通常releaseが直接読むという意味ではない。
ビルド・ツールの説明は[開発手順](../../development.md)、実行時の根拠・SHAは各レポートにある。

## データ・教師

[このテーマの全レポート](data/README.md)

元の暫定集合、現行基準による教師生成、集合拡大を辿るための記録。
件数は段階ごとに異なるため、対象の実験と生成・準備レポートを合わせて読む。

| 段階 | レポートと到達点 |
| --- | --- |
| 既存棋譜・探索データの由来 | [47runのSHA照合と歴史的評価データの制約](data/2026-10-11-learning-provenance-review.md) |
| 現行基準の教師36／18件の設計 | [教師更新の計画・54局面選択](data/2026-10-11-teacher-refresh-plan.md) |
| 教師生成の接続確認 | [探索0 dry-run](data/2026-10-11-teacher-refresh-dry-run.md) |
| 現行基準の教師生成・監査 | [54件受入、由来・コマンド・PVの監査](data/2026-10-11-teacher-refresh-generation.md) |
| 教師36／18件の固定末端・ゼロ更新準備 | [新教師reader・54末端・更新0検証](data/2026-10-11-refreshed-pilot-preparation.md) |
| 金銀連結用144／新検証36件への拡大 | [対象選択・静的準備](data/2026-10-12-pair-data-expansion-preparation.md) |
| 拡大集合の教師・末端の確定 | [有効143／35件、反復PV2件除外・補充なし](data/2026-10-12-pair-expanded-teachers-and-leaves.md) |

勝敗・draw層は保持する。手数上限drawを勝ちや正式裁定済みdrawには置き換えず、
勝敗損失は無効にして探索cpを使った。現行基準による教師生成も同じエンジンの自己蒸留であり、
教師の独立性や棋力向上を保証しない。新検証35件は既存検証run内の未使用対局である。

## 手番3係数の実験

[このテーマの全レポート](tempo/README.md)

最初の64／64件と、現行基準の新教師36／18件での実験を区別する。
両方とも20更新で終了し、選択した候補を運用には採用していない。

| 読む順 | 新教師36／18件の実験 |
| --- | --- |
| 結論・最終確認 | [再静止探索・通常探索の比較と実験終了](tempo/2026-10-11-tempo-final-review-and-king-safety-proposal.md) |
| 学習結果 | [20更新の候補選択・先後とdrawの観察](tempo/2026-10-11-refreshed-tempo-pilot-result.md) |
| 計画・接続 | [専用runner・更新0検証](tempo/2026-10-11-refreshed-runner-validation.md) |

初回64／64件の経緯は次の順で読む。

1. [初回パイロットの終了・候補側の再現確認](tempo/2026-10-11-tempo-pilot-closure.md)
2. [通常探索12局面・24検索の結果](tempo/2026-10-11-tempo-full-search-comparison.md)
3. [再静止探索validation32／test32の観察](tempo/2026-10-11-selected-tempo-qsearch-review.md)
4. [初回20更新の学習結果](tempo/2026-10-11-first-tempo-learning-pilot.md)
5. [基準評価の再現性確認](tempo/2026-10-11-tempo-baseline-repeatability.md)
6. [通常探索比較の対象・隔離環境の準備](tempo/2026-10-11-tempo-full-search-preparation.md)

## 玉周囲8マスの安全度4特徴

[このテーマの全レポート](king-safety/README.md)

守られた金・守られた銀・孤立した金銀・隣接マスの利き負けを、序盤／終盤8係数で試した。
全体の金銀連結や2段目の厚みは含めていない。

| 読む順 | レポート |
| --- | --- |
| 結論・理由 | [丸めと弱い残差信号、正則化の影響の診断](king-safety/2026-10-11-king-safety-saved-result-diagnosis.md) |
| 学習結果 | [4特徴・20更新、整数評価改善なし・基準維持](king-safety/2026-10-11-king-safety-first-pilot-result.md) |
| 動機・計画 | [小規模学習案と、金銀の厚みにどうつなぐか](king-safety/2026-10-11-king-safety-small-learning-plan.md) |

保存結果だけで診断し、この4特徴のL2変更や追加学習は実施していない。

## 金銀連結／厚みの入口

[このテーマの全レポート](gold-silver/README.md)

盤全体で、金と生銀が互いに利き、両端の玉を除く味方利き数が敵より多いペアを1回数える。
1特徴・序盤／終盤2係数。加点を強制せず、符号も学習に任せた。

| 読む順 | レポート |
| --- | --- |
| 結論・最終確認 | [選択5更新候補だけの再静止探索35局面・通常探索6局面、採用保留](gold-silver/2026-10-12-pair-final-search-review.md) |
| 拡大学習の結果 | [143／35件・20更新、全体と先後・draw層の監査](gold-silver/2026-10-12-expanded-pair-learning-result.md) |
| 初回学習の結果 | [36／18件で出現数・L2を確認した20更新](gold-silver/2026-10-12-gold-silver-pair-first-pilot.md) |
| 特徴の動機・定義 | [3局4区間で比較した、実際の支えと見た目の厚みの違い](gold-silver/2026-10-12-gold-silver-functional-example-review.md) |
| 拡大集合の準備 | [144／新検証36局面の選択](data/2026-10-12-pair-data-expansion-preparation.md)、[教師・末端143／35件の監査](data/2026-10-12-pair-expanded-teachers-and-leaves.md) |

初回では実験内で10更新候補、拡大集合では5更新候補を選択した。最終探索確認は後者だけ。
固定末端の微改善と、通常探索の最善手・PV・評価の変化を区別し、採用保留で終了した。

## 記録と保存物の見方

- この目次と各レポートはGit管理対象。元レポートの名前を維持し、テーマ別ディレクトリへ移動している。
- 詳細な入力、探索ログ、候補、checkpoint、監査JSONはGit管理外の `results/learning-pilot/`。
  対応する場所とSHAは各レポートを参照する。
- 参照計画は [初回手番](../configs/tempo-pilot-v1.json)、[新教師の手番](../configs/refreshed-tempo-pilot-v1.json)、
  [教師更新](../configs/teacher-refresh-v1.json)。終了済み実験の再実行指示ではない。
- 通常の開発を再開するときはリポジトリの `MEMORY.md` を読む。
  詳細な経緯はこの目次から辿り、終了済み実験のマーカーを解除しない。
