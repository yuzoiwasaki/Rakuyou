# 金銀連結のデータ拡大：教師生成・固定末端・監査まで完了

2026年10月12日。[準備済み144／36局面](2026-10-12-pair-data-expansion-preparation.md)に対し、
現行基準で教師生成を一度だけ実行した。180探索はすべて完了、PV内の局面反復で2件を除外。
**有効な教師・固定末端は学習143件／検証35件**。補充・再選択・再試行・条件変更なし。
学習更新・損失／勾配測定・候補選択・対局・配備は0。現行評価・定跡・25cp補正は維持した。

## 件数と層

以下は元棋譜の先後の勝敗。教師の符号はroot手番側であり、勝敗教師は使用しない。

| 層 | 計画train | 有効train | 計画validation | 有効validation |
| --- | ---: | ---: | ---: | ---: |
| 先手・先手勝ち | 24 | 24 | 6 | 5 |
| 先手・draw | 24 | 23 | 6 | 6 |
| 先手・後手勝ち | 24 | 24 | 6 | 6 |
| 後手・先手勝ち | 24 | 24 | 6 | 6 |
| 後手・draw | 24 | 24 | 6 | 6 |
| 後手・後手勝ち | 24 | 24 | 6 | 6 |
| 合計 | 144 | 143 | 36 | 35 |

先手／後手の内訳はtrain71／72、validation17／18。drawはtrain47（後手24）、
validation12（後手6）。打切りdrawを勝ちや正式drawに読み替えていない。
各層の件数は完全には揃わなくなったが、結果を見た補充や重み付けは実施していない。

除外は次の2件だけ。180探索の実行欠損・timeout・エラーは0。

| 集合・層 | run SHA・対局・手数 | 理由 |
| --- | --- | --- |
| train・先手draw | `e20dcf8bc053c5f82fad53132a70eea5b39e8a734c3e73271401690e701eb3df:24:33` | 教師PVを含む履歴に局面反復 |
| validation・先手勝ち | `e3ccacfacc268a8102c8e12c31dfae8110b3e2f7a7088636b8748fefd3a2c0a8:71:59` | 教師PVを含む履歴に局面反復 |

除外した教師の探索結果・コマンド・生ログも保存した。
固定末端は受入教師178件に対して178回だけ準備し、追加除外・エラー0。

## 維持した条件と実行

教師は現在の基準params、depth15、MultiPV1、Threads1、Hash64MB、ShinYonenagaGyoku ON、
OwnBook OFF、Ponder OFF、局面ごと新規プロセス、30秒上限。対象180件は事前固定。
隔離済みbaseline実行環境をSHA照合して使用し、通常のreleaseやparamsを書き換えていない。
生成区間は02:49:38〜02:51:52 UTC、約134秒。これは前後処理を含む当該実行の実測である。

旧36／18件のrunner・監査・readerは変更せず、`tools/pair_teacher_generation.py` が
180件の件数と準備SHAを接続した。生成ループ・教師判定・コマンド／PV監査は既存方式を流用。
基準の無効計画は保持し、実行用コピーのteacher_search_enabledだけtrue。
学習・配備フラグはfalseのまま。探索0 dry-runで180rootとUSI readinessを先に確認した。
ハーネスHEADは `619cb3b`、新規ツールと前段準備が未コミットの状態（dirty=true）で生成した。
実際のツールSHAと入力コピーを保存し、HEADだけをコードの同一性の根拠にしていない。

```sh
python3 tools/pair_teacher_generation.py \
  --plan results/learning-pilot/2026-10-12-pair-teacher-run-v1-plan.json \
  --output results/learning-pilot/2026-10-12-pair-teacher-run-v1 --run
python3 tools/pair_teacher_generation.py \
  --audit results/learning-pilot/2026-10-12-pair-teacher-run-v1/report.json \
  --output results/learning-pilot/2026-10-12-pair-teacher-run-v1/audit-v1.json
```

終了済み生成は準備ディレクトリの `teacher-generation-attempt-v1.json` で再実行を拒否する。
生成監査は全180件の由来・JSONL／report・コマンド・生ログ再解析・符号・root／PV合法性・
反復除外・入力コピー・runtimeを照合した。受入178／除外2の判定が一致。

## 固定末端と学習未実施の確認

`tools/prepare_pair_leaves.py` で、既存の静止探索probe・末端判定を使い、
現行基準の固定末端を準備した。探索の繰返しや差分係数による再探索は行わない。
全178末端が受入可能で、rootとleafのSFENは集合間で非重複。
PV全履歴の反復なし、整数評価の内訳からの再構成・cached/full一致・手番の偶奇を確認した。
金銀ペアprobeのゼロ差分でも同じ評価・内訳・進行度である。

| 固定末端の特徴出現 | train143 | validation35 |
| --- | ---: | ---: |
| どちらかに対象ペアあり | 124 | 31 |
| 先後ペア数差が非ゼロ | 85 | 22 |

同じ特徴・Config（L2=1e−6、符号自由、2係数ゼロから、最大20更新）を保持。
既存更新器で更新0のcheckpointを保存／復元し、全座標・平均値ゼロを確認。
ゼロ差分sidecarは実験用であり、現行releaseに採用したものではない。
学習結果や勾配を見て特徴・係数・条件を変更する処理は行っていない。

```sh
python3 tools/prepare_pair_leaves.py \
  results/learning-pilot/2026-10-12-pair-teacher-run-v1/report.json \
  --output results/learning-pilot/2026-10-12-pair-leaves-v1
```

生成ディレクトリの `frozen-leaf-preparation-attempt-v1.json` で再準備を拒否。
静的な保存結果監査では178件を旧probeと金銀ペアprobeで再生し、整数評価・進行度・
内訳・特徴数が一致した。この監査は追加の静止探索／通常探索を実行していない。

新規計画制約テスト1件と既存生成7・教師監査5・末端判定5テストが通過。
元57ファイルのバックアップを維持し、今回の追加40ファイルのみ別コピーしてSHA・独立性を照合。
入力と通常runtime、前回候補／checkpointは全SHA不変。外部バックアップは未実施。

## 次の区切り

教師と固定末端の有効件数・層・特徴出現を確認できたため、**ここで止める**。
学習接続・実行はまだ行わず、学習の段階に進む際に知らせる。
178件の監査完了は学習実行や評価採用を意味しないため、training_readyと配備はfalse。
旧18件検証の再利用からは進んだが、同じ検証run内の未使用対局であり完全に未知のrunではない。
同一基準の自己蒸留とrun／序盤の相関、少数層という制約も引き続き残る。
予約testは使用せず、欠けた2件を補充しない。

## 証拠

| ファイル | SHA-256 |
| --- | --- |
| `results/learning-pilot/2026-10-12-pair-teacher-run-v1/report.json` | `01c9a6cdf28e6c5114a0dafae99937ce0ce3dfe06900864faa4683eda403dd4c` |
| 同 `audit-v1.json` | `47c044ef535b45b4882107a9e0a68a508942684650232d4851e16c90c71acdc6` |
| `results/learning-pilot/2026-10-12-pair-leaves-v1/report.json` | `6e5216775697f1bbeaa6bd5c3e37e105378148f34fb04239aa6e313aa484dfed` |
| 同 `audit-v1.json` | `747229695ece4961f079dc1bbab30cda86cb52fb6b9ddd5dc4875dc5d7029a73` |

教師JSONL、固定末端cache、計画・コードSHA、零checkpoint、追加backupと生ログは各出力に保存。
選択済み180root・旧集合・前回候補はすべて保持する。
