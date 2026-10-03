# 新米長玉定跡の運用・実験一覧

2026-10-03時点の後手第一運用版は **v2の既存11局面**。
ファイル名に `experiment` が残るが、現在の運用対象は
`shin-yonenaga-white-book-v2-experiment.txt`。名称・内容は変えず、
過去の結果・コマンド・テストとの対応を保持する。
運用採用は勝ち越しや他候補への棋力優越の証明ではない。

| 用途・状態 | エンジンに指定するファイル | 生成元 |
|---|---|---|
| 後手第一運用版 | `shin-yonenaga-white-book-v2-experiment.txt` | v1候補＋`shin-yonenaga-white-v2-experiment.json` |
| 過去の比較基準v1 | `shin-yonenaga-white-book.txt` | `shin-yonenaga-white-candidates.json` |
| △２五歩一局面追加・保留 | `shin-yonenaga-white-book-v2-pawn25-experiment.txt` | v1候補＋`shin-yonenaga-white-v2-pawn25-experiment.json` |
| ７筋構想・運用不採用、構想は条件付きで保留 | `shin-yonenaga-white-book-seventh-edge-experiment.txt` | `shin-yonenaga-white-seventh-edge-experiment.json` |
| 先手専用定跡 | 未作成 | [着手方針](../docs/experiments/2026-10-03-black-book-start-plan.md) |

## 後手第一運用版の使い方

将棋所では `ShinYonenagaGyoku` と `OwnBook` をON、`ShinBookFile` に
`/Users/yuzo.iwasaki/Rakuyou/books/shin-yonenaga-white-book-v2-experiment.txt`
を指定し、`BookMaxPly` は20。未登録局面は探索へ抜ける。
`BookFile` の `book.bin` は通常側の標準定跡用であり、新米長玉側の
専用定跡に穴があるときの補完としては使われない。
後手用定跡なので、先手の新米長玉専用枝は含まない。

対象は主に対標準定跡・先手四間飛車。
別戦型・時間制・独立した技巧との対局による全面的な検証は未完了。
[採用判断と200局の結果](../docs/experiments/2026-10-03-v2-bounded-white-improvement-cycle.md)
を参照。

内容を再生成する場合（プロジェクト直下、採用ファイルへの書込み）：

```sh
python3 tools/build_shin_book.py \
  --extension books/shin-yonenaga-white-v2-experiment.json \
  --output books/shin-yonenaga-white-book-v2-experiment.txt
```

採用txtのSHA-256：
`28e59ec12cb86ada7280687d130e29bdb28eb0d550840d634c73e003aa2ffc62`。

## 保存と整理の方針

生成元JSON・実験txt・局面定義・レポートは再検討と再現のため残す。
パスを変えずに状態を一覧化し、参照が切れる移動・削除はしない。
大きな生データはGit管理外の `results/`、局面JSONは
`docs/experiments/positions/`、レポートは `docs/experiments/` に置く。
重要な生データの圧縮・外部バックアップは別途行い、バックアップ確認前に
ローカル原本を削除しない。今回の整理では移動・削除・バックアップを行っていない。
