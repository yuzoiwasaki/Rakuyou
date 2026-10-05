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
| 先手・入口固定なし６枝版、100局完了・採用保留 | `shin-yonenaga-black-book-conditional-experiment.txt` | `shin-yonenaga-black-conditional-experiment.json` |
| 先手▲３八銀先行・４局面試験版、100局完了・採用保留 | `shin-yonenaga-black-book-silver38-experiment.txt` | `shin-yonenaga-black-silver38-experiment.json` |

## 後手第一運用版の使い方

将棋所では `ShinYonenagaGyoku` と `OwnBook` をON、`ShinBookFile` に
`books/shin-yonenaga-white-book-v2-experiment.txt`
を指定し、`BookMaxPly` は20。このパスはリポジトリ直下からの相対表記。
将棋所のファイル選択で、自分の保存先にある実ファイルを選ぶ。
未登録局面は探索へ抜ける。
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

## 先手・入口固定なし６枝版

2026-10-04、７局面版の３手目▲２六歩固定だけを外した別の試験版を作成。
残る６エントリ（着手・局面・根拠）は完全に同一。初手▲４八玉は変更せず、
`5i4h 3c3d` 後は探索へ戻る。▲７六歩などの手順前後で登録局面に合流した
場合も利用できる。未登録局面は探索し、標準定跡への補完は行わない。
運用採用・棋力改善は未確認。既存７局面版と後手v2は変更していない。

外部100局は正常終了・エラー０。１本目13勝24敗13分（39%）、
２本目24勝17敗9分（57%）、合計37勝41敗22分（48%）。
既存基準47.5%とほぼ同水準だが、実行間の差が大きく改善は未証明。
定跡利用は17局・計18手、３手目は▲７六歩93局／▲２六歩7局。
６枝版は引き続き試験版で、運用採用していない。
詳細は[先手分岐レビュー](../docs/experiments/2026-10-03-black-300-game-branch-review.md)
末尾「入口固定なし６枝版：100局の結果」を参照。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-conditional-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-conditional-experiment.txt
```

追加比較は先手固定50局×２実行、計100局。既存の基準100局（47.5%）と
７局面版100局（38.5%）を参照するが、別実行・実行間のばらつきがあるため、
僅差から改善を確定しない。定跡利用・３手目の選択・玉戻り・中盤への接続も
確認する。対局中のエンジン・定跡編集や再ビルドは行わない。

１本目（リポジトリ直下で、同名結果が存在しないことを確認してからCodex外で実行）：

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --engine bin/release --shin-side black --games 50 --shin-book on \
  --shin-book-file books/shin-yonenaga-black-book-conditional-experiment.txt \
  --depth 15 --threads 1 --hash 512 \
  --book-file bin/book.bin --book-max-ply 20 --max-plies 256 --timeout 300 \
  --output results/shin-black-conditional-r1-depth15-50games.json
```

２本目は同じ条件の新規プロセスで、出力を
`results/shin-black-conditional-r2-depth15-50games.json` に変更する。
中断した実行は新規出力で上書きせず `--resume` で再開する。
txtのSHA-256は
`e08bb43bfd6c557ff402e8407b68f72443925228080d4774c60d0e2a4f72a0f7`。
エンジンは上記の現行 `6f7891c4…` のままで、再ビルド不要。

## 先手▲３八銀先行・４局面試験版

2026-10-05作成。初手▲４八玉を維持し、△３四歩に▲３八銀、
続く△８四歩には▲７六歩、さらに△８五歩には▲２六歩。
△４二飛には▲２六歩を登録する。最長７手目までの４局面だけで、
左銀整備・飛車配置・角交換などの長いPVは固定しない。
未登録応手は探索へ抜け、標準定跡への補完や玉戻り禁止は行わない。
既存先手試験版・後手v2・評価関数は変更しない。
根の▲３八銀は４候補限定深さ28の首位より39cp低く、
△８四歩後の▲７六歩も無制限深さ28の首位より10cp低い。
構想を試す選択であり、棋力改善・運用採用は未確認。
根拠と検証は[先手分岐レビュー](../docs/experiments/2026-10-03-black-300-game-branch-review.md)末尾を参照。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-silver38-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-silver38-experiment.txt
```

外部で50局×２実行。１本目（リポジトリ直下、同名結果がないことを確認）：

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --engine bin/release --shin-side black --games 50 --shin-book on \
  --shin-book-file books/shin-yonenaga-black-book-silver38-experiment.txt \
  --depth 15 --threads 1 --hash 512 \
  --book-file bin/book.bin --book-max-ply 20 --max-plies 256 --timeout 300 \
  --output results/shin-black-silver38-r1-depth15-50games.json
```

２本目は終了確認後、同一条件の新規プロセスで出力名の `r1` を `r2` に変更。
中断時は該当出力の `--resume` で再開し、対局中に再ビルド・定跡編集をしない。
txtのSHA-256は
`6cbb021417a755d193eeb66de3cfd26575bfbaf711cb1f89382e80ed712bf0c0`。
エンジンは既存 `6f7891c4…` のままで、再ビルド不要。

100局はエラー０で完了。r1は19勝24敗7分（45%）、r2は12勝30敗8分（32%）、
合計31勝54敗15分（38.5%）。24手目の右側玉97局だが成績改善は未確認。
試験版のまま採用保留。負け筋の５局面探索では、早い角交換を見送り
▲６六歩で左側を整える候補が残ったが、該当局面は１局のみで未登録。
詳細は[先手分岐レビュー](../docs/experiments/2026-10-03-black-300-game-branch-review.md)
末尾「銀先行100局の結果と負け筋の診断」を参照。

## 保存と整理の方針

生成元JSON・実験txt・局面定義・レポートは再検討と再現のため残す。
パスを変えずに状態を一覧化し、参照が切れる移動・削除はしない。
大きな生データはGit管理外の `results/`、局面JSONは
`docs/experiments/positions/`、レポートは `docs/experiments/` に置く。
重要な生データの圧縮・外部バックアップは別途行い、バックアップ確認前に
ローカル原本を削除しない。今回の整理では移動・削除・バックアップを行っていない。
