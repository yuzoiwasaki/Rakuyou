# Apple Silicon Mac での開発手順

技巧は SSE 4.2 前提のため、Apple Silicon では x86_64 (Rosetta) でビルドします。
初回のみ OpenMP ランタイムのビルドが必要です（cmake が必要です: `brew install cmake`）。

```sh
cd Rakuyou
make libomp-x86_64   # 初回のみ
make release
```

実行ファイルは `bin/release` です。将棋所等で使う場合は、
[Releases](https://github.com/gikou-official/Gikou/releases) の Windows 版 zip から
`params.bin` 等のデータファイルを `bin/` にコピーしてください（`gikou.exe` は不要）。

## 学習準備の検証ツール

`make learning-probe -j2` は通常エンジンとは別に
`results/learning-tools/learning-data-probe` をビルドします。
`obj/learning-probe/` を使い、`bin/release` を置き換えません。
既定の再生・静的評価モードは探索・学習を実行せず、既存の盤面・合法手判定・
Huffman処理でUSI着手列を検証します。`--layout` は対象ABIを表示します。
明示的な `--qsearch` モードだけは接続検査用の静止探索を行います。
どのモードにも学習更新・評価ファイル保存機能はありません。

```sh
make learning-probe -j2
python3 -m unittest discover -s test -p test_prepare_learning_data.py -v
python3 tools/prepare_learning_data.py \
  --output results/learning-pilot/my-preparation-001
```

出力先は存在しない新しいディレクトリを指定します。入力は既定で
`results/*.json` の自己対局データ、個別ファイルの指定も可能です。
暫定train/validation/testのJSONL、入力SHAと除外理由を記録するmanifest、
ゼロ差分の評価データコピーを保存します。引き分け局の探索教師は保持し、
手数上限drawの勝敗損失には無効フラグを付けます。

過去の各runの実行時データの由来確認が済むまでは `training_ready: false` です。
`*.provisional.jsonl` を学習確定集合として扱わないでください。
現在の入口には学習・パラメータ更新機能はありません。
計画と制限は[学習調査・実験案](experiments/2026-10-11-learning-feasibility-plan.md)を参照。

準備済みJSONLを元棋譜と照合し、全局面を更新なしで検証する入口：

```sh
python3 tools/validate_learning_input.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  --output results/learning-pilot/my-input-validation-001
```

これは教師の評価精度・損失・勾配を測定せず、入力、合法性、固定ベース、
ゼロ差分コピーの評価／進行度一致を確認します。`--checkpoint` で読む状態も
更新回数0・手番3係数のゼロ差分に限定されます。出力先は新規ディレクトリのみです。
検証後も暫定集合の `training_ready` はfalseのままです。

静止探索の固定末端を、trainから64局面に限って検証する入口：

```sh
python3 tools/check_qsearch_leaves.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  --output results/learning-pilot/my-qsearch-leaves-001.json
```

paramsとprogressの重み一致を確認し、ON・1スレッド相当・深さ0・局面ごと空のTTで
検索します。Qsearchで求めた末端は固定し、手番を摂動した後の再探索は行いません。
既存ファイルの上書きは拒否し、元データと定跡を保持します。
