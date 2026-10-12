# 小規模パイロット案と合成データでの更新器検証

2026年10月11日。静止探索の固定末端検証を `85db3fb` にコミットした。
今回は更新器と保存／再開を合成データで検証し、実験設定を具体化した。
既存棋譜・探索cpを使った学習、追加探索、対局、評価バイナリ保存は行っていない。

## 実装と検証

`tools/learning/core/tempo_updater.py` は手番差分3係数だけのRMSprop状態を扱うライブラリ。
エンジン、教師ファイルreader、params writer、実データ学習CLIは含まない。
呼出し側が、平均損失と差分L2の勾配を渡す方式とした。

```text
a = decay*a + gradient^2
move = clip(step_rate*gradient/sqrt(a+epsilon), ±max_step)
delta = clip(delta-move, ±delta_limit)
average_sum = average_decay*average_sum + delta
average_mass = average_decay*average_mass + 1
averaged_delta = average_sum/average_mass
```

RMSprop累積値は既存技巧の式と同様に、`(1-decay)` を掛けない形。
最大更新数20、1更新0.25cp以内、差分各成分±5cp以内を検査する。
平均化も差分にだけ行い、固定ベースを縮めたり混ぜたりしない。
非有限勾配、平方のoverflow、異常な累積／平均状態、上限超過を拒否する。
状態は不変オブジェクトとして返すため、失敗時に元状態を部分更新しない。

seed固定、1バッチ最大128、バッチ内非復元抽出を実装した。
保存には差分、平方勾配累積、平均化累積と重み、更新数、RNG状態、設定と入力のID、
Python版を含め、復元時に内容SHA・設定・入力binding・版を照合する。
このcheckpointは初期化専用のゼロ差分checkpointとは別schemaであり、
既存の更新なしreaderを解除するものではない。

```sh
python3 -m unittest discover -s test -t . -p test_tempo_updater.py -v
python3 tools/learning/checks/check_tempo_updater.py \
  --output results/learning-pilot/2026-10-11-input-validation-v1/updater-synthetic-v1.json
```

256件の合成3次元目標と平均二乗距離を使い、20更新した。
これは本番のsigmoid探索cp損失ではなく、更新・sampling・保存の制御を検査するための問題。

| 項目 | 結果 |
| --- | --- |
| 合成更新数／実データ更新数 | 20／0 |
| 合成損失 | 1.906978125 → 0.024015714 |
| 最終差分cp | `(1.288331, -0.972852, 0.746696)` |
| 平均化差分cp | `(0.944490, -0.786389, 0.652284)` |
| 最大1更新幅 | 0.249999999999944cp |
| 保存・再開 | 10更新目をJSON保存・復元し、20更新連続実行と全状態が完全一致 |
| 上限 | 21更新目を拒否 |

新しい6テストは、降下方向、ゼロ勾配、単回／累積の上限、平均化の範囲、
バッチの上限と再現性、checkpointのbindingと改変拒否、異常入力時の状態保持、
合成問題の損失低下と厳密な再開を確認し、成功した。
この結果から実データの損失低下や棋力向上を主張しない。

## 最初の実データパイロット案

設定ファイル：[tempo-pilot-v1.json](../../configs/tempo-pilot-v1.json)。
`real_data_training_enabled: false`、`deployment_enabled: false` として計画を保存した。
過去のruntimeパラメータが不明なことは、歴史的探索cp教師の制約として明記する。
元の準備manifestと `training_ready: false` は変更しない。

初回は、既に接続を確認した64train局面の固定Qsearch末端に限定する。
当初の1,024局面は将来の上限とし、この64局面を使う動作確認から始める。
validationは別runの既存256局面から最大64局面を選び、基準末端の準備が必要。
test256局面の教師品質は、この段階では参照しない。
上限draw由来の探索cpを残し、勝敗損失はOFFのままとする。

| 設定 | 初回案 |
| --- | --- |
| 対象 | 固定ベース＋手番3係数差分。進行度・他評価・25cp補正・定跡を固定 |
| 損失 | sigmoid二乗誤差の平均、gain1/600、差分L2係数 `1e-6` |
| RMSprop | rate0.25cp、decay0.9975、epsilon `1e-12`、1更新上限0.25cp |
| 実行上限 | 20更新、差分±5cp、seed20261011、単一処理 |
| sampling | batch最大128。train64なら全64を使用し、集合内順序を再現可能にする |
| 平均化 | decay0.9995。短い実験でも重み総量で割り、ゼロ初期値による縮小を避ける |
| 保存 | 更新0／5／10／20。float状態・RNG・平均化状態・manifest・別名候補params |
| 選択 | 3つの平均化checkpointをvalidationで比較。改善なし／整数評価変化なしなら基準維持 |

前段のL2 `1e-4` は数値検証用であり、今回の案ではcp単位の平均損失に対して
`1e-6` を固定候補とする。最大5cpの差分でのL2損失は0.0000125／成分となる。
元の大バッチ・係数2000の損失用epsilon `1e-4` を、正規化した小さい勾配へ
そのまま持ち込まない。epsilon `1e-12` は、この単位に合わせた検証案である。
validation/testの結果に合わせて選んだ値ではなく、最適な設定を証明したものでもない。
結果が曖昧でも自動的に係数調整・更新数増加・新規対局へ進めない。

途中で非有限値、進行度・対象外成分の変化、固定ベース／入力の改変、上限超過が
あれば停止する。基準のコピーと候補の保存先を分け、現行 `bin/` へは保存しない。
候補選択ができても、対局評価と現行データへの採用は別段階とする。

## 保存状態と次の作業

合成検証JSONのSHA-256：
`c24b4a5fe93a19aaa80349cca97797cb032d38f3b264b3afa4f6b1ab50038963`。
設定・更新器・合成入力ID・4つの合成checkpointを同JSONに保存した。
元の通常バイナリ、4つのbinデータ、共通定跡の6ファイルは前後でSHA不変。
現行評価に合成差分を適用していない。外部バックアップは行っていない。

次は別名候補paramsへの差分出力・保存再読込の検証と、validation固定末端の準備を行い、
実験runnerのdry-runを完成させる。ここまでの制御を具体的に検証してから、
既存棋譜を用いた最大20更新の実行を扱う。今回その実行はしていない。
