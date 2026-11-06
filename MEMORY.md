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

## Next step: prepared 0/10 comparison against normal

[Fixed design, verification and external command](docs/experiments/learning/thickness/2026-11-06-normal-comparison-plan.md).

- **READY; 0 match games run at last verification.** Sol preparation and Astra
  final review complete 2026-11-07. Check actual saved status before resuming.
- Output: `results/teatsui-vs-normal-2026-11-06/`. Local `match.py` reuses unchanged
  shared match/referee code. `plan.json`, `preflight.json`, `preparation-review.json`
  contain frozen inputs and validation evidence; raw artifacts are Git-ignored.
- Eight known 12-ply starts × Shin bonus0/10 =16 games. Focal Shin takes the color
  named by each start, NOT both-color swaps on one history. Each arm:4Black/4White.
  Same normal opponent: `ShinYonenagaGyoku=false`, `ExperimentalSupportChainBonus=0`.
- Same repaired binary/data; fresh engines each game; sequential games; bonus order
  balanced within each color. Shin arms differ only in bonus0/10. Bonus10 remains
  the existing symmetric evaluation feature, not a bonus restricted to focal color.
- d15 **cap**, 10s/move, margin100ms, watchdog30s, thread1/hash64, book/ponderOFF.
  Max256 additional plies remains unresolved. Errors stop; no automatic retries.
- Verified:6 local +25 shared tests;8 legal/distinct/ongoing/unrepeated starts;
  exactly6 fresh d3 preflight searches, legal moves/options before isready/timed go.
  Astra checked239 frozen file bindings, saved commands,8 SFENs and6 moves.
- Plan SHA: `ef4acbf95fced90aa2e249467b62e736b23f2ad8021eb57b7af4458b5fb47dd3`.
  Do not rerun prepare/preflight, overwrite plans or remove attempt markers.
- External execution from repository root, when user proceeds:

```sh
caffeinate -i python3 results/teatsui-vs-normal-2026-11-06/match.py run
```

- After completion: audit saved histories/options/hashes/results, then aggregate
  each arm and color plus differences within the same8 starts. Exclude unresolved,
  errors and unrun games from scored denominators; show their counts separately.
- Review **all8 pairs**, initially at total plies32/48/64 (or earlier terminal state).
  Distinguish gold/silver function, defensive holes, tactics and style preference;
  ask user about uncertain kifu judgments. No extra searches automatically.
- Known related starts are not16 independent samples. No normal-vs-normal control:
  this tests bonus differences conditional on these starts, not isolated Shin effect
  or general strength equivalence. Neither a tied score nor preferred shape adopts10.

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
