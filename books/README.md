# 新米長玉定跡

使用する定跡は [shin-yonenaga-book-v1.txt](shin-yonenaga-book-v1.txt) の1つです。
先手15局面・後手11局面を収録しています。
生成元は [shin-yonenaga-book.json](shin-yonenaga-book.json) です。

## 使用設定

OwnBookをON、BookMaxPlyを32にし、ShinBookFileに`shin-yonenaga-book-v1.txt`を指定します。
ビルド時に定跡ファイルを`bin/`へコピーします。設定の変更後はエンジンを再起動してください。

盤面・持駒・手番が一致すれば手順前後でも使用し、未登録局面は探索します。
通常定跡での補完はありません。初手▲4八玉／△6二玉はエンジン側の機能です。

## 再生成・確認

```sh
python3 tools/books/build_operational_shin_book.py --check
```

生成元を編集した場合は、`--check`を外して正式txtを再生成します。
合法性・定跡命中・適用条件は`test/books/test_operational_shin_book.py`で確認します。
