# 現行定跡の生成元

[定跡一覧へ戻る](../README.md)

| 対象 | JSON |
| --- | --- |
| 先手6局面 | [▲７六歩・右側構想](black/shin-yonenaga-black-pawn76-right-side-experiment.json) |
| 後手の基礎候補 | [後手v1候補](white/shin-yonenaga-white-candidates.json) |
| 後手v2の追加2局面 | [後手v2追加](white/shin-yonenaga-white-v2-experiment.json) |

後手v2は、基礎候補の採用済みエントリと追加2局面から生成する。

単独版を再生成する場合は、リポジトリ直下で明示的に出力する。
次のコマンドは既存の現行txtへ書き込む。

```sh
python3 tools/books/build_shin_book.py --side black --experimental \
  --source books/sources/black/shin-yonenaga-black-pawn76-right-side-experiment.json \
  --output books/shin-yonenaga-black-book-pawn76-right-side-experiment.txt
python3 tools/books/build_shin_book.py \
  --source books/sources/white/shin-yonenaga-white-candidates.json \
  --extension books/sources/white/shin-yonenaga-white-v2-experiment.json \
  --output books/shin-yonenaga-white-book-v2-experiment.txt
```

通常の確認には `python3 tools/books/build_operational_shin_book.py --check` を使用する。
