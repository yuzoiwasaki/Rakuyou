# 試験用定跡

[定跡一覧へ戻る](../README.md)

| 候補 | 生成元 | 生成txt |
| --- | --- | --- |
| 先手▲３六歩追加 | [JSON](black/shin-yonenaga-black-pawn76-right-side-pawn36-experiment.json) | [7局面txt](black/shin-yonenaga-black-book-pawn76-right-side-pawn36-experiment.txt) |
| 先手旧▲２五歩構想 | [JSON](black/shin-yonenaga-black-silver38-silver32-pawn25-experiment.json) | [6局面txt](black/shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt) |
| 後手△２五歩追加 | [JSON](white/shin-yonenaga-white-v2-pawn25-experiment.json) | [12局面txt](white/shin-yonenaga-white-book-v2-pawn25-experiment.txt) |
| 後手７筋構想 | [JSON](white/shin-yonenaga-white-seventh-edge-experiment.json) | [13局面txt](white/shin-yonenaga-white-book-seventh-edge-experiment.txt) |

これらの候補は共通v1とは別の定跡ファイル。

再生成は `tools/books/build_shin_book.py` にJSONと出力txtを明示する。
先手の単独試験版は `--side black --experimental`、後手７筋版は `--experimental`。
後手△２五歩版は `books/sources/white/shin-yonenaga-white-candidates.json` を
`--source`、上表の追加JSONを `--extension` に指定する。
比較根拠は [先手レポート](../../docs/experiments/books/black/README.md)、
[後手レポート](../../docs/experiments/books/white/README.md)を参照する。
