# 新教師36／18件の学習runner・固定計画・更新0検証

2026年10月11日、ソース基準 `3cf98ce`。
[新教師の接続と末端準備](../data/2026-10-11-refreshed-pilot-preparation.md)を読む専用の学習runnerと
無効な既定計画を追加した。実データでは更新0のdry-runを完了し、54末端の評価が一致した。
実学習・再探索・損失計測・候補選択・配備は未実施。

## 固定した条件

[計画JSON](../../configs/refreshed-tempo-pilot-v1.json)を新規追加し、旧64／64件のrunnerと計画は維持。
生成report・監査・準備report・train／validation末端・base params・既存backupのSHAを固定した。
使用するのは新教師36／18件だけで、testを読み込まない。

| 項目 | 設定 |
| --- | --- |
| 学習対象 | 現行paramsを固定ベースとした手番3係数差分 |
| 教師／末端 | 監査済み基準depth15 cp／保存済み基準QS末端を全実験で固定 |
| 損失 | mean sigmoid-square、gain1/600、差分L2=1e-6 |
| 更新器 | RMSprop rate0.25cp、decay0.9975、epsilon1e-12 |
| 上限 | 最大20更新、単回0.25cp以内、各差分±5cp以内 |
| seed／batch／平均化 | 20261011／最大128／decay0.9995 |
| 保存時点 | 0／5／10／20、平均化候補・完全なoptimizer／RNG checkpoint |
| 候補選択 | validation整数評価による損失＋L2、整数評価変化も必須 |
| 改善判定 | 基準より1e-12超の損失低下。改善なしは基準、同率は早い保存時点 |
| 勝敗損失／配備 | OFF／OFF |

train36件なので各更新で全36件を使う。過去cpではなく新教師cpだけを目的関数へ渡す。
候補として比較するのは現在差分ではなく平均化差分。
この設定は初回の小規模実験の条件を引き継ぎ、今回のvalidation損失を見て変更していない。
validation18件は小さく、過去実験でも使った集合なので、独立した棋力判定とは扱わない。

## 実装と実行制約

`tools/learning/tempo/refreshed_tempo_pilot.py` は既定でdry-run。
実行用計画コピーの変更は `real_data_training_enabled` だけに限定し、
`--run` がある場合はtrue、ない場合はfalseを必須にする。
配備・勝敗学習は常に無効、対象件数・optimizer・入力SHAなどの変更は拒否する。

保存済み末端を読むだけで、静止探索や通常探索を呼ばない。
新教師reader、既存objective／updater／exporter／候補再評価の検証済み処理を再利用する。
保存ごとにcandidateを再読込し、checkpointの復元状態を照合する。
勾配更新ごとに更新数を記録し、異常時は部分reportとエラーを残して中断。
実行時だけ準備ディレクトリに排他的な `learning-attempt-v1.json` を作成し、
自動再試行・再開・別名による繰り返し実学習を実装しない。

先の57ファイルのbackupを再照合し、今回の計画・runner・準備reportと追加の依存ツールだけを
別の追加backupへ保存する。元backupを変更せず、重い原本の再コピーを避ける。
今回の追加分は7ファイル・48,567バイト。元／コピーSHA・サイズ・独立inodeを検査した。
実学習時にも実行用計画コピーを含めた追加backupを新しい出力で検証する。
両backupは同一ボリュームのローカルコピーで、外部バックアップではない。

## dry-runとテスト

```sh
python3 tools/learning/tempo/refreshed_tempo_pilot.py \
  results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1/report.json \
  results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json \
  results/learning-pilot/2026-10-11-teacher-refresh-run-v1/audit-v2.json \
  --output results/learning-pilot/2026-10-11-refreshed-runner-dry-run-v1
```

- 固定36／18末端と教師を照合し、run／ルート／末端SFENの重複なしを確認。
- 初期状態だけを作成し、0更新candidateとcheckpointを保存・復元。
- candidate全体SHAはbase paramsと同じ。固定末端54件の整数評価変化0、loss=null。
- 保存は更新0だけ。新探索0、実データ更新0、quality_measured=false、selected_update=null。
- 元runtime、入力、既存backupと追加backupのSHAを再照合。エラー0、配備false。

新規5テストが通過した。無効計画・変更設定の拒否、評価変化と改善の両条件による選択・
改善なしの基準維持・同率時の選択、合成20更新と0／5／10／20保存、
異常時の再試行なし、末端SHA不一致の拒否を確認した。
テストの20更新は合成サンプル1件だけで、実データの勾配更新ではない。

| 成果物 | SHA-256 |
| --- | --- |
| `results/learning-pilot/2026-10-11-refreshed-runner-dry-run-v1/report.json` | `07660d91e7018de09812e5c96b9285409bcc9f5079d07c4e75efa60105bf53b6` |
| `additional-backup/manifest.json` | `aecc1951a85f95f68a5e395442b1c7de5a92308ef9620b01d78bc177efa58ffc` |
| 新しい計画JSON | `37c5eed0827627d7abea44c79460d64b5e7448b5123d060cb6a80da848d671db` |
| `tools/learning/tempo/refreshed_tempo_pilot.py` | `b8b9fc1bf089c928db980ae158530d4c6241018a9ccf027ed663432f904b1513` |

## 次の段階

runner・計画・テスト・更新0検証・報告を一まとまりで完了した。
次は新規の実行用計画コピーで実学習だけを有効にし、最大20更新を一度実行して、
候補保存・validation比較・結果監査までをまとめる段階。
現行paramsは上書きせず、学習候補の採用と再探索・対局は別に判断する。
この記録では実学習フラグを有効化していない。

由来は確認できたが自己蒸留は強化の保証ではない。
相関・validation再利用・固定末端と主探索の違い・上限draw裁定・外部backupの制約を維持し、
testの未使用224件を使った設定調整は行わない。
