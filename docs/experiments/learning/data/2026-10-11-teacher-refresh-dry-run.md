# 教師生成runnerの実装と探索0 dry-run

2026年10月11日、ソース基準 `4431991`。
[教師更新の設計](2026-10-11-teacher-refresh-plan.md)を実装するrunnerを追加し、
対象54局面、入力コピー、基準runtime、出力形式とUSIの準備完了をdry-runで検証した。
探索0、生成教師0、学習更新0、配備false。現行評価・定跡・25cp補正を維持する。
実探索の生成経路は合成テストまでで、実データによるdepth15教師生成は未実施。

## 実装

`tools/learning/data/refresh_teachers.py` は既定でdry-run。固定した準備manifestのSHAから54局面を読み、
未生成cp・split・元棋譜の由来を保持する。testを入力として扱わない。

実行前に準備と計画の対応、pending JSONLのSHA、36／18件の件数、運用6ファイル、
既存の分離baseline環境7ファイル（OpenMP含む）、probeのSHAを検証する。
基準releaseとparamsを使い、学習候補へ切り替える選択肢は設けない。
入力5ファイルを別inodeの独立コピーに保存し、実行後にも元／コピーSHAを照合する。
過去の棋譜・初回パイロット・準備データ・バイナリを上書きしない。

計画の変更は実行用コピーの `teacher_search_enabled` だけに限定する。
`--run` がある場合はtrueを必須とし、ない場合はfalseを必須とする。
深さ・局面数・探索時間・runtime・学習／配備フラグなどが参照計画と違えば拒否する。
参照計画は無効なまま維持する。実行用コピーはリポジトリ内に置く。

実探索は局面ごと新規プロセスでdepth15／MultiPV1／Threads1／Hash64／ON／book OFF／
Ponder OFF、54回以内・各30秒。ルート履歴を再生し、各結果をJSONLとreportへ逐次保存する。
実行時だけ準備ディレクトリへ独立した排他的マーカーを作り、別出力名での誤った再実行を拒否。
dry-runは実探索マーカーを消費しない。再開・自動再試行・補充は実装しない。

完了depth15のcp、boundsなし、合法PV、bestmoveとPV先頭一致、繰り返しなしを受け入れる。
mate／bounds／特殊終端／known-win cp（絶対値31000以上）／PV内繰り返しは、生結果と理由を
保存して教師cpをnullにする。途中停止・未完了深さ・不合法PV・読み込み失敗・timeout等は
部分結果とエラーを保存して中断する。受入件数と試行数は別に記録する。
学習準備flagは成功しても自動でtrueにせず、生成後の監査を別段階にする。

## dry-run結果

```sh
python3 tools/learning/data/refresh_teachers.py \
  results/learning-pilot/2026-10-11-teacher-refresh-preparation-v1/manifest.json \
  --output results/learning-pilot/2026-10-11-teacher-refresh-dry-run-v1
```

- 基準環境を1回起動し、USIオプション設定・isready・quitだけを送信。
  `readyok` を確認、読み込みエラー0。送信コマンド一覧にgoはない。
- 54局面で合法な履歴、SFEN／Huffmanの一致、繰り返しなしを再検証。
- 入力コピー5件のSHAと異なるinodeを検証。旧準備と実験成果物は不変。
- `train.teachers.jsonl` 36件／`validation.teachers.jsonl` 18件を書き出し。
  全件 `teacher_status=not-generated`、`teacher_cp=null`、勝敗損失OFF。
  過去cpは `archived_reference` のまま、新規教師とは分離。
- `teacher_generation_complete=false`、`training_ready=false`、`deployed=false`。
  探索・勾配更新・教師品質の計測・test選択はすべて0。
- 運用6ファイルと分離baseline7ファイルのSHAを前後照合し不変。

reportは計画／入力／runtime／probe／使用PythonツールのSHA、ハーネスgit revision、
dirty状態、実行環境、開始終了時刻、USI送信コマンドと出力、件数、各出力SHAを保存する。
今回のハーネスは `4431991` を基準にした未コミット実装としてdirty=true。
これは通常releaseが当該HEADでビルドされた証明ではなく、実行ファイルの同一性はSHAで扱う。

## 検証と成果物

新規7テストが通過した。実行フラグ以外の計画変更の拒否、cp受入、特殊スコア除外、
未完了／停止／不合法PV／bestmove不一致の中断、繰り返し除外を確認。
合成dry-runでは検索関数を呼ばないこととnull教師・既存出力拒否を確認した。
合成timeoutでは1回で止まり、failed行とreportの部分結果を保存し、再試行しないことを確認。
合成テストの検索はモックであり、実データの教師探索回数には含まない。

| 成果物 | SHA-256 |
| --- | --- |
| `results/learning-pilot/2026-10-11-teacher-refresh-dry-run-v1/report.json` | `e1e69434c4760e4331e5cd2a8e1f36b93119da3eefd9110d9dbbb98274ebe166` |
| `train.teachers.jsonl` | `e793d7aeabc135c2dc511da7d33f8d7989b900a6bc9b5a66f55963bf1b6ec178` |
| `validation.teachers.jsonl` | `49417da17b235d017967c8283f5508fef3678703129e9529612ff9faf95be466` |
| `tools/learning/data/refresh_teachers.py` | `2aeca389bc9496415e9e3995a6a10d1543f3dcb3c6236f582aedd0c9a6ee6b4f` |

## 次の段階

runner実装・テスト・dry-run・結果報告を一つのまとまりとして閉じる。
次は実行用計画コピーだけで教師探索を有効化し、新規出力に最大54回のdepth15教師生成を
行い、由来照合と受入／除外の層別集計まで一緒に確認する段階。
この記録では実探索を開始しない。学習更新・候補選択・配備は引き続きOFF。

由来のある教師が生成できても、相関・上限drawの裁定・validation再利用・
自己蒸留の限界は解消しない。外部バックアップも未実施。
生成後の監査を経てから次の学習計画を定め、欠損を埋める探索や学習設定の変更を自動で行わない。
