# 手番学習候補の通常探索比較：分離環境と12局面の準備

2026年10月11日、ソース基準 `e9e74b2`。
[再静止探索確認](2026-10-11-selected-tempo-qsearch-review.md)の次段階として、
同じ通常バイナリで基準・選定候補を読み込む独立した実行環境を準備した。
両方でUSIの `readyok` を確認。探索コマンドは送らず、追加学習・対局・配備はしていない。

## 読み込み経路と分離

`src/main.cc` は起動時に作業ディレクトリのprogress／probabilityを読み、
`src/usi.cc` は `isready` で `params.bin` を読む。
既存の `tools/analysis/analyze_positions.py` は実行ファイルの親ディレクトリをcwdにする。
そのため既存ツールと同じ経路を使い、以下の独立コピーを用意した。

- `results/learning-pilot/2026-10-11-full-search-preparation-v1/baseline/bin/`
- `results/learning-pilot/2026-10-11-full-search-preparation-v1/candidate/bin/`

各環境に通常release、params／progress／probability／標準book、共通定跡をコピー。
Apple Siliconのreleaseが使う `@loader_path/../lib/libomp-x86_64/lib` の位置に
OpenMP dylibもコピーした。両環境とも7ファイル、計14ファイル・654,729,574バイト。
ハードリンク・シンボリックリンクは使わず、SHA／サイズ／異なるinodeを検査した。
候補側paramsだけが選定済み20更新平均化候補で、その他は同一。

両環境から既存のUSI Engineクラスで起動し、ShinYonenagaGyoku ON、OwnBook OFF、
Threads1、Hash64MB、MultiPV1、Ponder OFFを設定して `isready`、最後に `quit` を送った。
起動ログには読み込み失敗がなく、両方がRakuyouとして `usiok`／`readyok` を返した。
通常バイナリはロード後のparams SHAを表示しないため、ロード確認の根拠は
ソースの相対読み込み経路、実際のcwd、実行直前後のファイル照合と成功応答である。

作成後のコピー14件と元のruntime／共通定跡6件を再照合し、SHA不変を確認。
通常のbinやGUI設定を変更せず、固定25cp補正・先後共通定跡を維持した。

## 固定した次の比較条件

| 項目 | 設定 |
| --- | --- |
| 対象 | validation6＋test6、計12局面 |
| 選択方法 | 再静止探索で確認済みの各split・各side/result層から最初の1件 |
| 深さ／MultiPV | 12／1 |
| Threads／Hash | 1／64MB |
| 補正／book／Ponder | ON／OFF／OFF |
| プロセス | 各局面・各パラメータで新規起動 |
| 上限 | 基準12＋候補12＝24探索、各探索30秒 |
| 途中終了 | timeout時は失敗として記録し、自動延長・深掘り・再試行をしない |

対象は既に診断したtest32件の部分集合。残り224件の教師品質は今回も未測定。
各splitで先手／後手×先手勝ち／上限draw／後手勝ちの6層を各1件保持する。
保存するのはルート情報・着手列だけで、教師値に合わせた候補調整はしない。

次の実行では `positions.json` を両環境で同条件検索し、完了depth、bestmove、
PV、cpまたはmate、bounds、nodes、停止有無を比較する。
PVの合法性も確認する。depth0では省いたルート前の着手履歴を通常探索では再生するため、
静止探索の数値と直接差し引かない。ランダムなZobrist初期化なども残るため、
小さなcp差や選択手の違いを因果的な強化・弱化と断定しない。
今回はUSI準備だけで、通常探索の選択手／PV／棋力は未評価。

## 再現と成果物

```sh
python3 tools/learning/tempo/prepare_tempo_search.py \
  results/learning-pilot/2026-10-11-preparation-v2/manifest.json \
  results/learning-pilot/2026-10-11-pilot-run-v1/report.json \
  results/learning-pilot/2026-10-11-pilot-run-v1/selected-qsearch-check-v1.json \
  --output results/learning-pilot/2026-10-11-full-search-preparation-v1
```

出力はignored results内の新規ディレクトリのみ許可。既存環境の上書きを拒否する。
候補は初回reportの選択とSHAに固定し、準備manifestにファイル一覧・SHA、
対象局面SHA、固定設定、USIログ、探索0／更新0／配備falseを記録する。

| 成果物 | SHA-256 |
| --- | --- |
| 準備 `manifest.json` | `05e26d28eb91f7def2277d3cc766e79bed964e12364a3f3223b81a3f8a862aec` |
| 準備 `positions.json` | `4f79a9859e53f85bde4158921e586dc6cb21a613573ec4adfa6e841a653e9e4e` |
| 候補側 `bin/params.bin` | `1858ca315c4a5821710ea7b71f9251c5909f1c0ade88314306fd6baa7a7101f8` |
| 基準側 `bin/params.bin` | `6bbc573306839fe019634dd94b06af7c22834a641e8bc060e23889ae9b3b2195` |

独立コピー・上書き拒否、SHA不一致時の無書き込み、診断済み局面だけの選択、
reportと局面の不一致拒否を確認する4テストが通過した。
実データで14コピーと2回のUSI準備が完了し、探索回数0のまま閉じた。

次はこのmanifestとコピーを再照合してから、上記24回以内の通常探索比較を行う。
コピーの検証を省略した直接実行や、testを見て選択候補・係数を変更することはしない。
この準備はローカルの実験環境であり、外部バックアップや運用採用を意味しない。
