# 実験runnerのdry-runと検証済みローカルバックアップ

2026年10月11日。候補ファイルの保存・再読込とvalidation末端の準備を
`532a8dd` にコミットした。今回は入力から更新0の候補保存・再読込までを
runnerで確認し、必要な入力の独立コピーを作成した。実データ学習は実行していない。

## runner

`tools/learning/tempo/tempo_pilot.py` の既定動作はdry-run。設定、元manifest、生JSON、分割、
train/validationの固定末端、現在のruntime、バックアップのSHAを確認する。
run・ルート・末端の重複、対象外の入力、未検証の設定、未整備のバックアップを拒否する。
更新器、目的関数、入力、設定をcheckpointのbindingに含める。

dry-runでは以下だけを実行する。

1. 固定したtrain64／validation64と設定を読み、入力とバックアップを照合する。
2. 更新0・ゼロ差分のfloat/RNG状態を作成する。
3. 別名のparamsとcheckpointを排他的に保存する。
4. train＋validationの128固定末端を再生し、候補の進行度・対象外評価成分を確認する。
5. 現行ファイルのSHA不変と、更新0・品質未測定・選択なしを記録する。

dry-runでは目的関数、勾配更新、validationの品質計算、候補選択、新規探索を呼ばない。
`--run` は設定の `real_data_training_enabled` がtrueの場合だけ受け付ける。
現在の[設定](../../configs/tempo-pilot-v1.json)はfalseで、この経路は実行していない。
実行経路は最大20更新、保存0／5／10／20、平均化候補の整数validation損失比較、
改善なし／整数評価変化なしなら基準維持とする。現行 `bin/` への保存・採用は行わない。
再開時は既存0／5／10等のcheckpointを再確認して候補履歴も保存し、設定やbindingの
違う状態を受け付けない。実行経路の実データ動作と結果はまだ未検証である。

## バックアップ

`tools/learning/core/learning_backup.py` は新規ディレクトリにファイルをコピーし、各ファイルの
SHA・サイズ・元ファイルとの別inodeを確認する。hard link、元データ削除、上書きは行わない。
復元用manifestはリポジトリ相対パスで構成し、path escape、改変、必要ファイルの欠落を拒否する。

作成したローカルコピーは61ファイル・772,357,064byte。
通常バイナリ、4つのbinデータ、共通定跡、47runの生JSON、分割3ファイル、
元manifest、固定末端2ファイル、設定、probeを含む。
全コピーと元ファイルのSHAが一致し、ファイルを共有するhard linkではないことを確認した。
これは同じローカルボリューム上の独立コピーであり、Google Drive等への外部バックアップは
行っていない。元のrawデータを削除していない。

## 実データで行ったdry-run

```sh
python3 -m unittest discover -s test -t . -p test_tempo_pilot.py -v
python3 tools/learning/tempo/tempo_pilot.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  results/learning-pilot/2026-10-11-input-validation-v1/qsearch-leaves-v1.json \
  results/learning-pilot/2026-10-11-input-validation-v1/validation-leaves-v1.json \
  --backup results/learning-backups/2026-10-11-pilot-v1/manifest.json \
  --create-backup \
  --output results/learning-pilot/2026-10-11-pilot-dry-run-v1
```

| 項目 | 結果 |
| --- | --- |
| mode／実データ更新数 | dry-run／0 |
| 候補params SHA | 元paramsと同一 `6bbc573306839fe019634dd94b06af7c22834a641e8bc060e23889ae9b3b2195` |
| 再読込した固定末端 | 128件、整数評価変化0、進行度・対象外成分一致 |
| validation損失／候補選択 | 未計算／なし |
| 更新checkpoint | 0のみ |
| 元runtime | 通常バイナリ・4つのbinデータ・共通定跡のSHA不変 |

新しい6テストは、既定設定で実学習を拒否すること、未検証設定・集合重複の拒否、
合成1ステップでの勾配接続、バックアップの独立性・改変検出・パス範囲・必要入力の
欠落と上書き拒否を確認し、成功した。実データの更新はテストにも使っていない。

| 成果物 | SHA-256 |
| --- | --- |
| `results/learning-backups/2026-10-11-pilot-v1/manifest.json` | `adb3fc1c7dbb7f547e52c2258ca76256f38a9b2370c3ab84b7800f5d5aea4338` |
| `results/learning-pilot/2026-10-11-pilot-dry-run-v1/report.json` | `44c428e9009d821bdd2d4cf1de402468add86374167bc9ba92b8cff6a6766064` |

設定ファイルはバックアップ時の版を維持し、実学習・採用フラグをfalseのままにした。
設定変更時には、runnerが要求するバックアップとbindingも一致させる必要がある。
元manifestや先行結果を上書きせず、test256件の教師品質も測定していない。

## 次の段階

パイロットの入力64／validation64、最大20更新、各更新0.25cp、差分±5cp、
固定末端・手番3係数だけの条件で、実行入口とdry-runまで準備できた。
実データ学習は当初の調査・計画段階の保留指定を維持して未実施。
この指定を変更して実行する段階で、実行用設定・検証済みバックアップ・新規出力先を
確定させる。実行しても定跡・25cp補正・現行paramsは変更せず、採用判断は別に行う。
この実験は動作と限定された教師への適合の確認であり、棋力向上の証明ではない。
