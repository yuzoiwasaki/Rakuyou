# 更新なしの学習入力readerと固定ベース検証

2026年10月11日。[由来確認](2026-10-11-learning-provenance-review.md) に続く、
入力・保存・再読込の検証。探索・対局・学習更新は行っていない。
現在の暫定分割と、定跡・初手玉移動・固定25cp補正は維持した。

## 実装

`tools/validate_learning_input.py` は、準備済みmanifestとJSONLを読む専用入口。
既存 `--learn` は呼ばず、棋戦フィルターを経由しない。
歴史的教師の由来が未確認であることを保持したまま、検証用途だけで入力を受け付ける。

- 生JSONと分割ファイルのハッシュを確認する。
- schema、集合名、ON、整数cp、depth15、run/game/plyと元記録の対応を確認する。
  着手前手順、手番、教師手、PV、cp、結果、終了種別、drawの勝敗マスクも照合する。
- 集合間のrun/SFEN/prefix24/ID、集合内のSFEN/ID重複、1局8局面の上限を再確認する。
- ネイティブprobeで全着手前手順と教師PVを再生し、保存SFEN・手番・Huffmanを照合。
  反復履歴が混入していれば拒否する。
- 現行paramsのハッシュとABIを確認し、別名のbyteコピーを排他的に保存する。
  元とコピーのすべての再生局面で、ON/OFF静的評価と進行度が一致することを確認する。
- 手番3係数の差分、固定ベースSHA、更新回数0を含む版付きcheckpointを保存する。
  別のcheckpointを読むときも、非ゼロ差分、非有限値、更新回数1以上、別ベースを拒否する。
  非ゼロ差分の適用やoptimizerはまだ実装していない。

`learning_data_probe.cc` にはpackedな手番係数の検査と、静的評価の進行度出力を追加した。
評価は既存 `EvaluateAll` / `ComputeFinalScore` から取得する。
成らずに行きどころのない桂を移動する入力も、エンジンのassertへ進む前に拒否する。
通常エンジンの `src/` は変更していない。

## 実データでの結果

```sh
make learning-probe -j2
python3 -m unittest discover -s test -p 'test_*learning*.py' -v
python3 tools/validate_learning_input.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  --output results/learning-pilot/2026-10-11-input-validation-v1
```

| 集合 | 検証した教師局面・PV | 上限draw局由来 | うち後手draw |
| --- | ---: | ---: | ---: |
| train | 1024 | 341 | 170 |
| validation | 256 | 85 | 42 |
| test | 256 | 85 | 42 |

計1,536局面すべてで入力・元記録の照合、着手再生、保存局面照合が成功した。
元paramsとコピーのON/OFF静的評価・進行度は、各教師のルートだけでなく、
着手前手順と教師PVのすべての途中局面で一致した。
testも入力の整合性とゼロ差分一致を確認しただけで、教師との損失や品質指標は
計算していない。モデル選択のためのtest利用は行っていない。

手番係数の生値は `[-163745, 653365, -1105013, 0]`、固定小数点スケールは65536。
第4成分を含めてコピーとの一致を確認した。進行度は有限値かつ0〜1の範囲にあった。
更新数は0、差分は `[0.0, 0.0, 0.0]`、`training_ready: false` を保持している。

関連19テスト（準備10、由来4、入力5）が成功。
新しい入力テストは、非ゼロ／NaN／別ベース／不正更新回数の拒否、
drawの勝ちラベル化、手番・PV・cp・手順・由来フラグの不整合、
元記録のbound、JSONLのhash・schema・件数・OFF・bool cpの拒否を確認する。

## 成果物と次の作業

出力ディレクトリは `results/learning-pilot/2026-10-11-input-validation-v1/`。

| ファイル | SHA-256 |
| --- | --- |
| `validation.json` | `f5970dd5034feefd60c36d59bdcd26075636d0b773865a5316a86c6b068c25d1` |
| `checkpoint-zero.json` | `e06c125cc4a3e5adc98f0841c4c655bb6c32a13bf7907d51ced9a5d2478924ec` |
| `params-zero-delta.bin` | `6bbc573306839fe019634dd94b06af7c22834a641e8bc060e23889ae9b3b2195` |

今回ビルドしたprobe SHAは
`907da718a5ca53e33f26ef44459583cc62ca2a4aa1d0c069bbebc0a2e1e99bde`。
準備時のprobeとは検査機能の追加で異なるが、ABIは同じ。
元manifest、JSONL、由来確認JSON、通常バイナリ、4つのbinデータ、共通定跡を
変更していない。現在の6つの通常バイナリ／データ／定跡は検証前後のSHAも一致した。
外部バックアップは行っていない。

この入口は損失・勾配・探索・非ゼロ差分をまだ扱わない。
次は手番3係数について、目的関数と符号・進行度係数を明示し、
学習更新なしで解析勾配と有限差分を確認する段階。
静止探索の末端を使うRootStrapへの接続は、それに続く別の検証とする。
歴史的データの由来・長い共通手順・正式裁定の制約を解除したわけではなく、
学習実行や現行paramsへの昇格を自動では行わない。
