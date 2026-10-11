# 由来を固定した教師更新の設計と54局面の準備

2026年10月11日、ソース基準 `409796b`。
[初回パイロットの一区切り](2026-10-11-tempo-pilot-closure.md)を受け、
過去の評価データの同一性が不明な探索cpに代わり、現在の基準runtimeと条件を明記した
教師を小規模に作る計画を準備した。対象選択と合法性検査だけを完了し、探索・学習は未実施。

目的は教師の由来を確定できる経路を作ること。同じ基準エンジンの深い探索を教師にする
自己蒸留であり、強い外部エンジンからの教師や棋力向上の保証にはならない。
初回の学習候補を教師として使わず、現行の基準paramsを固定する。

## 対象とサンプリング

| 項目 | train | validation |
| --- | ---: | ---: |
| 局面数 | 36 | 18 |
| 各side/result層の局面数 | 6 | 3 |
| 選択されたrun数 | 22 | 6 |
| 選択された対局数 | 36 | 18 |
| 実際の最大局面数／run | 5 | 6 |
| 上限draw由来（うち後手） | 12（6） | 6（3） |

入力は既存の暫定train／validationを使い、割り当て済みrunを移動しない。
先手／後手×過去の先手勝ち／上限draw／後手勝ちの6層から、seed20261011とidの
SHA256順で決定的に選ぶ。層を順に巡り、1対局から最大1局面・1runから最大6局面とする。
重複SFENを拒否し、条件内で件数を満たせなければ失敗にする。
教師値の大小や初回候補との差を使って対象を選ばず、結果を見た補充も行わない。

Native probeの再生54件で全着手の合法性、ルートSFEN／Huffman一致、
ルート前の繰り返しなしを検査した。train／validationのrunは分離されている。
testの対象選択・品質計測は0、従来の未使用224件を維持する。

同じrunの対局や長い共通手順の相関は残る。6層均等は自然な局面頻度を表さない。
validationは初回パイロットでも使った集合なので、新たな未使用holdoutとは扱わない。
これらをデータの由来確定だけで解消したとは主張しない。

## 固定する教師探索条件

[計画JSON](configs/teacher-refresh-v1.json)を追加した。教師探索・実学習・配備のフラグは
すべてfalse。今回のツールには探索機能も教師値生成機能もない。

| 条件 | 設定 |
| --- | --- |
| 使用エンジン／評価 | 現在の基準release／params、候補paramsは使わない |
| 深さ／MultiPV | 15／1 |
| Threads／Hash | 1／64MB |
| ShinYonenagaGyoku／OwnBook／Ponder | ON／OFF／OFF |
| プロセス・履歴 | 各局面で新規起動、startposからルート前の着手を再生 |
| 上限 | 54探索、各30秒（検索待ち上限の合計最大1,620秒） |
| 再試行・拡張 | 0回、対象補充・時間延長・自動深掘りなし |
| 教師符号 | ルート手番側のcp |
| 勝敗損失 | 全件OFF。上限drawは勝ちや正式drawに変換しない |

起動・isready・合法性検査の待ち時間は検索30秒とは別で、総所要時間の上限とは区別する。
既存の分離したbaseline環境を再照合して利用する案とし、運用binの上書きを避ける。
教師生成用の独立した実行マーカーを用意し、閉じた初回パイロットのマーカーは解除しない。
Zobristキーは固定されず、由来を固定することと探索の完全な決定性は区別する。

## 保存形式と受入条件

今回の `*.pending.jsonl` は局面・元棋譜SHA・run／game／ply・側・層・履歴を保持する。
`teacher_cp: null`、`teacher_status: not-generated` とし、過去cpは
`archived_reference` に隔離した。過去cpを新しい教師として誤使用しない。
元の暫定JSONLや初回キャッシュ・候補・reportは変更していない。

生成runnerは次の実装段階。次の項目を新しいJSONL／manifestに保持する仕様とする。

- ルート情報とsplit、元棋譜／対象選択／計画／実行ツールのSHA。
- 通常release、params、progress、probability、標準book、共通定跡とOpenMPのSHA。
  bookは検索に使わないが、コピーと運用ファイルの同一性も照合する。
- 完了depth、score_type／score、bounds、bestmove、PV、nodes、time、途中停止、
  生USI info、受入／除外理由。教師cpと過去cpは別項目のまま保持する。
- 開始／終了時刻、実行環境、ハーネスのgit revisionとdirty状態。
  git revisionはハーネスの由来であり、既存バイナリがそのHEADでビルドされた証明ではない。
- 各出力のSHAと件数、層別受入件数、探索試行数、更新0／配備false。

cp教師として受け入れる条件は完了depth15、cp、boundなし、bestmoveとPV先頭の一致、
ルート同一性と合法PV、繰り返し履歴なし、使用runtimeの前後SHA不変。
mate／特殊終端／boundsは生結果と除外理由を残し、cpへ換算しない。
除外した局面の代替探索は行わない。timeout・プロセス異常・読み込み失敗・SHA不一致・
不合法PVは実行を中断して部分結果を保存し、自動で再開／再試行しない。

対象選択完了、教師生成完了、学習利用可能は別の状態として記録する。
生成後は由来照合・cp符号・PV合法性・層別欠損を監査し、学習準備flagは自動でtrueにしない。
旧データとのcp差は探索条件や歴史的paramsが異なるため、直接的な強化指標にはしない。
この段階で学習率・特徴・候補採用の判定を変更しない。

## 今回の準備結果と再現

```sh
python3 tools/prepare_teacher_refresh.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  --output results/learning-pilot/2026-10-11-teacher-refresh-preparation-v1
```

出力はignored results内の新規ディレクトリだけを許可し、既存出力を拒否する。
サンプリングの入力順独立性・層の均等、対局／run上限、重複SFEN拒否、
過去cpと未生成教師の分離を確認する新規4テストが通過した。
実データの54ルート検査が通過し、運用6ファイルのSHAは不変。
新規教師探索0、学習更新0、test選択0、配備false。

| 成果物 | SHA-256 |
| --- | --- |
| 計画JSON | `2f4353ac1bca81dcbf3c9aff396142f8e0925290babaa2a8b729fa5e08fa9f90` |
| `tools/prepare_teacher_refresh.py` | `a93c9743f2b709e05ce10f6a077de29d36bc23177e1b5b56cf6b0c95d204543b` |
| 準備 `manifest.json` | `a4662b0f349560cfa3f03b2fef536d5c6000f9e4d5ee6b75a569f306ed9be5fc` |
| `train.pending.jsonl` | `46fdf47a254bf6bd0d16f01118ca0525e46a1dfe2b8e064ddfd2d714686aae98` |
| `validation.pending.jsonl` | `3276e6f02c916ad2f3a6baf12d44389f32bab3463ba1b6ab24c0ed6accf82819` |

準備成果物は `results/learning-pilot/2026-10-11-teacher-refresh-preparation-v1/` に保持する。
定跡、25cp補正、現行評価、GUI設定を維持した。

次は生成runnerを実装し、まず更新・探索0のdry-runで対象・コピー・SHA・保存経路を確認する。
本設計では54回の教師探索も再学習もまだ実行しない。
