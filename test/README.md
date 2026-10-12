# 回帰テスト

32個の `test_*.py` と定跡用fixture補助1個を用途別ディレクトリに配置した。
[ツール案内](../tools/README.md)／[開発手順](../docs/development.md)

## ディレクトリと実行

`books/`、`analysis/`、`learning/{data,core,tempo,king_safety,gold_silver}/` に分類した。
リポジトリ直下から全体を検出する場合：

```sh
python3 -m unittest discover -s test -t .
```

一部のテストはローカルの評価データ・probe・保存済みresultsが必要（後述）。

## 定跡・通常開発

| 用途 | ファイル |
| --- | --- |
| 現行の共通17局面・生成・読み込み | [test_operational_shin_book.py](books/test_operational_shin_book.py) |
| 先手▲７六歩6局面・保留▲３六歩版 | [test_black_pawn76_right_side_book.py](books/test_black_pawn76_right_side_book.py) |
| 後手の基礎候補・現行v2 | [test_shin_book.py](books/test_shin_book.py) |
| 保留中の後手７筋構想 | [test_seventh_trial_book.py](books/test_seventh_trial_book.py) |
| 旧先手系列・保存した別構想 | [test_black_trial_book.py](books/test_black_trial_book.py) |
| 旧生成txtの一時再生成・元SHA照合 | [book_test_fixtures.py](books/book_test_fixtures.py) |
| 通常探索のinfo解析・完了深さの扱い | [test_analyze_positions.py](analysis/test_analyze_positions.py) |
| 保存済み先手対局の集計・入力形式 | [test_review_black_runs.py](analysis/test_review_black_runs.py) |

定跡関連68テストを実行する場合は、リポジトリ直下で次を使う。

```sh
PYTHONPATH=tools python3 -m unittest discover -s test -t . -p 'test*book*.py'
```

定跡統合テストは `bin/release` と評価・標準定跡データを使用し、
登録局面の選択や短い探索への切替を確認する。新しい比較対局や学習実験ではない。
削除した旧txtは一時ディレクトリへ再生成するため、作業用の `books/` に戻す必要はない。
旧定跡のテストも共通の読込・手順前後・手番・OwnBook・手数上限の回帰確認として保持する。

## データ・教師の照合

| 段階 | ファイル |
| --- | --- |
| 既存データの由来・準備・入力 | [test_audit_learning_provenance.py](learning/data/test_audit_learning_provenance.py)、[test_prepare_learning_data.py](learning/data/test_prepare_learning_data.py)、[test_validate_learning_input.py](learning/data/test_validate_learning_input.py) |
| 教師54件の対象・生成・監査 | [test_teacher_refresh.py](learning/data/test_teacher_refresh.py)、[test_refresh_teachers.py](learning/data/test_refresh_teachers.py)、[test_audit_refreshed_teachers.py](learning/data/test_audit_refreshed_teachers.py) |
| 新教師と固定末端の接続 | [test_prepare_refreshed_pilot.py](learning/data/test_prepare_refreshed_pilot.py) |
| 拡大集合の選択・教師生成条件 | [test_prepare_pair_expansion.py](learning/data/test_prepare_pair_expansion.py)、[test_pair_teacher_generation.py](learning/data/test_pair_teacher_generation.py) |

## 学習の数値・保存

| 用途 | ファイル |
| --- | --- |
| 符号・進行度・平均損失・解析勾配 | [test_tempo_objective.py](learning/core/test_tempo_objective.py) |
| 上限・乱数・checkpoint・合成更新 | [test_tempo_updater.py](learning/core/test_tempo_updater.py) |
| 保存領域・候補params・整数丸め | [test_tempo_export.py](learning/core/test_tempo_export.py)、[test_tempo_rounding.py](learning/core/test_tempo_rounding.py) |
| 静止探索末端の受入条件・符号 | [test_qsearch_leaves.py](learning/core/test_qsearch_leaves.py) |

数値計算だけを確認する例：

```sh
PYTHONPATH=tools python3 -m unittest discover -s test -t . -p 'test_tempo_objective.py'
```

合成データでの更新器テストは、実棋譜を使う追加学習や候補選択とは区別する。

## 終了済み実験の実行条件・特徴

| 対象 | ファイル |
| --- | --- |
| 初回・新教師の手番runner | [test_tempo_pilot.py](learning/tempo/test_tempo_pilot.py)、[test_refreshed_tempo_pilot.py](learning/tempo/test_refreshed_tempo_pilot.py) |
| 選択済み手番候補の再静止探索 | [test_selected_qsearch.py](learning/tempo/test_selected_qsearch.py) |
| 通常探索の隔離準備・実行・再現性・終了確認 | [test_prepare_tempo_search.py](learning/tempo/test_prepare_tempo_search.py)、[test_run_tempo_search.py](learning/tempo/test_run_tempo_search.py)、[test_tempo_search_repeatability.py](learning/tempo/test_tempo_search_repeatability.py)、[test_close_refreshed_tempo_search.py](learning/tempo/test_close_refreshed_tempo_search.py) |
| 玉周囲4特徴・8係数・出力制約 | [test_king_safety_learning.py](learning/king_safety/test_king_safety_learning.py) |
| 金銀連結の定義・正負・上限 | [test_gold_silver_pair_learning.py](learning/gold_silver/test_gold_silver_pair_learning.py) |
| 金銀連結143／35件の入力・L2固定 | [test_expanded_pair_pilot.py](learning/gold_silver/test_expanded_pair_pilot.py) |
| 結果を見ない比較局面選択・環境変数の復元 | [test_final_pair_search_review.py](learning/gold_silver/test_final_pair_search_review.py) |

一部のテストはローカルの `results/learning-pilot/`、固定済みprobe、評価データを参照する。
Git管理ファイルだけで全テストが実行できる構成ではない。
テスト名が古い実験に対応していても、入力改変の拒否・更新上限・候補の固定・保存の整合性を
確認する役割が残っている。終了した実験の実行マーカーを解除してテストを通すことはしない。

## 今回の整理

テストは削除せず分類ディレクトリへ移動した。パッケージimportと参照パスを更新し、
回帰確認の内容は維持している。
動作の回帰確認と、特徴の有効性・棋力を測る実験は区別して扱う。
