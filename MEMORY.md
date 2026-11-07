# Rakuyou resume map

Updated 2026-11-07. Read this on resume; open linked reports only as needed.
This file holds current state, durable constraints and next steps, not a changelog.
Earlier details remain in experiment reports and Git history (`a87f406:MEMORY.md`
is the last full historical map). Historical NEXT headings are not active tasks.

## Current objective and collaboration

- Aim for the user's preferred **手厚い将棋**. Completed thickness or a rank pawn
  is not mandatory. Do not force gold/silver advancement merely to copy a shape.
- Design, interpretation and final review belong to **Astra**; delegate settled
  implementation, validation and aggregation to **Sol**. This division is approved.
  User can run long batches externally; avoid repeated monitoring of deterministic runs.
- User (~amateur 4-dan) supplies style preferences, concepts and counterexamples,
  not assumed best-move labels. Separate preference, positional interpretation,
  tactical correctness and measured strength; explain with concrete squares/pieces.
- No bonus adjustment or formal adoption has been decided. Learning is paused.
  Do not turn an exploratory result into automatic deployment or a new training run.

## Current result and next step: normal comparison completed

[Result and all-eight-pair review entry](docs/experiments/learning/thickness/2026-11-07-normal-comparison-result.md).
[Fixed design](docs/experiments/learning/thickness/2026-11-06-normal-comparison-plan.md).

- Completed16/16; comparable8/8. Shin+0 and Shin+10 each3W5L; no draws,
  unresolved/errors/unrun. +0 Black1W3L/White2W2L; +10 Black2W2L/White1W3L.
- Pair deltas10−0: +1,+1,0,−1,0,0,−1,0. All games ended by resignation.
  No strength equivalence, adjustment or adoption established. Existing default0 remains.
- Source `results/teatsui-vs-normal-2026-11-06/`; all239 frozen bindings intact,
  all16 histories/options/go/bestmoves audited with native referee, no new searches.
  Evidence in `results/teatsui-vs-normal-review-2026-11-07/audit.json`.
- IMPORTANT: pairs1/2 (the two +10-only wins) first diverge at ply18 on NORMAL
  side despite identical preceding moves/settings. Time-limited search variability
  confounds direct attribution of those wins to bonus. Other pairs also not causal proof.
- Review UI `results/teatsui-vs-normal-review-2026-11-07/index.html`: all8 pairs,
  total32/48/64 snapshots and full navigation. User has reviewed pair4 through48; see below.
- Pair4 user feedback: at32 both acceptable and +10 also preferred style; at48
  prefers +0 as unhurried, solid play: central pawn/silver and king-side preparation
  both matter. +10 becomes a mutual attack, K3i/R2i proximity also worries user;
  user judges it somewhat worse. Preserve preference vs tentative positional judgment;
  no proven blunder or bonus causality. Do not reject +10's32 shape or add a penalty.
- Pair7 user feedback: prefers +10 at32, reverses to +0 at48; suspects +10 play
  after32 is mistaken. No specific bad move established. +10 plays ...P5e/S5e/P*5f
  at42/44/46; +0 organizes K8b/S7b/S6c/P*6d. Opponent continuations differ.
  User clarified: own king solidity and whether opponent is attacking matter to
  thickness. +10's ...P2d/P2e/P2f timing feels wrong with enemy horse invading at4a
  and attacking from behind; ...P5e/S5e is exploited by N6e. This is contextual
  prioritization criticism, not a blanket ban on pawn advances or a proven losing move.
- [Safety/support code review and68 static positions](docs/experiments/learning/thickness/2026-11-07-king-safety-and-support.md)
  completed without search/build/code change. Existing safety, KP, controls, sliders
  already represent king/attacker relations; support bonus adds independently and
  has no safety gate. Existing weights' adequacy not established; no term breakdown.
  Pair4 game7(+10) has no chain32–48; game8(+0) Black chain32–46, hypothetical
  +10 gives Black+6 at32 (actual game bonus0). Pair7 game13(+0) none; game14(+10)
  White chain only42 (...P5e supported by S6d/S5c), +6 White, gone on43 Px5e.
  This does not exclude effects on search branches or establish bad-move causality.
  Evidence `results/teatsui-king-safety-review-2026-11-07/static_audit.json`.
- [Pair7 bounded diagnostic](docs/experiments/learning/thickness/2026-11-07-pair7-diagnostic.md)
  COMPLETE8/8: after35/41,0/10 twice fresh, go depth15 nodes200000 (iteration
  threshold, overshoots). Four same-config repeats exactly match bestmove/score/
  depth/nodes/PV. All110 PVs+8bestmoves legal; bindings unchanged; no retries.
  after35:0 ...P1e (d13,278013,-570cp),10 ...P2d (d14,287093,-540cp).
  after41:both ...P5e;0 d14,214594,-617cp;10 d14,328767,-474cp.
  Both after41 PVs include Px5e Sx5e N6e: cannot claim knight jump unseen.
  Score143cp difference is NOT raw bonus effect; search paths differ. after35
  selection influence reproduced but0 also advances a flank pawn, not proven safer.
  Evidence `results/teatsui-pair7-diagnostic-2026-11-07/` (report,parent-review,raw).
- NEXT: diagnostic closed. No coefficient/safety penalty/training change justified
  by these two cases alone. Continue preference/function review of other saved games
  or, if user wants, compare saved after35 PV plans without assuming0 is better.
  Keep operational default0; experiment10 unadopted. No more searches automatically.
- No extra searches or matches automatically. User can supply shape/function preference;
  separate it from tactical correctness and strength. Learning remains paused.
- Preserve sealed plans, raw games and attempt markers; do not rerun prepare/preflight.
  Original plan SHA `ef4acbf95fced90aa2e249467b62e736b23f2ad8021eb57b7af4458b5fb47dd3`.
  Same repaired engine/data, normal ShinOFF/bonus0, focal ShinON/bonus0 or10,
  eight12ply known starts, focal color fixed, d15cap/10s/margin100ms/thread1/hash64.
  No normal-vs-normal control; do not infer isolated Shin effect or pool old pilot.

## Recent evidence and unresolved interpretation

- Existing feature: fifth-rank pawn supported by G/S, itself supported by another
  G/S behind/level; binary per side, files2..8, tapered by (1-progress).
  `ExperimentalSupportChainBonus` default0, range0..10; parameters/layout unchanged.
  It is a narrow experimental proxy, not a definition of all thickness.
  [Implementation](docs/experiments/learning/thickness/2026-10-31-support-chain-native.md).
- Search exposed two upstream problems, both fixed in isolated test engine:
  [Hypothetical recapture](docs/experiments/learning/thickness/2026-11-01-recapture-fix.md)
  and [no-legal-moves picker](docs/experiments/learning/thickness/2026-11-01-terminal-picker-fix.md).
  Operational `bin/release` was not replaced. Preserve old failed runs.
- Saved changed-PV reviews:14/12 prefer10,03 tentative10,13 roughly equal
  (0 naturalness/10 pressing potential). Different opponent continuations confound
  causal interpretation; preference is not strength evidence.
- [Timed16 pilot](docs/experiments/learning/thickness/2026-11-03-teatsui-match-result.md):
  bonus10 vs0, BOTH ShinON,8W8L,0errors/unresolved; all histories audited.
  Earlier fixed-depth pilot failed on a300s timeout; not scored or combined.
- [Saved-game review](docs/experiments/learning/thickness/2026-11-03-teatsui-game-review.md):
  game05 edge attack looked natural to user; later deterioration does not alone
  prove bad initial plan. No support feature in played states of05/06/15/16;
  this does not rule out effects inside search branches.
- **Game06 correction:** disputed silver is a defensive move, not an attacking drop.
  76 S8c9b captures pawn;80 S9b9c captures tokin;83 P9d9c+ captures silver.
  Separate from68 S*8h. Do not repeat the withdrawn “silver-drop attack” account.
- [Bounded defense diagnostic](docs/experiments/learning/thickness/2026-11-06-defense-diagnostic.md):
  before72 both0/10 P*9d; before76 both P*8d. Neither original move reproduced.
  Cold hash/time variability limits causality: bonus10 is NOT established as cause,
  nor proved irrelevant. Diagnostic is closed; avoid more06 digging without evidence.

## Durable style understanding

- Thickness also depends on own king solidity and whether the opponent is attacking.
  Forward pawn/GS shape is insufficient when rear invasion or tactical counterplay
  undermines it. Pair7: user dislikes flank pawn tempos under horse pressure and
  central push exploited by a knight jump; preserve contextual timing, not move bans.

- [Current direction](docs/experiments/learning/thickness/2026-11-01-teatsui-direction.md):
  A59 is now judged preferred solid G/S defense, not established thickness;
  advancing G/S and pawns further might make it thick. This supersedes the earlier
  positive thickness label without rejecting the shape. Gold advance also liked.
- Build thickness when feasible; otherwise defend, retain balanced right-king play,
  or exploit an actual opening to fight. Coordinate rank acquisition with supporting
  pieces and the opponent's play; neither pawn-first nor preparation-first is universal.
- Thickness differs from local numerical superiority, castle solidity, tactical
  deterrence and overall advantage. Judge attack/escape directions and exchanges;
  advanced pieces can also obstruct escape. Equality or difficult winning play
  does not imply thickness failed. Direct support differs from reinforcement.
- Do not infer an attack trigger merely from a rook relocation. B40/C56 were
  success examples; C rook9f→2f still covered8f, so user wanted continued restraint.
  [Core dialogue](docs/experiments/learning/thickness/2026-10-25-dialogue.md) and
  [corrections](docs/experiments/learning/thickness/2026-10-25-dialogue-followup.md).
- [Book teaching](docs/experiments/learning/thickness/2026-10-31-book-game12-dialogue.md)
  and [Shin transfer A/B/C](docs/experiments/learning/thickness/2026-10-31-shin-transfer-dialogue.md)
  are closed for now. A:not yet thick/no mandate to build; B:partial central
  thickness; C:attacking foothold, not established thickness. Book images/text/kifu
  stay private. All judgments are contextual, not automatic training labels.
- Feature limitations: ordinary high-Mino+S5f and preferred A59 can both match
  diagonal/unopposed support. Straight-only would lose A59; excluding an opposing
  pawn does not resolve the false match. No such feature change was adopted.
  [Context audit](docs/experiments/learning/thickness/2026-11-01-support-context-audit.md).

## Operational engine, books and build

- Rakuyou is a personal Gikou2 fork. Preserve upstream copyright headers.
  Read [development instructions](docs/development.md): SSE4.2/x86_64 via Rosetta
  on Apple Silicon. Experiments use isolated binaries; do not overwrite `bin/`.
- Operational `ShinYonenagaGyoku` defaults ON; initial K5i4h/K5a6b subject to legal
  root restrictions;25cp opening king-location preference retained; retreats legal.
- Current combined book:`books/shin-yonenaga-book-v1.txt` (17 positions).
  Black:`books/shin-yonenaga-black-book-pawn76-right-side-experiment.txt` (6).
  White:`books/shin-yonenaga-white-book-v2-experiment.txt` (11,frozen).
  GUI operation uses ShinON/OwnBookON/BookMaxPly20, combined file explicitly;
  uncovered positions search, no standard-book fallback. Experiment bookOFF is separate.
  [Sources/builders](books/README.md); [retired trials](books/HISTORY.md).
- Operational binary/data identities and isolated repaired engine identity are
  saved in current `preparation-review.json` and frozen plan. No learning candidate
  or support-chain bonus has been installed into the operational runtime.

## Paused research and repository safeguards

- All historical learning candidates remain unadopted. Tempo, king safety,
  gold/silver pair, supported pawn/gold, historical imitation and outcome/hybrid
  trials are closed or paused; do not resume from old NEXT headings.
  [Report index](docs/experiments/learning/README.md),
  [overall review](docs/experiments/learning/2026-10-14-overall-learning-review.md).
- Latest guarded mixed-learning behavior/match did not establish consistent
  strength/style gain. Deferred proposal: frozen-QS-leaf audit then root-vs-leaf
  comparison, not currently authorized execution.
  [Deferred design](docs/experiments/learning/data/2026-10-24-next-learning-design.md).
- Preserve corpus splits and exposure provenance; reused validation/test material
  is not unseen. Self-generated cp teachers are not independent stronger teachers.
  Normal Gikou `--learn` resets parameters/material. New learning needs its own plan.
- Keep raw games, search logs, checkpoints and audit JSON in ignored `results/`;
  reports record paths/hashes. Do not delete originals before a separate backup is
  verified: important raw data is not independently backed up outside this workspace.
- Preserve failed/incomplete runs and attempt markers; never silently retry/refill
  or reuse post-stop bestmoves. Runtime/input/source bindings must remain auditable.
- Cleanup may remove retired tools/tests and unadopted book variants in small
  batches, retaining findings/history. Keep operational17/book sources/builders,
  reusable USI/referee/replay utilities and meaningful tests. Filename “experiment”
  does not mean unused. playtest/match reaches hybrid/behavior/imitation/tempo/core:
  audit dependencies before removing learning packages. Current frozen run bindings
  must survive any cleanup; postpone code pruning until this comparison is finished.
- Public docs use repository-relative paths. READMEs explain usage/roles, reports
  preserve experiment details, MEMORY holds only current resume essentials.
  Keep this map short; replace superseded status instead of appending full histories.
