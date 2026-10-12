# 終了した定跡系列の生成元

[現行定跡へ戻る](../README.md)

現行運用と保留候補の使用に不要な生成txt7ファイルを削除した。
元JSON・登録手・実験レポート・生データは保持する。
以下は削除したtxtの名称と、同じ内容を再生成する入力。

| 削除した生成txt | 保持する生成元JSON |
| --- | --- |
| `shin-yonenaga-black-book-pawn26-experiment.txt` | [▲２六歩7局面](black/shin-yonenaga-black-pawn26-experiment.json) |
| `shin-yonenaga-black-book-conditional-experiment.txt` | [入口固定なし6枝](black/shin-yonenaga-black-conditional-experiment.json) |
| `shin-yonenaga-black-book-silver38-experiment.txt` | [▲３八銀4局面](black/shin-yonenaga-black-silver38-experiment.json) |
| `shin-yonenaga-black-book-silver38-silver32-experiment.txt` | [▲３九玉追加5局面](black/shin-yonenaga-black-silver38-silver32-experiment.json) |
| `shin-yonenaga-black-book-silver38-silver32-pawn76-experiment.txt` | [旧系列▲７六歩追加6局面](black/shin-yonenaga-black-silver38-silver32-pawn76-experiment.json) |
| `shin-yonenaga-black-book-silver38-silver32-pawn25-silver68-experiment.txt` | [▲６八銀追加7局面](black/shin-yonenaga-black-silver38-silver32-pawn25-silver68-experiment.json) |
| `shin-yonenaga-white-book.txt` | [現行v2にも必要な後手v1候補](../sources/white/shin-yonenaga-white-candidates.json) |

必要になった場合だけ、リポジトリ直下から別名出力へ再生成する。
次は先手▲２六歩版の例で、現行ファイルを上書きしない。

```sh
mkdir -p results/book-tools
python3 tools/build_shin_book.py --side black --experimental \
  --source books/archive/black/shin-yonenaga-black-pawn26-experiment.json \
  --output results/book-tools/black-pawn26.txt
```

後手v1の再生成は `--source books/sources/white/shin-yonenaga-white-candidates.json` と
別名の `--output` を指定する（`--experimental` は付けない）。
回帰テストでは一時ディレクトリへ生成し、削除前のSHAとの一致も確認する。
以前のコミット `12b41d0` には削除した7ファイルの元内容が残っている。

過去レポートの生成・対局コマンドと、生データ／監査JSONの旧txtパスは当時の履歴である。
この案内へ変更した旧txtのリンクは、その削除と復元方法を示す。
過去の長いコマンド履歴を現行READMEへ再掲せず、
[先手レポート](../../docs/experiments/books/black/README.md)と
[後手レポート](../../docs/experiments/books/white/README.md)から参照する。
