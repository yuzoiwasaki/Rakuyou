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
このツールは探索・学習を実行せず、既存の盤面・合法手判定・Huffman処理で
USI着手列を検証します。`--layout` は対象ビルドのバイナリ構造を表示します。

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
