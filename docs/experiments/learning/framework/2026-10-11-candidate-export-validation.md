# 別名候補paramsの出力・再読込とvalidation固定末端の準備

2026年10月11日。更新器の合成検証とパイロット案は `6fba59a` にコミットした。
今回は手動の検査用差分を別名のparamsに保存して再読込し、validationの基準末端を
準備した。既存棋譜による学習更新と、現行データの上書きは行っていない。

## 候補ファイルの出力

`tools/tempo_export.py` は、固定ベースのSHAとネイティブABIを確認してコピーし、
手番3係数の12バイトだけを変更する。ゼロ差分は全byte一致を保つ。
手番第4成分、進行度、駒価値、KP/PP、その他すべての評価成分はそのまま保存する。

- 差分は有限の3数値、各±5cp以内。整数差分は `trunc(delta_cp*65536)` とし、
  ベースのraw値へ加算する。最終int32のoverflowを拒否する。
- ファイルサイズ、packed値、ネイティブ読込値からABIとbyte orderを検査する。
  現環境ではlittle endian、手番offset259336896、全体259336912byte。
- 保存先が元ファイルと同じ場合、既存ファイルの場合、`bin/` 配下の場合は拒否する。
  新規保存後もベースのSHAが変わっていないことを確認する。
- 変更を許す12バイト以外の全領域をhash照合し、第4成分までpacked値を検査する。

`tools/check_tempo_export.py` は、手動差分 `(0.25,-0.5,0.75)` を保存し、
既存train64固定末端でネイティブprobeから再読込する。
元データをメモリ上で同じraw値だけ摂動した結果と、再読込結果を比較する。
学習を行って得た差分ではなく、候補を選択・採用する検査でもない。

```sh
python3 -m unittest discover -s test -p test_tempo_export.py -v
python3 tools/check_tempo_export.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  results/learning-pilot/2026-10-11-input-validation-v1/qsearch-leaves-v1.json \
  --output results/learning-pilot/2026-10-11-candidate-export-v1
```

手番raw値は `[-163745,653365,-1105013,0]` から
`[-147361,620597,-1055861,0]` となった。
再読込は64固定末端および途中局面で、メモリ上摂動のON/OFF評価・進行度・packed値と
完全一致した。手番以外の全領域も一致し、最大丸め誤差は0.891884cpだった。
新しい5テストが、全領域保持、ゼロ差分、上書き・同一保存先の拒否、
異常差分／ベースSHAの拒否、int32 overflowの拒否を確認して成功した。

| 成果物 | SHA-256 |
| --- | --- |
| `results/learning-pilot/2026-10-11-candidate-export-v1/params-manual-delta.bin` | `a40d46be79422ded9021e700704be58c54f86a4aba25253c3ec01e18af405baf` |
| 同ディレクトリの `validation.json` | `0053bb1d925b2861606226e1f066c10ea0c0e81afe9982c8abbb0d356fd0bd1a` |
| 変更しない領域のSHA | `71bfb53f862c67896921726d9edb7404729c381804dbfb42aa5698df186b121a` |

## validationの固定末端

`check_qsearch_leaves.py` にtrain／validationの明示選択とprepare-onlyを追加した。
validationを選ぶと常にprepare-onlyとし、教師との損失・勾配・摂動検査を実行しない。
testを選ぶ入口は設けていない。

```sh
python3 tools/check_qsearch_leaves.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  --split validation --prepare-only \
  --output results/learning-pilot/2026-10-11-input-validation-v1/validation-leaves-v1.json
```

基準paramsで選んだvalidation64ルートの末端はすべて静的評価と対応し、除外0。
先手33／後手31、PV長0手44・1手10・2手7・3手3、奇数末端13／偶数末端51。
上限draw由来21件、うち後手10件を保持した。
Searchカウンタ上の静止探索ノードは合計283（詰み関数内部の全計算量ではない）。
損失・勾配・摂動の結果配列は空で、モデル選択を行っていない。
既存Qsearch検証の6テストも再実行して成功した。

train64とvalidation64について、runの集合、ルートSFENの集合、固定末端SFENの集合が
互いに重ならないことを別途照合した。より一般的な相関や長い共通手順の問題が
解消したという意味ではなく、元manifestの制約を維持する。
validationキャッシュSHA：
`d1632112165cc73f635e0db854e4d4a90292e7d9b72488c180859aa603956af4`。

## 保存状態と次の作業

[パイロット設定](../../configs/tempo-pilot-v1.json) にvalidationキャッシュと候補出力検査の
SHAを追加した。実学習・採用フラグはfalse、更新器設定は変更していない。
通常バイナリ、4つのbinデータ、共通定跡は前後でSHA不変。
元manifest、JSONL、過去のtrain固定末端、checkpoint、先行結果も上書きしていない。
testの教師品質は測定しておらず、L2／学習率をvalidationに合わせて変更していない。
外部バックアップは未実施。

次は入力・設定・固定末端・候補保存を結ぶ実験runnerのdry-runと、
検証済みの独立バックアップを完成させる。実データの最大20更新を行う入口は
まだ実行していない。手動候補の棋力や通常運用への採用は本検査の結論に含めない。
