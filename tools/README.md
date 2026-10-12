# 開発ツール

43個のPythonファイルと3個のnative補助ソースを、用途別ディレクトリに配置した。
[開発手順](../docs/development.md)／[テスト案内](../test/README.md)／
[学習レポート](../docs/experiments/learning/README.md)

## ディレクトリ

- `books/`：定跡の生成・確認
- `analysis/`：局面解析・対局・既存棋譜の集計
- `learning/core/`：目的関数・更新器・候補保存・バックアップ
- `learning/data/`：データ準備・教師生成・監査・固定末端接続
- `learning/checks/`：勾配・丸め・更新器・末端の確認
- `learning/tempo/`：手番3係数の実験
- `learning/king_safety/`：玉周囲4特徴の実験
- `learning/gold_silver/`：金銀連結の実験・最終確認
- `learning/native/`：native probeと特徴補助ソース

Pythonの実行はファイルパスでも、`python3 -m tools.books.build_operational_shin_book --check`
のようなパッケージ名でも指定できる。

## 普段の定跡・解析に使うもの

| 用途 | ツール |
| --- | --- |
| 現行の共通17局面の生成・確認 | [build_operational_shin_book.py](books/build_operational_shin_book.py) |
| 個別定跡・保留候補・旧定跡の生成 | [build_shin_book.py](books/build_shin_book.py) |
| 指定局面の通常探索 | [analyze_positions.py](analysis/analyze_positions.py) |
| 対局・着手と探索結果の記録 | [paired_selfplay.py](analysis/paired_selfplay.py) |
| 既存棋譜の序盤集計 | [analyze_selfplay.py](analysis/analyze_selfplay.py) |
| 先手の保存済み対局の監査・分岐集計 | [review_black_runs.py](analysis/review_black_runs.py) |
| 後手の保存済み対局の監査・集計 | [review_white_runs.py](analysis/review_white_runs.py) |
| 後手v2の局面別集計の再現 | [review_v2_white_cycle.py](analysis/review_v2_white_cycle.py) |
| 駒配置・反復・序盤構造の照合 | [audit_white_positions.py](analysis/audit_white_positions.py) |

通常の書込みなし確認は、リポジトリ直下で次を使う。

```sh
python3 tools/books/build_operational_shin_book.py --check
```

定跡の対象・生成元は [books/README.md](../books/README.md) を参照。
解析・対局ツールの掲載は新しい実験の実行予定を示すものではない。

## 共通の学習部品・確認用ツール

これらは複数の実験からimportされる部品や、数値・保存の確認に使った入口。
一度きりの確認に見えるファイルでも、テストや後の処理から使用されている。

| 分類 | ファイル |
| --- | --- |
| 既存データの準備・由来・入力照合 | [prepare_learning_data.py](learning/data/prepare_learning_data.py)、[audit_learning_provenance.py](learning/data/audit_learning_provenance.py)、[validate_learning_input.py](learning/data/validate_learning_input.py) |
| 教師54件の選択・生成・監査 | [prepare_teacher_refresh.py](learning/data/prepare_teacher_refresh.py)、[refresh_teachers.py](learning/data/refresh_teachers.py)、[audit_refreshed_teachers.py](learning/data/audit_refreshed_teachers.py) |
| 教師54件の固定末端接続 | [prepare_refreshed_pilot.py](learning/data/prepare_refreshed_pilot.py) |
| 拡大集合180件の選択・教師・末端 | [prepare_pair_expansion.py](learning/data/prepare_pair_expansion.py)、[pair_teacher_generation.py](learning/data/pair_teacher_generation.py)、[prepare_pair_leaves.py](learning/data/prepare_pair_leaves.py) |
| 独立コピー・SHA・バックアップ検証 | [learning_backup.py](learning/core/learning_backup.py) |
| 手番の目的関数・更新器・別名候補出力 | [tempo_objective.py](learning/core/tempo_objective.py)、[tempo_updater.py](learning/core/tempo_updater.py)、[tempo_export.py](learning/core/tempo_export.py) |
| 8座標の目的関数・更新器、安全度テーブル出力 | [king_safety_objective.py](learning/core/king_safety_objective.py)、[king_safety_updater.py](learning/core/king_safety_updater.py)、[king_safety_export.py](learning/core/king_safety_export.py) |
| 固定静止探索末端の確認 | [check_qsearch_leaves.py](learning/checks/check_qsearch_leaves.py) |
| 手番の勾配・丸め・更新器・候補保存の確認 | [check_tempo_gradient.py](learning/checks/check_tempo_gradient.py)、[check_tempo_rounding.py](learning/checks/check_tempo_rounding.py)、[check_tempo_updater.py](learning/checks/check_tempo_updater.py)、[check_tempo_export.py](learning/checks/check_tempo_export.py) |

8座標の目的関数・更新器は金銀連結でも最初の2座標を使っている。
`check_tempo_updater.py` の合成チェックは `test_tempo_updater.py` からも呼ばれる。
`check_tempo_gradient.py` はPythonのimport元がなくても、初期の実データ勾配検証の記録を再現する入口。
単純な重複や未使用コードとしては削除しない。

## 終了済み実験の処理

データ件数・SHA・候補・実行回数を固定した処理。共通部品への参照も含むため、
古い版を消して新しい版だけに統一してはいない。
以下の実験はすべて終了しており、学習・候補選択・追加探索は再開しない。

| 実験 | ファイル | 結論 |
| --- | --- | --- |
| 初回手番64／64件 | [tempo_pilot.py](learning/tempo/tempo_pilot.py) | [初回の終了](../docs/experiments/learning/tempo/2026-10-11-tempo-pilot-closure.md) |
| 新教師の手番36／18件 | [refreshed_tempo_pilot.py](learning/tempo/refreshed_tempo_pilot.py) | [学習結果](../docs/experiments/learning/tempo/2026-10-11-refreshed-tempo-pilot-result.md) |
| 手番候補の探索・再現性確認 | [check_selected_qsearch.py](learning/tempo/check_selected_qsearch.py)、[prepare_tempo_search.py](learning/tempo/prepare_tempo_search.py)、[run_tempo_search.py](learning/tempo/run_tempo_search.py)、[check_tempo_search_repeatability.py](learning/tempo/check_tempo_search_repeatability.py)、[close_refreshed_tempo_search.py](learning/tempo/close_refreshed_tempo_search.py) | [最終確認・終了](../docs/experiments/learning/tempo/2026-10-11-tempo-final-review-and-king-safety-proposal.md) |
| 玉周囲の安全度4特徴 | [king_safety_pilot.py](learning/king_safety/king_safety_pilot.py) | [結果と基準維持](../docs/experiments/learning/king-safety/2026-10-11-king-safety-first-pilot-result.md) |
| 金銀連結36／18件 | [gold_silver_pair_pilot.py](learning/gold_silver/gold_silver_pair_pilot.py) | [初回結果](../docs/experiments/learning/gold-silver/2026-10-12-gold-silver-pair-first-pilot.md) |
| 金銀連結143／35件 | [expanded_pair_pilot.py](learning/gold_silver/expanded_pair_pilot.py) | [拡大学習結果](../docs/experiments/learning/gold-silver/2026-10-12-expanded-pair-learning-result.md) |
| 金銀連結の最終探索確認 | [build_pair_final_search.py](learning/gold_silver/build_pair_final_search.py)、[final_pair_search_review.py](learning/gold_silver/final_pair_search_review.py) | [採用保留で終了](../docs/experiments/learning/gold-silver/2026-10-12-pair-final-search-review.md) |

`gold_silver_pair_pilot.py` は拡大学習・最終確認が使う特徴定義・静的評価・候補照合の部品も含む。
`run_tempo_search.py` の保存処理や `prepare_tempo_search.py` のコピー・USI処理も他の実験で使う。
「その実験が終わった」という理由だけでファイルを削除できる構成ではない。

## Native補助ソース

| ソース | 用途 |
| --- | --- |
| [learning_data_probe.cc](learning/native/learning_data_probe.cc) | 合法性・SFEN・Huffman・静的評価・静止探索。Makefileの別ビルドと、他probeの共通実装 |
| [king_safety_features.h](learning/native/king_safety_features.h) | 玉周囲4特徴と評価テーブルの対応。安全度probeからinclude |
| [gold_silver_pair_probe.cc](learning/native/gold_silver_pair_probe.cc) | 金銀連結の静的な特徴数と差分評価。最終探索ビルドも数え方を流用 |

通常の `bin/release` と実験用probeは別物。再ビルドの対象や保存済みSHAは各レポートを参照する。

## 履歴の扱い

既存ファイルは削除せず分類ディレクトリへ移動し、import・Makefile・実行パスを更新した。
保存済み結果・監査JSON・バックアップの旧パスとSHAは当時の記録として保持している。
終了済みのSHA固定実験を現在の移動後コードで再開しない。当時のコードを照合する場合は、
各レポートに記録したコミットまたは保存済みソースのバックアップを使う。
現行評価・定跡・保存候補は変更していない。
