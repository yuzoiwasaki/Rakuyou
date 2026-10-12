# 旧定跡系列の生成元

[定跡一覧へ戻る](../README.md)

旧系列の生成元JSONと、対応する生成txtの名称。

| 生成txt名 | 生成元JSON |
| --- | --- |
| `shin-yonenaga-black-book-pawn26-experiment.txt` | [▲２六歩7局面](black/shin-yonenaga-black-pawn26-experiment.json) |
| `shin-yonenaga-black-book-conditional-experiment.txt` | [入口固定なし6枝](black/shin-yonenaga-black-conditional-experiment.json) |
| `shin-yonenaga-black-book-silver38-experiment.txt` | [▲３八銀4局面](black/shin-yonenaga-black-silver38-experiment.json) |
| `shin-yonenaga-black-book-silver38-silver32-experiment.txt` | [▲３九玉追加5局面](black/shin-yonenaga-black-silver38-silver32-experiment.json) |
| `shin-yonenaga-black-book-silver38-silver32-pawn76-experiment.txt` | [旧系列▲７六歩追加6局面](black/shin-yonenaga-black-silver38-silver32-pawn76-experiment.json) |
| `shin-yonenaga-black-book-silver38-silver32-pawn25-silver68-experiment.txt` | [▲６八銀追加7局面](black/shin-yonenaga-black-silver38-silver32-pawn25-silver68-experiment.json) |
| `shin-yonenaga-white-book.txt` | [後手v1候補](../sources/white/shin-yonenaga-white-candidates.json) |

先手▲２六歩版を別名出力へ生成する例（リポジトリ直下）：

```sh
mkdir -p results/book-tools
python3 tools/books/build_shin_book.py --side black --experimental \
  --source books/archive/black/shin-yonenaga-black-pawn26-experiment.json \
  --output results/book-tools/black-pawn26.txt
```

後手v1の再生成は `--source books/sources/white/shin-yonenaga-white-candidates.json` と
別名の `--output` を指定する（`--experimental` は付けない）。

実験の経緯は [先手レポート](../../docs/experiments/books/black/README.md)と
[後手レポート](../../docs/experiments/books/white/README.md)を参照。
