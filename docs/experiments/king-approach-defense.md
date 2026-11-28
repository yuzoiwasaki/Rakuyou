# 玉の前方の侵入口を塞ぐ評価の試作

## 状態と目的

`experiment/king-approach-defense` の検証用試作。基点は採用済みmain `5ecd314`。PR #14の定跡２局面は含めず、定跡は94局面のまま変更していない。新項目の既定値は0（無効）。今回の結果では採用を推奨しない。

目的は、相手の攻めが玉の隣まで届く前に侵入口を塞ぐ受けを評価すること。攻め手や特定の歩突きは禁止しない。局面固有の手を加点しない。

## 第１試作の定義

玉から前方２段・左右２筋の５マスと、前方１段・左右２筋の２マス、計７マスを調べる。隣接８マスは既存補正と重なるため除外する。盤外は除外し、先後では前方を反転する。

- 相手の現在の利きがないマスは数えない。
- 味方の駒があり、味方の利き数が相手の利き数以上なら、塞がっているものとして数えない。
- その他は `1 + max(0, 相手の利き数 − 味方の利き数)` を危険度とする。利き数は各３、片側の総危険度は８で打ち切る。
- 先後の危険度の差に係数を掛ける。終盤になるほど減衰させる。既存の玉の安全度の合計に加え、全評価・差分更新・巻き戻しで同じ計算を使う。

開発・比較用ビルドの `ExperimentalKingApproachPenalty` で0〜40を設定する。新しい探索を開始する前に指定する。通常版では公開せず、変更要求も無視する。

これは幾何的な近似であり、合法な侵入手、駒打ちの可能性、ピン、交換後の守備、詰みを直接判定しない。未攻撃の穴を事前に塞ぐ価値も対象外。玉が移動すると測定範囲が変わるため、玉移動への副作用は今後の確認が必要。

## 検証例

対象は2026-11-28の後手実戦の50手目。△８六歩に対して、△６四歩打または△４三金で受ける形を検討した局面。

新項目の追加前は、既存の歩・金銀連結補正が３候補でほぼ同じ、玉の隣接利き不足補正も全候補で0だった。本試作では△６四歩打で後手危険度が1→0になる。係数20ではその直後の後手評価への寄与が約13点改善する。△８六歩・△４三金の直後は危険度が変わらない。この静的な反応だけで指し手改善を証明するものではない。

### 同一深さ18・MultiPV3

各候補は新しいプロセス、1スレッド、512MB、定跡OFF。値は後手視点。

| 係数 | 第１候補 | 評価 | △６四歩打の評価 |
| --- | --- | ---: | ---: |
| 0 | △６四歩打 | −115 | −115 |
| 10 | △８六歩 | −108 | −193 |
| 20 | △８六歩 | −157 | −216 |
| 40 | △６四歩打 | −163 | −163 |

係数を上げても受けを選ぶ効果は単調ではない。別評価で得られた評価値自体の大小を、棋力の比較には使わない。

### １手２秒・12手の指し継ぎ

同じ49手目までを初期履歴とし、先手は通常評価、後手だけを0/20/40で比較。全候補で50手目は△６四歩打だった。その後は異なり、実験版が受けの形を改善したとは確認できなかった。係数40では52手目に△８六歩へ戻った。全着手をネイティブ合法手で確認し、四回同一局面なら止める。今回は全て12手上限で未決着。

通常評価の再探索でも受けを選んだので、元の実戦との違いには探索履歴・時間も関係する。１局面を希望手に合わせるため係数を増やし続けない。

### 対照例と実装検査

- 先手の応手、必要な角の取り返し、端の桂攻め、終盤の攻めも確認。取り返し・桂攻め・終盤の第１候補は0/20/40で同じだった。ただし対照は少数であり、棋力維持の証明ではない。
- 136局面を４係数で検査。各入力の全手順で全評価と差分更新、巻き戻し、合法なnull move、180度回転と先後交換を確認。
- 支えのある歩で侵入口が塞がる例、攻めの利きがない例を先後両方で確認。
- 係数0の静的評価は既存基準と一致。５局面の深さ12の指し手・評価・PVは凍結mainと一致。
- 通常版は新項目を非表示にし、40を指定しても係数0の比較版と一致。
- 100万ノード指定を0/20各３回で比較したNPS中央値は約107万/105万。今回の小さな測定で約1.7%低下。実ノード数は停止検査間隔で指定値を超えるため、実ノード数と時間から算出した。一般的な速度保証ではない。

## 再現

評価データ、OpenMPライブラリは通常の開発手順に従って用意する。実行用データとライブラリへのリンクを作成し、普段使う実行ファイルとは別にビルドする。

```sh
mkdir -p results/king-approach-experiment/runtime/bin
ln -s "$PWD/lib" results/king-approach-experiment/runtime/lib
for data in params.bin progress.bin probability.bin book.bin; do
  ln -s "$PWD/bin/$data" "results/king-approach-experiment/runtime/bin/$data"
done
make match -j2 output_file=results/king-approach-experiment/runtime/bin/match
make release -j2 output_file=results/king-approach-experiment/runtime/bin/release
make king-approach-test -j2
python3 -m unittest test.analysis.test_king_approach
python3 tools/analysis/king_approach_experiment.py --mode fixed --output results/king-approach-experiment/fixed.json
python3 tools/analysis/king_approach_experiment.py --mode scan --output results/king-approach-experiment/scan.json
python3 tools/analysis/king_approach_experiment.py --mode rollout --output results/king-approach-experiment/rollouts.json
python3 tools/analysis/king_approach_experiment.py --mode speed --output results/king-approach-experiment/speed.json
```

`--mode baseline --baseline <凍結mainの実行ファイル> --output <出力>` で係数0の探索一致を確認できる。入力は `test/analysis/king_approach_positions.json`、詳細出力はGit管理外の `results/king-approach-experiment/`。

## 判断

項目の機械的な反応と実装の整合性は確認できたが、望む受け将棋への安定した変化は未確認。既定値0の実験として保持する。次の仮説を試すなら、単なる空きマスの利き数よりも、その侵入によって守備駒の交換や分断が起きるかを調べ、異なる複数局面で同じ傾向を確かめたい。
