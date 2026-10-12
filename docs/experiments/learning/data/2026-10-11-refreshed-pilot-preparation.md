# 新教師の入力接続・固定末端準備・更新0 dry-run

2026年10月11日、ソース基準 `58131a6`（教師生成・監査までプッシュ済み）。
由来を照合済みの新教師54件を専用readerで読み、基準静止探索の末端を固定した。
train36／validation18すべてが適格。既存更新器の初期状態の保存・復元、ゼロ差分候補の
保存・再読込を更新0で確認した。実学習・損失計測・候補選択・配備は行っていない。

## 入力の接続

`tools/learning/data/prepare_refreshed_pilot.py` を追加。
[教師生成reportと最終監査](2026-10-11-teacher-refresh-generation.md)のSHAを固定し、
JSONLとreportの一致、受入済みcp、ルート手番側の符号、勝敗損失OFFを検査する。
新教師のcpを `FrozenLeaf.teacher_root_cp` に渡し、旧cpは `archived_reference` に保持する。
過去の暫定JSONLを上書きしない。train／validationのrunを分離し、testを読み込まない。

元棋譜・生成入力のSHA、運用runtime、分離した基準runtime、probeのSHAを照合する。
readerと固定末端は生成report／監査SHAに結び付け、旧教師や別候補への混在を拒否する。
今回は入力と更新器の接続準備であり、実学習コマンドは実装していない。

## 基準静止探索の末端

各局面につき1回、計54回だけのON・depth0・PV静止探索を実施した。
learning_mode=true、毎回fresh1MB TT、paramsのKP第4成分とprogressの一致を検査。
Huffman境界でルートを復元し、ルート前のNode履歴は省く。
通常depth15教師は全着手履歴を再生しているため、両者の探索条件は異なる。

cached／full末端評価の一致、ルートと末端の手番符号、静止探索scoreが末端整数評価に
一致すること、特殊終了の適格性を検査した。
別の静的評価probeでルート＋PVを再生し、SFEN、進行度、packed parts、整数再構成、
繰り返しなしも照合した。除外時の補充や再探索は行わない。

| 項目 | train | validation |
| --- | ---: | ---: |
| 要求／受入 | 36／36 | 18／18 |
| 除外 | 0 | 0 |
| 各side/result層 | 6 | 3 |
| 上限draw由来（うち後手） | 12（6） | 6（3） |
| PV偶数長／奇数長 | 30／6 | 13／5 |
| PV長ごとの件数 | 0手27・1手6・2手3 | 0手11・1手4・2手2・3手1 |

train／validation間でrun・ルートSFEN・末端SFENの共通要素は0。
長い共通手順や同一run内の対局相関まで消えたとは扱わない。
基準末端は今後の限定した実験で固定する候補であり、変更後のPVを追従させるものではない。

## 更新0のdry-run

末端準備の後は探索を行わず、既存 `tempo_updater.Config()` の初期状態を作成した。
設定は既存パイロットと同じ最大20更新・単回0.25cp・各差分±5cp・batch128・seed20261011。
今回は初期状態の接続検査にだけ使い、新しい実学習を有効化していない。

- 新教師の生成／監査／末端／ベースparams／objective／updaterのSHAをbindingに保存。
- 更新0・差分0のcheckpointを保存し、完全なoptimizer／RNG状態を復元して一致を確認。
- `params-zero-delta.bin` を別名保存。全体SHAは現行paramsと同じ。
- 固定末端54件を候補から再評価し、非手番成分・進行度・SFENと整数評価の一致を確認。
  評価変化0／54、loss=null。損失・勾配・validation選択は行わない。
- 読み込んだ入力・元棋譜・runtime・末端・検証ツール等を57ファイルの独立した
  ローカルコピーとして保存。628,846,812バイト、全SHA・サイズ・別inodeを照合。
  原本は保持し、外部バックアップは未実施。

末端準備の探索54回と、その後のdry-runの探索0回を区別する。
`training_enabled=false`、`training_ready=false`、`deployment_enabled=false`。
旧パイロットの候補を採用せず、定跡・25cp補正・通常release・運用paramsを維持した。

## 検証と成果物

新規5テストが通過。新cpだけをsampleへ接続して旧cpを保持すること、後手ルートの
符号／奇数長PVの微分係数、未生成／除外／test／勝敗損失の拒否、解析cp不一致、
異なるroot・特殊score、結び付けていない生成reportの拒否を確認した。
実データでは54末端の検査とゼロ更新候補・checkpoint・backupの往復照合が完了した。

```sh
python3 tools/learning/data/prepare_refreshed_pilot.py \
  results/learning-pilot/2026-10-11-teacher-refresh-run-v1/report.json \
  results/learning-pilot/2026-10-11-teacher-refresh-run-v1/audit-v2.json \
  --output results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1
```

既存出力を拒否し、生成ディレクトリの `frozen-leaf-preparation-attempt-v1.json` で
同じ末端準備を別名出力で誤って再探索することも拒否する。マーカーは解除しない。
終了済み成果物は `results/learning-pilot/2026-10-11-refreshed-pilot-preparation-v1/` に保持する。

| 成果物 | SHA-256 |
| --- | --- |
| `report.json` | `da5310a8b195632f39c36101d853b0992f9ad447d1a7ca07e5752251de8e04a3` |
| `train.leaves.json` | `d284a89c42447578025421ea9f55516ad9b01dde537666f250b2fd97343f60f3` |
| `validation.leaves.json` | `c18997ac3694870cffe66872cafd6c520a5c457e18c695e9dab9f7f112d42d3e` |
| `checkpoint-00.json` | `d73526c9b704e6b6f32a71a84bd818dc5a7d0c3c4098310485978ccc89248ac2` |
| `backup/manifest.json` | `ba18462cd3b7c260fdfbbe5088d10efc1bfa9abc0d9a2087add815eb515e644b` |
| `tools/learning/data/prepare_refreshed_pilot.py` | `bd8e7c04c045f12b1fe19f4d579075bfd5234ab9cc44bf1da1c991dc99b4afe3` |

## 次の段階

入力接続・固定末端・更新0dry-runの検証を一まとまりで閉じる。
次は新教師36／18件用の学習runnerと無効な既定計画を用意し、今回の末端SHAと結ぶ。
旧runnerが前提とする64／64件の制約を勝手に緩めず、旧実験の再現性を保持する。
最大20更新など既存の小さい上限を引き継ぐ案とし、独立保存・整数validation比較・
改善なしなら基準維持という条件を実行前に固定する。
実学習の有効化と実行は別に扱い、testを見て学習設定を調整しない。

自己蒸留は強化の保証ではない。相関、validation再利用、上限drawの裁定、固定末端と
主探索の違い、外部バックアップ未実施という制約を保持する。未使用test224件も維持する。
