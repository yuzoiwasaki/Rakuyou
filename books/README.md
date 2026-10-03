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
| 先手▲２六歩型・７局面試験版、運用未採用 | `shin-yonenaga-black-book-pawn26-experiment.txt` | `shin-yonenaga-black-pawn26-experiment.json` |

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

## 先手試験版の比較

先手試験版は７局面、最長７手目まで。後手v2とは別ファイルで、
自動的な手番別ファイル切替はない。使う側に合わせて `ShinBookFile` を指定する。
未登録局面は探索し、玉戻りを禁止しない。運用版への採用・勝率改善は未確認。
[15局面探索・作成根拠と検証](../docs/experiments/2026-10-03-black-300-game-branch-review.md)
を参照。先手対応後に再ビルドしたエンジンが必要。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-pawn26-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-pawn26-experiment.txt
```

比較はCodex外で、プロジェクト直下から以下を実行する。
４実行は**順番に１つずつ**で、並列対局ではない。`caffeinate -i` が
終了までアイドルスリープを防ぐ。既存の同名結果がある場合は実行前に
ファイル名を変える。中断時は該当JSONを `--resume` で再開できる。

```sh
caffeinate -i bash -c '
set -e
for black_cycle_run in baseline-r1 trial-r1 trial-r2 baseline-r2; do
  if [[ -e "results/shin-black-pawn26-${black_cycle_run}-depth15-50games.json" ]]; then
    echo "Result already exists: ${black_cycle_run}; rename outputs or use --resume." >&2
    exit 1
  fi
done
for black_cycle_run in baseline-r1 trial-r1 trial-r2 baseline-r2; do
  black_cycle_extra=(--shin-book off)
  case "$black_cycle_run" in
    trial-*) black_cycle_extra=(--shin-book on --shin-book-file books/shin-yonenaga-black-book-pawn26-experiment.txt) ;;
  esac
  python3 tools/paired_selfplay.py \
    --engine bin/release --shin-side black --games 50 \
    --depth 15 --threads 1 --hash 512 --book-file bin/book.bin \
    --book-max-ply 20 --max-plies 256 --timeout 300 \
    "${black_cycle_extra[@]}" \
    --output "results/shin-black-pawn26-${black_cycle_run}-depth15-50games.json"
done
'
```

基準100局・試験100局、計200局。両方とも通常側は標準定跡ON。
対局開始前のエンジンSHA-256は
`6f7891c4957e1bf37b1e80c37ad0c9cf83f34ca974e87be05fb05dd5c1f4c2ac`、
先手試験txtは
`6218cbbcd7768ecd3c0e90aec650ec080e8a02dfcf14555e76edd23775ed00b1`。
実行中は再ビルド・定跡編集をしない。成績だけでなく、定跡到達・玉の配置・
中盤への接続を比較する。長い対局はこの作成作業では実行していない。

## 保存と整理の方針

生成元JSON・実験txt・局面定義・レポートは再検討と再現のため残す。
パスを変えずに状態を一覧化し、参照が切れる移動・削除はしない。
大きな生データはGit管理外の `results/`、局面JSONは
`docs/experiments/positions/`、レポートは `docs/experiments/` に置く。
重要な生データの圧縮・外部バックアップは別途行い、バックアップ確認前に
ローカル原本を削除しない。今回の整理では移動・削除・バックアップを行っていない。
