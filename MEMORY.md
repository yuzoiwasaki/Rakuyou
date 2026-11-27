# Rakuyou resume map

Updated 2026-11-27.

## △3二金のみ指定した柔軟な続行（2026-11-27）

- ユーザーは、△1三角を使うなら△4四歩〜△3四歩・△3三桂で下段飛車の横利きを通して備えたい、角に固執せず△3二金でバランスよく指す案を承認。今回の指定は34△3二金だけ、以降は探索。前のG32/B13/R41指定試行と混同しない。
- 同ブランチで `results/white-bishop13-rook41-review/run-gold-only.py gold-only` 実行。共通33手目から24手、凍結main26f7339/双方2秒/1thread512MB/booksOFF。34G32のみtrial_fixed、残り23手searchを確認。棋譜・ビューアは同親ディレクトリの `gold-only/rollout.json`・`gold-only/game-full.html`。ビューアは33手目から表示、先手通常下側・後手新米長上側。全57着手native合法・四回同一局面なし・JS構文確認済み。
- 続き：35▲1六歩/36△4四歩/37▲9六歩/38△3四歩/39▲4七金/40△3三桂/41▲2六歩/42△9四歩/43▲2八玉/44△1三角/45▲6九飛/46△2四歩/47▲2七銀/48△2一飛/49▲3八金/50△2五歩/51▲同歩/52△同桂/53▲2六歩/54△3七桂成/55▲同金/56△3三桂打/57▲9五歩。後手最終評価-115（先手最後+95）。勝敗未決、棋力改善の証拠ではない。
- 狙いのP44/P34/N33/B13が自発的に現れ、S44なし・銀53/63保持、玉62保持。飛車は41でなく21から2筋攻め。42△9四歩と57▲9五歩は残るレビュー点で、9筋の問題を解消したとは言えない。ここで24手試行を止め、ユーザーの形レビューを待つ。
- 正式定跡・コード未変更、PRなし。MEMORY.mdの既存未コミットメモを保持して追記。

## △1三角構想と手待ちの比較（2026-11-27）

- ユーザー補足：△1三角の構想は残す。△7二金〜△8一飛を先に整え、△4一飛も視野。左金は場合により△3二金。前試行の角往復・△4四銀・△9四歩から逆襲された点に違和感。後手なので手待ちも可。新たな一般禁止は導入しない。
- 同じexperiment/white-gold72-before-edgeで、前試行33手目（▲3七桂）を共通開始点として3本の24手試行を実施。凍結mainエンジン、2秒/1thread/512MB、booksOFF、先手通常下側・後手新米長上側。結果は `results/white-bishop13-rook41-review/{rook41,waiting,bishop-first}/rollout.json` と各 `game-full.html`。全着手native合法・四回同一局面なし、JS構文確認済み。
- rook41:34G32/36B13/38R41指定。39▲1五歩に40△2四角、42△4四銀。56手目後手-715。waiting:34G32/36B13/38R82指定。39▲1五歩に40△2二角、42△8一飛。56手目後手-698。単なる待ち・G32先決めはこの形で好結果にならず。両案の先手35P16/37G47は探索が同じ応手を選択。
- bishop-first:34△1三角のみ指定、金・飛車は探索。35▲4七金/36△5二金/37▲1六歩/38△4四歩/39▲1五歩/40△2四角/42△3四歩/44△1四香/46△1三歩/48△1五角/50△2六角/54△3三桂/56△3七角成/57▲同銀。後手最終-162。銀は53/63、9筋不動、飛車81・玉62のまま。角は働くが相手も変化し、勝率・一般的優位の証拠ではない。△4一飛は実現していない。ユーザーにはまずこの形を提示。
- 単独候補8秒比較 `diagnosis34.json`:34G32 -252/d23、34B13 -169/d25、34G52 -172/d23、34R82待ち -326/d25。`diagnosis38.json`（G32/B13済み・37G47）:38R41 -559/d23、R82 -621/d24、P15 -543/d23。異なる深さ・局面の値であり構想全否定しない。最初から3二金や4一飛を固定せず、金飛車整備後の34B13が次のレビュー候補。
- 正式定跡・コード未変更、PR未作成。局面限定試案をユーザーにレビューしてもらう段階。実験生成物はignored results/、引き継ぎのみMEMORY.md未コミット。

## △1三角より金・飛車を優先する試行（2026-11-27）

- ユーザーは今回の28手目△1四歩〜30手目△1三角を問題視。角が目標になるため△7二金〜△8一飛を急ぎたいとの意向。新規 `experiment/white-gold72-before-edge` で局面限定の診断を実施。正式定跡・コードは未変更、PR未作成。先に形をレビューする段階。
- `results/white-gold72-before-edge-review/diagnosis.json`: 実戦27手までから8秒ずつ単独指定（fresh/512MB/1thread）。△1四歩-104、△7二金-156、△8一飛-135。短い探索の数値で棋力優劣は断定しない。
- `results/white-gold72-before-edge-review/rollout.json`: main凍結エンジンで実戦27手＋28△7二金を指定、29▲5八金は探索、30△8一飛を指定。その他は双方2秒で探索、定跡OFF。52手まで24手の短い試行。全着手native合法・四回同一局面なし。△1三角は出ず、32△1四歩/34△5二金左/36△1五歩/40△3一角/42△2二角/44△4四銀/50△8三金、終了時後手-318。角の往復は残るので改善確定ではない。
- ビューア `results/white-gold72-before-edge-review/game-full.html`。先手通常版＝下、後手新米長玉＝上。28・30手だけ試案指定であることを明記。主に28〜44手の形をユーザーにレビューしてもらう。採用方向が固まったら局面限定の定跡追加と必要検証・PRを進める。

## 最新の対局レビュー（2026-11-27）

- origin/mainをfetchし、main `26f7339`（PR #11マージ済み）へfast-forward。既存の未コミット引き継ぎは保持。release/match再ビルド済み、bin定跡89局面は正式ソースと一致。生成チェックと定跡8テスト成功。
- ユーザーの依頼で初期局面から一局実施。先手＝通常版（下側）OFF/0/0、後手＝新米長玉（上側）ON/10/10。双方2秒・margin0・1thread・512MB、定跡は通常20/新米長44。158手目に後手投了。全157着手のnative合法性確認済み、四回同一局面なし。棋力比較の証拠ではない。
- 棋譜 `results/main-white-20261127-one.json`、凍結入力・ハッシュ `results/main-white-20261127-one/manifest.json`、ビューア `results/main-white-20261127-one-review/game-full.html`（ブラウザで開いた）。前局と分岐し新規30G72/32R81の定跡局面には到達せず。38R81/40G52は探索による別形。
- レビュー候補は40手目△5二金（6aから）と108手目△3五歩の攻めの継続。104手目△2六香はMultiPV3/depth15で-493（△1六桂-151）だったが、各8秒の単独指定では△2六香depth19/+11・△1六桂depth20/-123。評価が逆転し悪手断定不可。両単独読み筋に108手目△5七角が現れるが、実戦△3五歩との厳密比較は未実施。曖昧な敗因を深追いせずユーザーの棋譜レビューを待つ。診断は同reviewディレクトリのdiagnosis.json（MultiPV分のみ、後続指定手検査は候補数不一致で失敗）とforced-diagnosis.json（MultiPV1で再実行成功）。
- コード・定跡の改善変更なし。mainの未コミット変更はこのMEMORY.mdのみ。以下の再開メモは更新前の履歴として保持。

## 再開時の引き継ぎ（2026-11-27）

- ユーザーがPR #11（https://github.com/yuzoiwasaki/Rakuyou/pull/11）をマージしたと報告。Codex更新のためチャットを終了するところ。ローカルは `experiment/white-gold72-rook81-order`（df88776）のまま。リモートのマージコミット取得・mainへの切り替えはまだ。再開時は作業ツリーを確認し、このメモを保持してfetch・mainのfast-forwardを行う。
- ソース定跡は89局面（先手52・後手37）。実行用 `bin/` の定跡はまだ87局面なので、次の対局前にmainで `make release` / `make match` を実行し、正式定跡との一致を確認する。評価はShinON/support10/D10、BookMaxPly44のまま。
- 今回の採用は、早い▲1六歩が入る手順で30手目△7二金、▲4七金に32手目△8一飛を優先する２局面のみ。左金の△5二金／△3二金や△4四歩の時期は探索に任せる。金・飛車を整えた後の△5二金左はユーザーが許容。形の違いで定跡が外れたときは、既存の修正消失と混同しない。
- 次の候補は更新済みmainで初手から１局指し、ユーザーが棋譜を動かしてレビューする流れ。次局の実行指示はまだ受けていない。短い診断・１局ずつのレビューを好み、曖昧な敗因を深追いしない。先後と盤面の上下を明記する。
- 元の後手実戦: `results/main-white-20261126-one.json`、ビューア `results/main-white-20261126-one-review/game-full.html`。後手新米長玉（上側）が136手目投了。採用形の24手試行: `results/white-gold72-rook81-short-review/rollout.json` と同ディレクトリの `game-full.html`（29手目から）。詳細は `archive/white-gold72-rook81-before-integration-2026-11-27` に保存。
- 定跡・評価・探索の改善は今後すべて新規ブランチ＋PRで進めることをユーザーが明示許可済み。ブランチ選択を毎回聞かない。正式PRはDraftを外し、ユーザーがレビュー・マージする。AGENTS.mdとdocs/development.mdにも反映済み。
- この引き継ぎ更新はローカルの未コミット変更として保存。対局・解析プロセスは終了済み。

- White formation-order integration: two exact positions30G72/32R81 added in the earlyP16 rook-exchange line; book87→89 (Black52/White37). Leftgold destination and laterP44 remain searched. User approved the24-ply continuation, endingWhite-218; no strength claim. All89 entries pass native legality/load/hit checks; eight maintained book tests, scope fallbacks and generation checks pass. Detailed investigation archived and linked in PR; generated results remain local. User reviews/merges; installed book remains main87.

- Black closed-bishop integration: six exact positions for13P66/15B77/17S38/23S47/25S67/29G58 in the reviewed P74/S22 line. Book81→87 (Black52/White35). Middle-game plans remain searched; no engine/evaluation/BookMaxPly changes. All87 entries pass native legality/load/hit checks; eight maintained book tests and generation/scope checks pass. Known-line shape review is not strength evidence. Detailed investigation archived and linked in PR; generated games stay local. User reviews/merges; installed book unchanged.

- White P44 extension: add one exact position after BlackN37 in the reviewed G32 formation. Book80→81 (Black46/White35); prior P96 branch and other entries unchanged. AfterP44 replies remain searched. Candidate comparison and24-ply continuation reviewed; no strength claim. All81 positions pass native legality/load/hit checks, eight maintained book tests and generation/diff checks pass. Detailed notes archived and linked in PR; generated results remain local. User reviews/merges; installedbook remains main until integration.

- White balanced-formation integration: four exact book entries added after the opponent exchanges the six-file pawn with its rook:22S63/24G72/34G32/38P44. Book76→80 (Black46/White34). Other replies remain searched; no general G32 requirement, king lock, P24 ban or engine/evaluation change.
- User approved the formation after short diagnostics and a known-start game ending in fourfold repetition at115 (script records unresolved, no strength claim). Eight native book tests pass, including all80 entries and scope fallbacks; generated source/txt match. Detailed investigation is archived and linked in the PR; generated games/viewers remain local under results/. User reviews and merges; installed bin/book remains main until integration.

- Early rook-pawn integration: six exact Black book positions added (70→76, Black46/White30). First three prioritize P26/P25 before opening the bishop diagonal in the S62/P85/B33 line. New P96/P76/S77 branch prepares the edge and develops S77 after bishop exchange. Other replies remain searched; no engine/evaluation/BookMaxPly change. N77/P86/P85/R89 remains a reviewed middle-game idea, not a forced book line.
- User approved shapes after individual game review; mixed known-start and initial-position diagnostics do not establish a strength gain. All76 entries pass native legality/loading/hit checks; eight maintained book tests, generation check and diff check pass. Experiment details are preserved on the archive branch linked in the PR; local games/viewers stay under ignored results/. PR review/merge by user; GUI installation remains separate.

- Integrating three White book entries:22S63,28G72 after BlackG58,30G72 after R81/BlackG58 (BlackP46 branch). User approved shapes; subsequent moves remain searched. Book67→70 (Black40/White30); engine/eval/BookMaxPly44 unchanged. Known-start10 baseline4W1L/candidate3W1L1cap; initial20 baseline2W8L/candidate4W6L with only2newhitgames, identical first121plies. Third entry only short54-ply rollout, no long-game result; no strengthclaim. Experiment archived at archive/white-silver63-before-integration-2026-11-21 (e4447f5); generated results remain local. Release build and7 maintained book tests pass; all70 entries nativelegal/hit, fallback after new gold entries checked, generator/source and installed copy match. PR review/merge by user.

- Floating-rook integration prepared on experiment/bogin-bishop-transfer; do not merge automatically. User favors hineri formation and accepts modest evaluation disadvantage. Formal source/txt now67 positions (Black40/White27); book rules equal final tested candidate. Canonical source move orders repaired without changing SFEN/hand/turn/book moves; native uniqueness/legal/path consistency verified. BookMaxPly default44 includes late43B97; GUI saved20/32 needs44.
- Added conditional floating-rook entries, N77/P96/B97 and19S38 at S42/S72/B33. AfterS38 all replies return to search; no hard-coded floating/rightking classifier, kinglock, eval or search changes. Promotion when available retained; alternate defended23 floats. Existing bogin gold regrouping survives via transpositions; original White rules unchanged.
- Latest20: Black4W5L1cap,White0W9L1cap. S38 hit5Black/alllost but shared111plies; rightking K38/S47/N37/R29 achieved. No strength claim or pooling; no lateN77/B97 hits in startpos batches. Prior known-start shape review separate. User approves shape. Later111R49 vsS*52 (-673/-187 atd21) recorded as futuresearch issue; no fix included. Logs/diagrams results/s38-startpos20-review/.
- Full experiment sources preserved on archive/floating-rook-before-integration-2026-11-21 at3f6314b. Trial scripts/notes removed from integration tree; generated results/ remain local. Per-search shared-history halving rejected; no experimental C++ carried over. Reproduction needs archived sources and original frozen binaries/books/data; current bin/match rebuilt for default44.
- Validation: release/development/match builds pass; all18 maintained Python tests pass without skips; generator check and bin/ book copy match. PR #5 https://github.com/yuzoiwasaki/Rakuyou/pull/5 created ready (not draft); integration/archive pushed. User reviews and merges. Long games are user-run.

- PR #4 (https://github.com/yuzoiwasaki/Rakuyou/pull/4), branch `experiment/white-king62`, was merged as main2bdf140 and integrates the approved White fourth-rook book update. User reviews and merges; do not merge automatically.
- Fixed G32 adoption was rejected. White's 4a gold destination and P94 are not prescribed. King location and formation are not forced against arbitrary replies. Evaluation/search C++ is unchanged.
- Engine remains ShinON/support10/D10. Release hides fixed style options; stale style setoption values are ignored. OwnBook/ShinBookFile remain editable.
- `make release`: optimized fixed style. `make match`: optimized configurable comparison engine. `make development`: debug checks, much slower; do not use for long batches.
- Book verification is consolidated in test/books/test_operational_shin_book.py. Experiment sources/books/tests/runners/reports were removed from the final PR tree.
- White trial history is preserved at `archive/white-king62-before-integration-2026-11-18` (`25ee593`). Ignored results/ remain local; use that revision and its frozen book copies to reproduce experiment runners.
- Earlier archives: `archive/early-silver68-before-integration-2026-11-17` (`99e4859`), `archive/pre-adoption-cleanup-2026-11-15` (`f488a64`). PR3 root-recheck experiment was closed without adoption; its branch remains preserved.
- User runs long matches. Short bounded diagnostics are fine. Review clear style defects and skip ambiguous losses; known/repeated starts and capped games do not prove strength improvement.
- Aim: thick, coherent shogi; support sustainable territory, permit counterplay and turn thickness into attack. No blanket requirement to preserve territory or avoid king recastling.
- User authorizes new task branches and PRs for opening-book/evaluation/search improvements without repeating branch-selection questions. Consult about other changes. Minor changes may go directly to main with approval. Keep main limited to adopted code, maintained tools/tests and concise docs.
- Public README should stand alone and retain only2–3 major milestones. Remove Draft when presenting a finished PR; user reviews and merges.
