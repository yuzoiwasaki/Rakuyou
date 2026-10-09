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
| 先手銀先行・△３二銀に▲３九玉を追加した５局面版、200局比較完了・採用保留 | `shin-yonenaga-black-book-silver38-silver32-experiment.txt` | `shin-yonenaga-black-silver38-silver32-experiment.json` |
| 先手銀先行・頻出17手目▲７六歩を追加した６局面版、200局比較完了・採用保留 | `shin-yonenaga-black-book-silver38-silver32-pawn76-experiment.txt` | `shin-yonenaga-black-silver38-silver32-pawn76-experiment.json` |
| 先手▲２五歩６局面版、暫定運用候補・独立レビュー待ち | `shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt` | `shin-yonenaga-black-silver38-silver32-pawn25-experiment.json` |
| 先手15手目▲６八銀追加７局面版、200局比較完了・採用保留 | `shin-yonenaga-black-book-silver38-silver32-pawn25-silver68-experiment.txt` | `shin-yonenaga-black-silver38-silver32-pawn25-silver68-experiment.json` |

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

## 銀先行５局面版：△３二銀に▲３九玉の１枝追加

原版４エントリ（根拠を含む）を変更せず、
`5i4h 3c3d 3i3h 3a3b | 4h3i` だけを追加した別の試験版。
原版・後手v2・エンジン・評価補正・BookMaxPly20は変更なし。
▲３九玉後は探索に任せる。角交換対策の▲６六歩や△３二飛への枝は追加しない。
深さ24／26で▲３九玉が首位だったが、勝率改善・運用採用は未確認。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-silver38-silver32-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-silver38-silver32-experiment.txt
```

比較は50局×４実行、**原版→改訂版→改訂版→原版**の順で計200局を完了。
並列にはせず１本ずつ、原版・改訂版各100局を新規プロセス２回で測る。
出力の識別子は `baseline-r1`、`trial-r1`、`trial-r2`、`baseline-r2`。
過去の原版38.5%だけを対照にせず、今回の原版も参照する。
同一乱数で対にした比較ではなく、勝率小差の因果効果は断定しない。

以下は完了済みの最初の原版50局のコマンド履歴。再実行時は出力名を変える：

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --engine bin/release --shin-side black --games 50 --shin-book on \
  --shin-book-file books/shin-yonenaga-black-book-silver38-experiment.txt \
  --depth 15 --threads 1 --hash 512 \
  --book-file bin/book.bin --book-max-ply 20 --max-plies 256 --timeout 300 \
  --output results/shin-black-silver38-silver32-baseline-r1-depth15-50games.json
```

２・３本目は改訂txt `shin-yonenaga-black-book-silver38-silver32-experiment.txt` を指定し、
出力末尾の `baseline-r1` を `trial-r1`／`trial-r2` に変更。
４本目は原版txtで出力を `baseline-r2` にする。
終了確認後に次の１本へ進む。中断時は同名JSONの `--resume` で再開する。
対局中は再ビルド・定跡編集をしない。再ビルドは不要。
改訂txtのSHA-256：
`42622adc1fb4cc479bd70af352e296b4b5fa413f91ccad9ea4fc161866ea5a17`。
41回帰テスト成功。比較の判定項目は[先手レポート](../docs/experiments/2026-10-03-black-300-game-branch-review.md)末尾参照。

2026-10-06の結果は原版100局45.5%、５局面版100局39%。
△３二銀群は原版19局39.5%、５局面版23局60.9%だが、非対象群も大きく異なる。
全体差・小群差を追加手の因果効果とせず、５局面版の運用採用は保留。
次の比較では、この５局面版を変更せず対照として使用する。

## 銀先行６局面版：頻出17手目▲７六歩の１枝追加

５局面版の全エントリを根拠・注記ごと保持し、次の１組だけを追加した別の試験版。

```text
5i4h 3c3d 3i3h 8b4b 2g2f 5a6b 9g9f 9c9d
5g5f 3a3b 7i6h 7a7b 6h5g 6b7a 4h3i 4c4d | 7g7f
```

無制限深さ24／26で首位、深さ26では▲８六歩との差９cp。
勝率改善は未証明。19手目▲８六歩、金整備の固定手順、長いPVは追加しない。
未登録局面は探索へ抜け、標準定跡の補完なし。玉戻り禁止・補正変更もなし。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-silver38-silver32-pawn76-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-silver38-silver32-pawn76-experiment.txt
```

45回帰テスト成功、５エントリ保持・生成一致・全６組読み込み・手順前後・
19手目の探索・対照版17手目の探索・OwnBook OFF・BookMaxPly16／17境界を確認。
txtのSHA-256：`284850ec7495a4d1889c79d393fe75e775cc56dc3cfe7b7ec7af2b0df1b9c299`。
再ビルドは不要。旧txt・後手v2・エンジンは変更しない。

外部比較案は50局×４、新規プロセスで順番に
**５局面版→６局面版→６局面版→５局面版**。各版計100局、計200局。
出力は `results/shin-black-silver38-pawn76-<識別子>-depth15-50games.json`、
識別子は `baseline-r1`／`trial-r1`／`trial-r2`／`baseline-r2`。
同一乱数の対応比較ではない。登録対象の到達・原版で同じ手を選んだ数・
手順前後・右側の玉・後続接続を確認し、曖昧なら採用保留で区切る。

以下は完了済みの対照５局面版50局のコマンド履歴。再実行時は出力名を変える：

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --engine bin/release --shin-side black --games 50 --shin-book on \
  --shin-book-file books/shin-yonenaga-black-book-silver38-silver32-experiment.txt \
  --depth 15 --threads 1 --hash 512 \
  --book-file bin/book.bin --book-max-ply 20 --max-plies 256 --timeout 300 \
  --output results/shin-black-silver38-pawn76-baseline-r1-depth15-50games.json
```

２・３本目は６局面txt `shin-yonenaga-black-book-silver38-silver32-pawn76-experiment.txt`、
出力を `trial-r1`／`trial-r2` に変更。４本目は５局面txt、出力 `baseline-r2`。
１本ごとに完了確認し、並列実行・対局中の再ビルド／定跡変更をしない。
中断時は同名JSONの `--resume` で再開する。準備段階では追加対局未実施。

2026-10-07に全200局が完了、エラー０。
５局面版は44%／49%、合計40勝47敗13分（46.5%）。
６局面版は39%／45%、合計35勝51敗14分（42%）。
追加枝は６局面版で３局１勝１敗１分、対照で１局（探索で同じ▲７六歩を選び勝ち）。
低到達と実行差のため効果は未確認、６局面版は運用採用保留で比較を区切る。
同じ枝の追加100局は行わず、試験版・探索根拠を保存する。
５局面版も運用採用ではなく、次に調べるなら対△８四歩の既存負け棋譜を優先する。

## 対△８四歩６局面版：13手目▲２五歩の１枝追加

既存５局面版を根拠・注記ごと保持し、次の１組だけを追加した別の試験版。
前の17手目▲７六歩追加は含まない。試験用で、運用採用や棋力改善の証明ではない。

```text
5i4h 3c3d 3i3h 8c8d 7g7f 8d8e 2g2f 8e8f
8g8f 8b8f 6i7h 4c4d | 2f2e
```

▲２五歩は無制限深さ24で首位、４候補限定深さ26でも首位−119cp。
限定26内では▲６八銀と22cp差、▲２七銀／▲３九玉と70cp差。
無制限深さ26の最善手とは扱わない。15手目の左銀整備・▲２九飛などは固定せず探索へ任せる。
BookMaxPly20・補正25cp・玉戻りの合法性は変更なし。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-silver38-silver32-pawn25-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt
```

50回帰テスト成功。５組保持・生成一致・全６組利用・手順前後・15手目の探索・
OwnBook OFF・BookMaxPly12／13境界・17手目▲７六歩追加が混在しないことを確認。
txtのSHA-256：`52123e92c55e0dc33f1f77849daf481879f00dffb6e68c4831e93534a9a531c7`。
エンジン・旧txt・後手v2は変更なし、再ビルド不要。

比較案は新規プロセス50局×４、順に
**５局面版→▲２五歩６局面版→▲２五歩６局面版→５局面版**、各版100局・計200局。
出力は `results/shin-black-silver38-pawn25-<識別子>-depth15-50games.json`。
識別子は `baseline-r1`／`trial-r1`／`trial-r2`／`baseline-r2`。
過去の５局面版46.5%だけを対照にせず、今回の再計測を含める。

以下は完了済みの対照５局面版50局のコマンド履歴。再実行時は出力名を変える：

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --engine bin/release --shin-side black --games 50 --shin-book on \
  --shin-book-file books/shin-yonenaga-black-book-silver38-silver32-experiment.txt \
  --depth 15 --threads 1 --hash 512 \
  --book-file bin/book.bin --book-max-ply 20 --max-plies 256 --timeout 300 \
  --output results/shin-black-silver38-pawn25-baseline-r1-depth15-50games.json
```

２・３本目は `shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt`、
出力を `trial-r1`／`trial-r2`。４本目は５局面txt、出力 `baseline-r2`。
並列実行せず１本ごとに確認し、対局中の定跡変更・再ビルドをしない。
同一乱数の対応比較ではないため、実行差・対象／非対象群・玉配置・駒組みを分けて判定。
僅差や低到達で曖昧なら採用保留で比較を区切る。準備段階では対局未実施。

2026-10-08に全200局を確認、エラー０。
対照は45%／35%、合計29勝49敗22分、試験は39%／41%、合計32勝52敗16分。
全体の得点率は両版40%。対象群は対照15局５勝10敗、試験13局６勝６敗１分。
有望な観察結果は残るが改善の因果効果は未確定で、運用採用保留で比較を区切る。
試験13局の15手目▲６八銀は１局のみで、左銀整備・▲２九飛の後続は未保証。
同じ枝の追加100局ではなく、15手目の１局面診断を次の検証とする。

## ▲２五歩～▲６八銀７局面版：最後の接続比較

▲２五歩６局面版を根拠・注記ごと保持し、次の１組だけを追加。
構想誘導と棋力の試験で、運用採用・勝率改善の証明ではない。

```text
5i4h 3c3d 3i3h 8c8d 7g7f 8d8e 2g2f 8e8f 8g8f 8b8f
6i7h 4c4d 2f2e 2b3c | 7i6h
```

▲６八銀は無制限24・３候補限定26で首位だが、無制限24の▲２六飛との差は17cp。
▲７七銀・▲２九飛の後続は固定せず、別の応手も探索へ任せる。
保留中の17手目▲７六歩は含めない。BookMaxPly20・補正25cp・玉戻りの合法性は変更なし。

再生成：

```sh
python3 tools/build_shin_book.py --side black \
  --source books/shin-yonenaga-black-silver38-silver32-pawn25-silver68-experiment.json --experimental \
  --output books/shin-yonenaga-black-book-silver38-silver32-pawn25-silver68-experiment.txt
```

56回帰テスト成功。６組保持・全７組利用・手順前後・17手目と別応手の探索・
対照15手目の探索・OwnBook OFF・BookMaxPly14／15境界を確認。
新txt SHA-256：`1fb65e90a39cd882e7689e28c5a9cbcba33775c4a2fd712cabf5f71db2ab67a9`。
旧txt・エンジン・後手v2は変更なし、再ビルド不要。

比較は新規プロセス50局×４、**６局面→７局面→７局面→６局面**、各100局・計200局。
出力は `results/shin-black-silver38-pawn25-silver68-<識別子>-depth15-50games.json`、
識別子 `baseline-r1`／`trial-r1`／`trial-r2`／`baseline-r2`。
以下は完了済みの対照６局面版50局のコマンド履歴。再実行時は出力名を変える：

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --engine bin/release --shin-side black --games 50 --shin-book on \
  --shin-book-file books/shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt \
  --depth 15 --threads 1 --hash 512 \
  --book-file bin/book.bin --book-max-ply 20 --max-plies 256 --timeout 300 \
  --output results/shin-black-silver38-pawn25-silver68-baseline-r1-depth15-50games.json
```

２・３本目は `shin-yonenaga-black-book-silver38-silver32-pawn25-silver68-experiment.txt`、
出力 `trial-r1`／`trial-r2`。４本目は６局面txt、出力 `baseline-r2`。
並列実行・対局中の定跡変更や再ビルドはせず、１本ごとに確認する。
実行差・対象／非対象群、左銀整備・右側の玉・中盤接続を成績と分けて判定。
結果が曖昧でもこの系列はいったん区切り、先手の暫定運用版を選ぶ。
勝ち越しまで同じ対局・枝追加・深さ拡張を続けない。準備段階で対局未実施。

2026-10-10に全200局を確認、エラー０。６局面版44%／29%、合計26勝53敗21分（36.5%）、
７局面版42%／24%、合計26勝60敗14分（33%）。
追加枝の対象は対照18局５勝12敗１分、試験26局６勝18敗２分。
対照も15／18局で探索から▲６八銀を選んだ。
試験では左銀整備・右側の玉・▲２九飛を概ね実現したが、対照も同様の形へ進み、
追加利益は未確認。７局面版は採用保留で、この系列を区切る。
▲２五歩６局面版を構想上の暫定運用候補とし、独立レビューで再確認する。
棋力優越・勝ち越し・採用確定とは扱わず、エンジンの自動選択も変更しない。

## 保存と整理の方針

生成元JSON・実験txt・局面定義・レポートは再検討と再現のため残す。
パスを変えずに状態を一覧化し、参照が切れる移動・削除はしない。
大きな生データはGit管理外の `results/`、局面JSONは
`docs/experiments/positions/`、レポートは `docs/experiments/` に置く。
重要な生データの圧縮・外部バックアップは別途行い、バックアップ確認前に
ローカル原本を削除しない。今回の整理では移動・削除・バックアップを行っていない。
