# 静止探索の固定末端と手番差分の接続検証

2026年10月11日。[整数丸めの検証](2026-10-11-tempo-rounding-validation.md) は
`c19fbc7` にコミットした。今回は接続確認のための小規模な静止探索を行った。
optimizer・学習更新・対局・現行データ上書きは行っていない。

## 探索境界と設定

`learning_data_probe.cc` に明示的な `--qsearch params progress` を追加した。
従来の再生・静的評価モードは探索しない。
Qsearchの入力はUSI着手列から合法性を確認したルート局面で、次の設定とする。

- paramsとprogressを明示的に読み込み、サイズとKP第4成分の重み一致を確認する。
  `Node::Evaluate` のデバッグ検査も進行度を照合するため、未読込の重みを使わない。
- ルートをHuffman圧縮・復号の境界に通す。これはRootStrapと同様に過去のNode履歴を
  含めない方式であり、対局全体の正式な千日手判定ではない。
- ON固定、単一呼出し、深さ0、PV探索、window ±31000、局面ごと空の1MB TT。
  定跡と実現確率の重みを探索で使わず、反復深化は呼ばない。
- `learning_mode=true` でTTの得点置換・hash cutを無効にする。
  これはパラメータを更新する意味ではなく、末端と評価の対応を保つための探索設定。
- 戻り値、PV、ルート・末端の手番、末端SFEN、差分／全計算の静的評価、
  進行度、packed成分、反復検出、王手状態を保存する。

既存 [RootStrap](../../../../src/learning.cc) はこのlearning_modeを明示していない。
通常の [静止探索](../../../../src/search.cc) ではTT得点から戻る経路があり、
保存された探索得点と取得PV末端の対応が常に保証されるとは仮定しない。
新しい検証入口では空のTTとlearning_modeを使い、実際の対応も必ず照合する。
既存trainerのソースは今回変更していない。

## 固定末端の検証手順

`tools/check_qsearch_leaves.py` はtrainの先後／結果6層から順番に64ルートを選ぶ。
validation/testは入力整合性だけを読み、探索・品質測定には用いない。

1. 基準paramsだけでQsearchを1回実行する。
2. mate／既知勝ち、反復・SHEK、王手が残る終端、戻り値と静的末端評価が合わない
   ケースを除外する。差分評価と全計算の不一致は検査エラーにする。
3. PVの長さと末端手番、ルート手番側へ変換した末端cpとQsearch戻り値を照合する。
   元の着手前手順＋PVを別のstatic probeで再生し、盤面、手番、進行度、
   packed成分、静的評価を照合する。完全な棋譜履歴側での反復も検査する。
4. 固定した末端から、前段と同じ手番3係数の解析勾配を有限差分と比較する。
5. 固定末端だけを±の小幅手番摂動で再評価し、整数丸めとルート側の符号を照合する。
   摂動後のQsearchやPV切替は実行しない。

## 結果

```sh
make learning-probe -j2
python3 -m unittest discover -s test -p test_qsearch_leaves.py -v
python3 tools/check_qsearch_leaves.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  --output results/learning-pilot/2026-10-11-input-validation-v1/qsearch-leaves-v1.json
```

64ルートすべてで、Qsearchの戻り値と固定末端の手番変換後の評価が一致した。
除外0、先手33／後手31、上限draw由来21（うち後手10）。
PV長は0手43件、1手11件、2手6件、3手4件。
奇数手末端15／偶数手末端49の両方で、手番の変換を確認できた。
差分評価と全計算、別probeでの再生・静的評価・進行度・packed成分も一致した。

| 検査 | 結果 |
| --- | --- |
| Qsearch | 64回。Searchカウンタ上は合計409ノード、最大93。詰み関数内部の全計算量の指標ではない |
| 固定末端の平均勾配、deltaゼロ | 最大有限差分誤差 `3.9432e-16` |
| 固定末端の平均勾配、式内delta `(0.25,-0.5,0.75)` | 最大誤差 `8.0715e-16` |
| メモリ上の固定末端摂動 `(0.25,-0.5,0.75)` | 最大丸め誤差0.891884cp |
| 逆向きの固定末端摂動 | 最大丸め誤差0.924454cp |

各末端の勾配も個別に確認した後、64件の平均について上表の照合を行った。
新しい6テストは、戻り値・手番の対応、非静的終端の除外、差分評価不一致の拒否、
層別64件の上限、摂動とQsearchの同時実行拒否、初期局面の空PVと角交換後の奇数PVを
確認し、成功した。既存の32関連テストも再実行して成功した（計38）。

これは少数のtrain局面での接続確認であり、1,024局面すべてのQsearch検証や
新しい評価の棋力測定ではない。過去の上限drawを正式な引き分け／勝ちへ置換していない。
Qsearchの得点・PVは今回の条件で保存した観測値で、常に同一のPVを返すという
再現性まで証明したものではない。Zobristの起動時乱数も維持している。

## 保存状態と次の段階

結果JSON：`results/learning-pilot/2026-10-11-input-validation-v1/qsearch-leaves-v1.json`。
SHA-256：`2b627a565a11ae3acfe916aa7b3a6255f815677fd6be2ba09fcd00dd1b3ffbca`。
probe SHA：`b1401e61a5e776c2df5f242bb12a8dead5de54a4d9d8c5f86c514559c60a900e`。
元manifest・分割・checkpoint・先行検証結果は変更していない。
通常バイナリ、4つのbinデータ、共通定跡の6ファイルは前後でSHA不変。
`updates: 0`、`parameter_files_written: false`、`training_ready: false` を保持した。

これで、暫定入力・固定ベース・手番の数式・整数化・固定Qsearch末端の接続までを
小規模に確認できた。次は最初のパイロットについて、歴史的教師を使う前提、
L2・学習率・float状態・保存と停止条件を具体化し、更新器の実装を独立に検証する。
非ゼロパラメータでの再探索・PV切替・optimizerによる実データ学習は未実施。
現行paramsへの採用や学習実行は自動では行わない。
