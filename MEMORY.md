# Rakuyou Development Notes

This file is the resume map: current state, durable decisions, constraints, and
links to evidence. Detailed experiment history belongs in `docs/experiments/`.

## Current direction: user-led thickness dialogue (updated 2026-10-30)

- Learning series explicitly paused. Root/QS-leaf proposal below is deferred.
  No learning/search/games/deployment or scoring implementation in this dialogue.
- Collaboration: user (~amateur4-dan) supplies intended style, conceptual
  distinctions and counterexamples, not assumed best-move labels; user regards
  Rakuyou as stronger. Separate style preference, conceptual mismatch and reading
  differences; use search/games when authorized to test actual strength.
- Incremental cleanup in progress: keep clearly reusable match,
  position/rules and operational tools plus meaningful tests; remove retired
  experiment-specific scripts/tests, retaining concise Markdown findings and Git
  history. Avoid committing future disposable scripts by default.
  Initial inventory (2026-10-26): tracked Python226 files/20433 lines;
  C++ .cc48/18880 lines plus .h66/11991 lines. Counts include repository-wide files.
  IMPORTANT dependency before pruning: playtest/match imports hybrid data/runner
  and behavior; these reach imitation, tempo and core. Extract needed match
  utilities first, not wholesale directory deletion. paired_selfplay.py has a
  reusable USI base; audit_white_positions.Board is used by local diagram scripts.
  First pass (2026-10-26): removed standalone constraints/audit.py and tempo/
  check_tempo_search_repeatability.py plus their two dedicated tests. No retained
  code imports them; historical reports now mark retired commands and point to
  commit530ca09 for source recovery. Local sources/results untouched. Next pass
  should again target isolated retired tools before shared-library extraction.
  Second pass (2026-10-26): removed four standalone imitation auditors
  (preparation, pilot, search_review, transfer_pilot; audit_*.py),360 lines.
  No remaining Python references; corresponding result reports retain findings
  and source-recovery pointers to fd3596f. Reusable sparse/native/match code kept.
  Cleanup is current-tree maintenance, not rewriting Git history.
- Agreed style direction: prefer thickness as an identity, while allowing a
  balanced right-king approach when conditions do not support building it.
  Do not force gold/silver advancement merely to reproduce a shape.
  Against static rook too, watch the opponent's attack speed and direction;
  prioritize defense when needed, build thickness if feasible, otherwise exploit
  an opponent opening to start a fight. Completed thickness is not a prerequisite
  for fighting. These are user-approved strategic aims, not verified rules.
  Rank acquisition is also conditional: if supporting golds/silvers will be late,
  taking a rank too early may be undesirable. Neither pawn-first nor preparation-
  first is fixed; coordinate rank and support with the opponent's play.
- User teaches thickness via historical positions and hypothetical arrangements.
  [Durable dialogue record](docs/experiments/learning/thickness/2026-10-25-dialogue.md)
  preserves judgments, eight boards, roles, uncertainties and assistant corrections.
  Board snapshots + manifest tracked; full games/local interactive HTML remain in
  results/thickness-dialogue/{first-game,b-concepts,main-game}/, not Git.
- Key distinctions: thickness vs local superiority/solidity/balance/effectiveness;
  rank pawns important but not absolute; direct support vs numerical reinforcement.
  Shin restriction targets effective enemy attack; ordinary king-head rank play
  can instead pressure enemy king. Exchanges not universally prohibited: compare
  resulting formations, drops and attack; favorable after exchange is not
  automatically continued restriction. Support pieces should be retained/replaced.
- Main-game B40 and C56 are user's success examples, A24 not thick yet. C slightly
  preferred for knight/silver participation and6e support; B rook/gold synergy good.
  B pawn7e is WHITE: assistant misread it; withdraw claim B has no rank pawn.
  G7d directly supports it; R7b supplies numbers. Losing pawn allows enemy setup.
  C still needs king/major-piece coordination; K7b is NOT a settled best square.
- Visual check COMPLETE: B40 White R7b->8b confirms prior reinforcement concern.
  C56 Black R9f->2f CORRECTS prior verbal interpretation: keep restricting, do not
  attack yet; rook still covers8f horizontally. Black S5f/P5f blocking that ray
  is an example of a real opening for White P8f, not a mandatory attack pattern.
  Wait for own readiness or actual enemy overextension; rook relocation alone
  is not an attack trigger. Hypothetical diagrams remain local in
  results/thickness-dialogue/understanding-check/.
- [Follow-up dialogue](docs/experiments/learning/thickness/2026-10-25-dialogue-followup.md)
  records this correction and user teaching from privately supplied Doronuma-ryu
  book photos. No book images/text/kifu reproductions in Git.
  G7h primarily castles for later attack; Fig4 already assembled, then pushing.
  P5e/S5f expand territory AND support rank; enemy silver leaving the area and
  own silver joining improve local participation. P7e also cramps the opponent.
  Forward pressure gives some indirect king protection (offensive defense),
  distinct from direct castle solidity. Reluctant silver capture is a special
  certainty-versus-complication choice, not a general rule against material gain.
- [Main-game continuation dialogue](docs/experiments/learning/thickness/2026-10-25-main-game-continuation.md)
  records D70/E82/F88 and actual79 vs ...P8f Px8f K7b reference variation.
  User's final distinction: thickness succeeded even if overall position equal;
  later handling and winning chances remain separate. E's initially favorable
  impression was reconsidered after P*7f; Px6f/P4d suspected, not proven errors.
  D calls for gold/major-piece activation with exchange risks; rook roles include
  supporting thickness, opposite-wing attack and covering thin2-file. Returning
  king7b can reopen an8-file plan. Reference variation: equal but no dissatisfaction.
  User identifies earlier B5g as opportunity enabling ...P3d and offensive setup,
  not necessarily a blunder; do not attribute the opportunity only to P*6f.
  Diagrams/HTML remain local in results/thickness-dialogue/main-game-continuation/
  and main-game-79-variation/. Native reference-line replay/SFEN checked, no search.
  Ware Yaburetari reference was secondary; original book not inspected (see report).
- [Book game08 dialogue](docs/experiments/learning/thickness/2026-10-26-book-game08-dialogue.md)
  COMPLETE: privately supplied pp87-97 vs Nakahara. Fig5: opponent's2-file attack
  means no time for slow buildup; use rank pawn P7d to start fighting. Fig8 S6e
  is an attacking move, NOT necessarily thickness-building (assistant corrected).
  Fig11: advanced silvers give king-head territorial control, simultaneously
  attacking and making own king harder to attack; can outweigh some material loss.
  Distinguish individual move purpose from resulting formation's effect.
  This game too is vs ranging rook; differences from Shin concern king/rook
  placement and pressure targets, not merely opponent's opening category.
  Book images/text/kifu remain outside Git. No learning or search performed.
- [Book game09 dialogue](docs/experiments/learning/thickness/2026-10-30-book-game09-dialogue.md)
  COMPLETE: private pp98-109 vs Oyama. G6h prepares king defense before P6e
  opening battle; not just adding forward thickness. Fig7 thickness serves both
  pressure and defense, slightly more pressure. ...P9e attacks thin edge while
  bypassing thickness; own dense pieces also block the king's desired rightward
  escape (not merely ineffective thickness). G8h/K7h is concrete defense, not
  "restored thickness": opens escape, pressures rook/seeks gold-for-rook exchange,
  activates idle gold. User adds Shin countercase: against attack from below,
  upper pieces may support entering king. Consider attack/escape directions;
  no concrete Shin entering-king example verified here. No learning/search.
- NEXT: another book case when user supplies it; today's dialogue finished.
  User wants understanding before
  learning restart and asks about transfer from non-Shin games. Proposed distinction:
  general thickness concepts vs formation-specific judgments vs actual training
  data. Cross-check book insights against Shin positions; do not automatically mix
  book games/outcomes into teachers. No learning/scoring restart authorized.

## Current direction: matched search/outcome/hybrid learning (2026-10-15)

- Latest completed (2026-10-20): train-only bounded common-direction diagnostic
  at mixed zero/final states; no checkpoint changes, search, games or deployment.
  Same caps permit both groups' mixed AND outcome losses plus global mixed+L2
  to decrease. At zero, ordinary direction fails all7 step sizes; unit-normalized
  group-gradient sum succeeds. At final, ordinary corrected direction succeeds;
  balanced direction needs one halving. Neither method is universally better.
  [Evidence and limitations](docs/experiments/learning/data/2026-10-20-common-direction.md).
  Follow-up implemented: one zero-start fixed200 comparison with group-loss
  acceptance, ordinary direction first then balanced fallback; same data/ratio/
  caps and20 backtracks per direction (diagnostic used6). Five smooth train
  losses must decrease >1e-12; stop if both directions fail. Saved ordinary
  mixed is control. No checkpoint extension or validation selection.
  [Plan and command](docs/experiments/learning/data/2026-10-20-temporal-guarded-plan.md).
  Related57 tests pass, including5 new tests.
  COMPLETE user run:200 updates, all balanced fallback, no accepted backtracks,
  71 corrected steps. Ordinary direction fails loss-group mixed/outcome guards
  on all4200 trials. Validation outcome all+.231530%, win+.019903%, loss+.518332%;
  ordinary mixed +.214871/+2.143440/-2.398772%. Black still-.172235%, White+.647482%.
  Validation search+.079795% (ordinary+.121815%). Smooth confirms direction.
  Saved bindings, trajectory, final losses/caps and sidecar checked.
  [Result](docs/experiments/learning/data/2026-10-20-temporal-guarded-result.md).
  Follow-up behavior implemented:24 roots,3 per original/additional x side/result
  stratum, fixed hash ordering, distinct games within each stratum; no score-based
  selection.48 fresh baseline/candidate d15 searches,1thread/hash64/bookOFF/ShinON,
  timeout120s both. Related62+7 tests pass. Export1088 static checks pass,
  zero export and byte-region checks pass; current bin unchanged.
  PREPARED24 roots from23 games; native replay and both USI readiness checks
  pass, no go sent. Added-root Huffman IDs derived by native replay.
  [Behavior plan](docs/experiments/learning/data/2026-10-20-guarded-behavior-plan.md).
  COMPLETE user run reviewed2026-10-24:48/48 successful,24 regular pairs,10
  changed moves (original6/additional4; win5/loss5). All saved records/PVs and
  plan/runtime bindings checked without search. Changes include a gold move
  toward own king, knight preparation, attacking silver drop and move-order
  swaps; no consistent thickness or strength improvement established.
  [Result](docs/experiments/learning/data/2026-10-24-guarded-behavior-result.md).
  Follow-up implemented: fixed candidate vsbaseline, fresh14 games on same7
  operational-book prefixes with color swaps; exposed starts, exploratory only.
  Same d15/thread1/hash64/timeout300/max256 additional plies; native referee.
  Related66+10 tests pass. PREPARED2026-10-24-guarded-book-match-v1;7 native
  start replays, plan reload, both USI readiness checks pass. No searches/games.
  [Plan](docs/experiments/learning/data/2026-10-24-guarded-match-plan.md).
  COMPLETE14/14,7/7 pairs:5W8L1D,0errors/unresolved. Black3W3L1D,
  White2W5L; Shin-side2W5L versus opponent-side3W3L1D. First5 pairs split,
  pair6 bothlosses, pair7 draw/loss. All histories replayed and bindings checked;
  one lower-reported-depth flag(game5 ply157), no stop commands.
  Saved reviews games1/8/11/12 show useful silver advance but also exposed king
  and exchanges removing guards; no consistent thickness/strength gain.
  [Result and pause](docs/experiments/learning/data/2026-10-24-guarded-match-result.md).
  Pushed through32abceb toorigin/main. Design review completed: current root
  static fitting differs from native RootStrap (QS score, gradient at QS leaf).
  NEXT implement bounded preparation/audit of baseline frozen-QS leaves for
  same750/187 roots and saved d15 teachers; no new deep teachers or learning yet.
  If preparation is sound, compare fresh zero-start root vsleaf search-only
  runs with shared data/keys/caps, then reevaluate actual candidate QS scores.
  Hypothesis only, not established cause. Style remains separate; no G6c labels.
  [Design](docs/experiments/learning/data/2026-10-24-next-learning-design.md).
  No further training/ratio sweep, deeper case searches or deployment.
- User found the specific G6c preference-label discussion unhelpful because the
  move is unusual. Stop that case's preference confirmation and further digging;
  retained examples are diagnostics, not approved imitation labels.
- User agreed to implement search-only, outcome-only and 50/50 mixed learning.
  Parent handles design/integration; bounded Sol implementation/test delegation
  was authorized to reduce token use. User can run long commands externally.
- New isolated `tools/learning/hybrid/` reuses expanded 383/80 roots plus six old
  draw diagnostics. Primary cohort is the same 256/64 decisive roots for all
  arms, subject to shared documented teacher exclusions. Draws stay diagnostic.
  Current depth15 root teachers are generated once; all arms predict ROOT static
  scores. No historical cp teachers or old QS leaves are silently mixed in.
- New train-only backtracking optimizer permits up to 200 updates, .02cp step,
  .5cp per-key cap and 100cp train-position impact cap. Validation never selects
  steps/checkpoints. L2 1e-6; no averaging. Native scoring reports both losses,
  sides/outcomes and separate draw impact; no automatic adoption/arm selection.
- [Plan and external commands](docs/experiments/learning/data/2026-10-15-hybrid-learning-plan.md).
  Keep old experiment markers and runtime/books/25cp unchanged. Historical NEXT
  entries below do not override this user-approved direction.
- Implementation/preparation completed; final verification checked 2026-10-16.
  Full suite: 302 tests passed (29 new hybrid tests). One old outcome-search test
  now uses its own temporary marker so real closed experiments cannot affect it.
  All469 saved root scores/packed components match native zero-overlay evaluation.
  At implementation verification, no real searches/updates had run yet (completed below).
- Prepared `results/learning-pilot/2026-10-15-hybrid-v1/` with isolated baseline.
  Plan SHA `daf08198939a16af32c03b662a54a93e080bf17c202e776be7ad79afc29df51c`;
  dataset SHA `ad48bff61e63c542b6767fc2d58bca237389c893c5d3b22cbc66350bac0db8fe`.
  Preparation/code/runtime bindings rechecked successfully. Do not rerun prepare.
- User completed teachers + runner on 2026-10-16: accepted318/excluded2,
  common train255/validation63. Search/outcome/mixed stopped at63/64/74 updates.
  Validation outcome improvement +0.650/+0.192/+0.360%, search metric
  +0.149/+0.020/+0.067%; these are loss improvements, NOT win rates.
  All three worsen outcome loss on losing-game roots, including training roots.
  Saved arithmetic confirms all21 next proposals exceed100cp in each arm:
  boundary stop, not proven convergence. Code/runtime/teacher bindings checked.
- [Result and next priorities](docs/experiments/learning/data/2026-10-16-hybrid-learning-result.md).
  Initial implementation/result committed and pushed as58e1309.
- User requested continuation. First implement a24-root same-position behavior
  comparison, before games: existing paired_selfplay hardcodes ON/OFF and lacks
  adequate repetition adjudication. Both variants here use ShinON/bookOFF.
  Select6 per side/result stratum by fixed ID hash from accepted validation63;
  already exposed diagnostic data, not an unseen strength test. Fresh depth15,
  thread1/hash64/timeout30,48 searches. Long run remains external/user-executed.
- Search-only isolated export completed:469 static evaluations match saved arm;
  zero export and byte-region audits pass. No search or deployment in export.
  `results/learning-pilot/2026-10-15-hybrid-v1/search/export-audit.json`
  SHA327cb6343abd48941232be7a947c7125ca1bff551ffd46d95b6121020faa53af.
  Do not rerun export; retain existing isolated runtime.
- [Behavior plan and commands](docs/experiments/learning/data/2026-10-16-hybrid-behavior-plan.md).
  New code lives in tools/learning/playtest; frozen hybrid code stays unchanged.
  PREPARED results/learning-pilot/2026-10-16-hybrid-behavior-v1; do not reprepare.
  Plan SHA8e350fdcd7f5651a75c77ec0dc4f134b3f1ae0d295764c24391c8d085e8f0765.
  All309 tests pass (7 new);24 native root replays legal/nonrepeated with matching
  SFEN/Huffman; both isolated USI readiness checks pass, no go/search/game sent.
  COMPLETE user run2026-10-17:48/48 success,24 regular pairs,6 changed moves.
  Changes by Blackloss/Blackwin/Whiteloss/Whitewin=3/1/1/1 of6 each.
  Baseline24 bestmoves/cp reproduce teacher generation exactly.48 saved records,
  bindings/checksums and native PV legality/diagnoses rechecked without search.
  Behavior reaches move choices, but strength/thickness gains remain unproven.
  [Behavior result](docs/experiments/learning/data/2026-10-17-hybrid-behavior-result.md).
  Report SHA0db293a5ea9347c5e922f5e316ad060cdc7d0a44f38216d90773d1a0efa45980.
  User approved next small paired-game stage and requested a behavior-stage
  checkpoint commit before implementing it. No paired games have run yet.
- Behavior checkpoint committed as46300be (not pushed). User authorized proceeding.
  [Paired-match plan](docs/experiments/learning/data/2026-10-17-hybrid-match-plan.md).
  New match.py + independent native referee; existing engine/hybrid/behavior
  code unchanged. Fixed8 manually authored12-ply starts,4 Black-Shin/4 White-Shin
  contexts across rook choices;2 color-swapped games each. Not an unseen sample.
  Both ShinON/bookOFF/thread1/hash64/depth15,timeout30,256 additional-ply cap.
  Formal fourfold/perpetual-check/mate/CSA declaration; illegal/timeouts/errors
  never count as losses, ply cap stays unresolved. Fresh processes per game.
  Per-ply logs; completed games resumable; failed/incomplete attempts block retry.
- PREPARED results/learning-pilot/2026-10-17-hybrid-match-v1,8starts/16games.
  Plan SHA2dafaed708152a303987289dca8e95dd326247b0aab5e7b867eb318e340c77db.
  Referee results/match-tools/match-referee separately compiled, build.json binds
  inputs/objects/headers/recipe; do not rebuild default or overwrite artifacts.
  All330 tests pass (13 native +8 match new);8 roots legal/nonrepeated/ongoing,
  distinct from each other and469 learning roots; both USI readiness checks pass.
  No real searches/games/learning/adoption performed in this implementation turn.
  NEXT external: `python3 -m tools.learning.playtest.match run` (no prepare/build).
  Read summary.txt/report.json and games/ after user completes;16-game depth pilot
  is not an equal-time strength estimate or adoption evidence. Candidate stays fixed.
- v1 user run FAILED game1 atply107/additional95: referee underpromotion
  enumeration constructed forbidden White lance9d9i through asserting FromSfen.
  Actual candidate move1e2f legal; infrastructure failure, not a game result.
  Fix native token construction via unchecked Create then IsOk; assertions kept.
  Old v1 logs/attempts/runtime/build retained. New v2 binary/results prepared.
  Verified106 saved-history states identical, ply107 legal,95 saved PVs legal;
  no new search. All332 tests pass, including2 added regression tests.
  Same starts/games/settings/runtime verified in restart-audit.json.
  Restart16 games from original openings (cannot restore in-game search state).
  v2 output results/learning-pilot/2026-10-17-hybrid-match-v2 (superseded below).
  Plan SHA30c3858259ba614b143e467befc468805b0a77865068a97d98a6db149ce8935a.
  Referee results/match-tools-v2/match-referee; do not overwrite old or new build.
  NEXT external unchanged: `python3 -m tools.learning.playtest.match run`;
  default now v2, no prepare/build required. Read v2 summary/report after run.
- v2 user run: game1 complete candidateBlack win by resignation; game2 rejected
  normal bestmove8f8g atply147 because last printed info depth12/cp9559.
  Source IterativeDeepening throttles final info, so reported depth is not actual
  completion depth. Harness now accepts normal bestmove with valid1..15 printed
  depth, flags lower printed depth/stale PV; timeout/errors still fail.
  No engine/referee/candidate/settings changes. Old v2 failure retained.
  v3 prepared output results/learning-pilot/2026-10-17-hybrid-match-v3 (superseded below).
  Game1 legally/result audited and imported with sourceSHA; game2 starts afresh.
  Same16-game schedule/runtime/settings/referee checked, old logs bound in plan.
  Plan SHAd137ecafde0e6342d98f2df2cdec9cc7109b035f95b73b2efb1c382d5b0ab124.
  NEXT external same `python3 -m tools.learning.playtest.match run`, starts game2.
  No build/prepare needed. Read v3 results; previous errors aren't scored losses.
  No additional real searches/games in this fix.
- v3 game2 timed out after112 plies on baselineBlack depth15 search. Logs show
  stop then depth15/time30004ms + resign; do NOT score post-stop resignation.
  Extend both watchdogs30->300seconds; go depth15 unchanged, no engine change.
  match.play now reads depth/timeout from frozen plan instead of hardcoded30.
  Ten match tests pass incl both-player timeout forwarding. No real new searches.
  CURRENT prepared results/learning-pilot/2026-10-17-hybrid-match-v4.
  Plan SHA1261a85999e80c3436ee63c7c0bb721b4553c73da1ec3a174ab15db299a04d97.
  Oldv3 failure retained and bound. Game1 re-audited legal/resign/no-stop, imported;
  restart game2. Starts/runtime/referee and settings except watchdog unchanged.
  NEXT external: `python3 -m tools.learning.playtest.match run`; defaults v4.
  No build/prepare. Review v4 summary/report after user run. 300s completion untested.
- v4 COMPLETE user run:16/16games8/8pairs;candidate6W8L2D,unresolved0/errors0.
  Black3W3L2D,White3W5L; start-design Shin side2W6L vs other4W2L2D.
  These are exploratory8 fixed openings, not proof of strength/style change.
  All16 sealed game/report matches, bindings and native final replay/results pass:
  14 resignations,2 formal repetition draws (games11/13). Old failed runs retained.
  Report SHA8ab4156ed910defb45d6ccb6c3ef612f7d73ffcd0c827c984940f75f56dca5b5.
  [Match result](docs/experiments/learning/data/2026-10-17-hybrid-match-result.md).
  NEXT recommended: review games3/4 and7/8 (both-color losses) for support/king
  safety/defense vs tactics before additional games or learning; no special move
  labels. Candidate adoption and mass games on hold. No new searches in review.
  Match implementation/fixes/results committed and pushed as111153c (also46300be).
- User approved saved-only review first, then narrowly selected extra searches.
  COMPLETE games3/4/7/8 review: no common excessive-advance/thickness cause isolated.
  Game7 gold-drop check wins rook for gold; both earlier PVs omit it, candidate
  recognizes it atply81. Game4 ply88 PV already anticipates pawn drops +G*8c
  while +544; later assessment changes, not simply an unseen king attack.
  Games3/8 major-piece exchanges also prevent simple hanging-piece claims.
  [Four-game review](docs/experiments/learning/data/2026-10-17-hybrid-match-loss-review.md).
  No new searches/games/learning/code/runtime changes. NEXT proposed: same-history
  game7 beforeply79 andgame4 beforeply88, baseline/candidate xdepth15/20 (8 searches),
  fresh processes, user-run. Preparation completed below. Distinguish tactical
  horizon/continuation valuation from candidate-specific effects; no move labels.
  Before further learning address optimizer stopping globally at100cp.
  Raw artifacts remain in ignored results/.
- Review committed asf342df0; user requested continuation after commit (no push requested).
  PREPARED diagnostic.py, two roots xbaseline/candidate xdepth15/20 =8 searches.
  Output results/learning-pilot/2026-10-17-hybrid-diagnostic-v1; do not reprepare.
  [Diagnostic plan/command](docs/experiments/learning/data/2026-10-17-hybrid-diagnostic-plan.md).
  Threads1/hash64/ON/bookOFF/fresh/fullhistory/watchdog300. Completed failures
  retained without retry; other jobs continue. Incomplete marker blocks restart.
  Related21 tests pass; both USI ready and saved two bestmove/PV native checks pass.
  Plan SHA12c77cbe39fbdc9acac26dace78722ae4728b31fb2d6e095f58aa2f77af276d7.
  Source match/hybrid/behavior code and runtime unchanged.
  COMPLETE user run8/8 successful; requested/reported depth and bestmove/PV agree.
  Game7 d15 baseline/candidate G8f -377/-47; d20 R8h -960/S*3c -1028.
  Game4 baseline G*8g +548/+643 atd15/20; candidate N4e +345 ->G*8g +604.
  No persistent candidate-specific thickness failure isolated; d20 is not ground truth.
  Bindings/eight saved records/commands and native bestmove/PV legality checked.
  [Diagnostic result](docs/experiments/learning/data/2026-10-17-hybrid-diagnostic-result.md).
  Report SHA9b1472fe632e1e92f3b12924b6c4c7732cef2dfebd91b63510bc9f2fecdee1ae.
  NEXT recommend stop digging these roots; design optimizer constraint handling
  before new learning. Compare direction adjustment vs soft penalty, not merely
  raising100cp. No new implementation/training authorized by result alone.
  No new searches/learning/deployment in result-review turn.

- Diagnostic implementation/results committed and pushed as3971b90 (includesf342df0).
  User authorized proceeding after checkpoint. New isolated constraints/audit.py
  completed train-only saved-checkpoint direction diagnosis, no candidate saved.
  Each arm has1 training root near100cp; coefficient-bound counts115/120/148.
  All3 admit a hypothetical improving step with BOTH old bounds intact after
  direction correction. No validation used, no iterative training/search/export.
  Four geometry/constraint tests pass; input SHA unchanged and all bounds checked.
  [Audit and next design](docs/experiments/learning/data/2026-10-17-constraint-direction-audit.md).
  results/learning-pilot/2026-10-17-constraint-audit-v1/report.json
  SHA982f96544ac2375191877eec6246e91b3d2a5979b55b04e8b8d843f382f63449.
  NEXT implement robust constrained-direction training in separate module/run,
  compare old/new from zero delta with same data/teachers/budget for all3 arms.
  Prioritize hard-bound direction adjustment over soft penalty or cap increase;
  prototype is not exact projection nor a convergence/strength guarantee.

- User authorized continuation. Implemented separate constraints/optimizer.py and
  runner.py: active-bound feasible direction, all-bound step limit, train-only
  Armijo acceptance, explicit numerical stops. No frozen hybrid changes.
  PREPARED six runs legacy/direction xsearch/outcome/mixed, each zero-start max200,
  same255train/63validation, teachers, .5cp coefficient/100cp root caps.
  Legacy must exactly reproduce original delta/trajectory/stopping. Validation
  only after all6 training runs; native469 reports; no export/search/adoption.
  [Plan and external command](docs/experiments/learning/data/2026-10-17-constrained-training-plan.md).
  results/learning-pilot/2026-10-17-constrained-training-v1; do not reprepare.
  Plan SHAb5e2a3927196191631d2b03a218bc2199671982952dd81403671c514d4d7f044.
  Full349 tests passed, then added iteration-limit test; targeted8 optimizer tests
  passed (12 constraints tests incl audit). Native469 zero scores match; all3
  saved checkpoints admit improving feasible hypothetical step in new code.
  No real iterative training yet. Each update atomically checkpointed/resumable.
  COMPLETE user run: legacy reproduces all3 original checkpoints exactly.
  direction all200 updates but worse train objective and val-outcome than legacy.
  Active position constraints=0 throughout all3: maxtrain94.53/92.81/90.23cp
  (search/outcome/mixed). ~half steps<.001 due coefficient-bound global step limit.
  This implementation slows before reaching100cp; did not exercise root-bound
  direction correction. Loss-group outcome loss still worsens train andval.
  [Result/implementation limitation](docs/experiments/learning/data/2026-10-17-constrained-training-result.md).
  comparison SHA49e10b33c7efb4234f6a6436183a97ed25d2e3d491512e7d9af0e89efe865608.
  NEXT prioritize independent coefficient clipping (legacy behavior until root
  cap) with bounded correction only when needed; synthetic near-coefficient-cap
  test and exact pre-root-cap reproduction before another run. Freeze v1 code
  and results; do not extend budget or mutate plan. No adoption/new games.

- User requested checkpoint commit then continuation. Committed audit/v1 code/results
  as1694621; no push requested. v1 remains frozen.
  Implemented projected.py + runner_v2.py: legacy independent coefficient clipping;
  only root-cap-violating proposals get cyclic slab/box/step-box correction.
  Strict objective decrease, all bounds checked; no v1 global coefficient step limit.
  PREPARED results/learning-pilot/2026-10-17-constrained-training-v2, six zero-start
  legacy/projected x3 teachers, same data/limits/max200. Do not reprepare.
  [v2 plan](docs/experiments/learning/data/2026-10-17-constrained-training-v2-plan.md).
  Plan SHA59756c4f23ac36021785d103c55b6d46099589739b97b30785ba4566b6d2e137.
  Full355 tests passed; then added restart test and targeted6 passed.
  Saved0/25/50 checkpoints x3: hypothetical next step exactly matches legacy at9
  points. All3 old stopping checkpoints admit feasible improving corrected step,
  3/4/4 sweeps. No real iterative training/candidate save/search during prep.
  COMPLETE user run6/6: projected all200, root corrections140/142/133 updates
  (search/outcome/mixed); legacy exact reproduction; pre-correction prefixes
 60/58/67 exactly match legacy. All train/coef caps respected.
  Val outcome improvements search .986649%, outcome .170904%, mixed .515802%.
  Train loss-group outcome now improves all3 (+.421/+2.042/+1.780%).
  Val loss-group still worsens (-.696/-2.345/-2.178%); search most improved.
  Outcome/mixed same val-loss root exceeds100cp (+113.122/+108.949); outcome
  train-draw diagnostic also+113.664, outside constrained255. Search all469<=100.
  [v2 result/next priorities](docs/experiments/learning/data/2026-10-17-constrained-training-v2-result.md).
  comparison SHA0a866f893df29e04a1db299d7518e0b3b92a0b9bcdc4aaee8c3fd651d8a4c842.
  NEXT recommend isolated projected-search export +24 exposed behavior roots;
  audit/reuse original baseline and oldsearch logs for3-way comparison, only24
  new searches if bindings match. Not yet implemented/exported/searched.
  No adoption; outcome/mixed tuning, extra updates and mass games on hold.

- User requested commit and next stage: v2 implementation/results committed646ea4b,
  no push requested. Isolated projected-search export complete, zero/byte audits
  and469 native table/sidecar scores match; both source and prior runtime retained.
  export-audit SHA53302ff9f5ec39d1d119721668fb3fa2e6a592a4dcbf29beccfbfb82e0af2805.
  PREPARED results/learning-pilot/2026-10-17-projected-behavior-v1,24 old roots,
  new projected-search only. Audited48 baseline/oldsearch saved records, PVs and
  commands; reused with SHA bindings for3-way comparison. No new real searches.
  [Plan/command](docs/experiments/learning/data/2026-10-17-projected-behavior-plan.md).
  Plan SHA93c93349404b05d8fa23b42a0e59120ffcc7ee4d075bdea0653a3ef09d07d7bd.
  Same depth15/thread1/hash64/fresh/ON/bookOFF/timeout30 as old behavior stage.
  Full359 tests passed, then added timeout/reuse test; targeted4 passed.
  New engine ready verified. Export/prepare complete; do not repeat.
  COMPLETE user run24/24 success,24 valid triples. Changed vsbaseline6,vsold4.
  Of6 old changes:3 retained,2 different new moves,1 baseline reversion;1 new
  change among18 formerly same. New changes concentrated seen loss roots.
  Root5 G5h supports S6h/S4g beforeP7e, but old PV also G5h afterP7e; no proof
  of newly learned thickness. Root3 P3f vsoldK2h,root15 B3c vsG5b,root1 revertsB*3c.
  All24 PVs/native diagnosis, source bindings, commands and report recomputation pass.
  [Result/next match proposal](docs/experiments/learning/data/2026-10-17-projected-behavior-result.md).
  Report SHA4497f2309806f67ff96d732988cbff638fc0ed3bec9360fe552cfc3bb4bf2579.
  NEXT recommend16 fresh games vsbaseline, same8starts/color swaps/depth15 as
  old pilot to compare descriptively. No reuse of old games with changed opponent.
  Already-exposed diagnostic starts, not independent/equal-time strength proof.
  Not yet implemented/prepared/run. No adoption or new labels/deeper root hunts.

- User approved trying16 games. PREPARED projected-match-v1 with new constraints/match.py,
  old match rules/play/saved/aggregate reused unchanged. Same8starts,16fresh games,
  depth15/thread1/hash64/ON/bookOFF/watchdog300/additional256. No imported old games.
  Fixed projected-search vsbaseline; native referee unchanged. Completed-only resume;
  failed/incomplete attempt blocks retry, errors not losses, caps unresolved.
  [Plan/command](docs/experiments/learning/data/2026-10-17-projected-match-plan.md).
  results/learning-pilot/2026-10-17-projected-match-v1, do not reprepare.
  Plan SHA24a39a47a10819292983846d3e109665bc31cde419b546e2421ca18540ecb8b1.
  Related27 tests pass;8 native starts match legal/nonrepeated/ongoing;both engines
  ready with no go. No actual new games/searches in preparation.
  COMPLETE user run2026-10-18:16/16,8pairs;9W5L0D2unresolved0errors.
  All16 native histories/last_referee match,14 resignations and2maxply verified;
  no stop commands. Unresolved games1/9 at268plies, not draws or scored wins/losses.
  Black3W3L2U,White6W2L. Opening-Shin-side3W4L1U vsother6W1L1U.
  Old6W8L2D comparison promising, not independent/equal-time strength proof.
  [Match result](docs/experiments/learning/data/2026-10-18-projected-match-result.md).
  Report SHA33458f93b4c2a7a1dd63dfc309ec2766e28df2262691b07977a7ed8dce662fdc.
  NEXT recommend saved games10/12 (Shin losses->wins) and6 (win->loss) review,
  then fixed candidate on prospectively chosen unused starts, separately designed
  equal-time trial if practical strength is target. No rerunning/lengthening
  unfinished games, training or adoption now. No cause/style claim yet.

- User requested commit then continue. Behavior/match implementation/results
  committed eec4b60, no push requested. Saved review games10/12/6 COMPLETE.
  First old/new divergences atplies14/16/16, so later comparisons not same roots.
  Game10 edge attack with knight/lance/pawn, game12 king escape to7d/8d/8e
  and exchanges/counterattack; neither proves stronger thickness. Game6 loses
  king-side gold/silver through B*6b/G*6b sequence; defensive replies exist,
  later PV already anticipates much of exchanges, not simply unseen threats.
  [Review](docs/experiments/learning/data/2026-10-18-projected-match-review.md).
  Native replay/new3+old12 and independent piece/capture/check tracing pass.
  NEXT recommend fixed candidate on prospectively defined different starts,
  same depth15 first to isolate opening dependence; equal-time separate later.
  No deeper root searches/labels/training/adoption. New-start trial not prepared.

- User authorized continuation. PREPARED alternate_match.py with8 fixed12-ply
  alternatives: Black-Shin ply11 P5f->P7f,White-Shin ply12 S5c->P9d, acrosssame4
  rook strata. Config fixed before evaluation/search, no result filtering.
  Candidate/runtime/settings unchanged;16fresh games,same depth15/watchdog300.
  Novelty audit checks all469 saved learning root histories +32 prior match full
  histories, including180deg color swap and transpositions;8 roots unique/legal/
  nonrepeated/ongoing, independent Board SFEN matches. Not universal unseen claim;
  nearby opening variants, not independent random sample; later transpositions possible.
  [Plan/command](docs/experiments/learning/data/2026-10-18-alternate-match-plan.md).
  results/learning-pilot/2026-10-18-projected-alternate-match-v1; do not reprepare.
  Plan SHAe89c5eb2f5e4597750507f6a7a0ed09a3a3e5c35afc014eb823f559f2146cfff.
  Related30 tests pass; both fixed engines ready/no go. No games/searches yet.
  COMPLETE user run16/16:7W8L1D0U0errors, Black4W3L1D/White3W5L.
  Candidate Shin-side0W7L1D vsother7W1L; baseline Shin-side1W7L.
  Thus both engines combined onShin-side1W14L1D. Initial saved13ply search
  scores negative forShin context inall8 (white-static about-600), also negative
  in prior starts. Start/engine-common difficulty plausible, not isolated cause.
  All16 native histories/last_referee match;15 resign/1formal repetition(game3,
  102plies),no stop. Not stable strength proof; adoption held.
  [Result/next priorities](docs/experiments/learning/data/2026-10-18-alternate-match-result.md).
  Report SHA889711c5cf109e3c8b025c7d9eceda41f9272cc14f133374f2ef62b26ea5099e.
  NEXT recommend saved-only representativeness audit of manual12ply starts vs
  operational books/intended formations before more games/retraining/time tests.
  Keep candidate fixed; no cherry-picking favorable starts, no new labels.
  No new experiments in result-review turn.
- User requested commit/push then continuation: checkpoint d66a92e pushed to main.
  Completed saved-only book/start audit (no searches/games/training): manual
  Black roots diverge at ply3 (S3h vs book P7f), White-fourth at ply8 (S7b vs
  S5c); other strata outside book coverage. No subsequent registered-position
  transposition through ply12. All16 starts +17 book continuations native legal.
  [Audit and next proposal](docs/experiments/learning/data/2026-10-18-start-book-audit.md).
  Audit SHA40106553ab176f4bde40a56403942e644ab5b47a4c40ac7783d641d4d0b29ad6.
  NEXT proposed: fixed current candidate, all7 canonical operational-book leaf
  prefixes (2 Black/5 White), color swaps14games, bookOFF thereafter. Verify
  position duplicates/re-entry before freezing plan. Not prepared or executed.
  This tests book-aligned entry continuations, not independent strength or book
  selection; retain all unfavorable prior results. Adoption remains held.
- User approved book-aligned comparison. PREPARED book_match.py, all7 canonical
  leaf prefixes /14 color-swapped games; same fixed candidate/runtime/settings.
  Native legal/ongoing/nonrepeated, independent Board SFEN exact, no duplicate
  roots including rotation/color swap, no immediate registered-book re-entry.
  Related33 tests pass; both USI readiness checks pass with no go sent.
  [Plan and command](docs/experiments/learning/data/2026-10-18-book-match-plan.md).
  Output results/learning-pilot/2026-10-18-projected-book-match-v1; do not reprepare.
  Plan SHAb595cf14fac08a04522d03411f6fd2a3c9da06a97a5b640b8a09ab4e5fe286d7.
  NEXT external: `python3 -m tools.learning.constraints.book_match run`.
  No new games/search/training/deployment during preparation. Review by entrance,
  candidate color and Shin side; seven related branches are not independent.
- Book match COMPLETE:14/14games7/7pairs;6W6L2D,0unresolved/errors.
  Each candidate color3W3L1D. Candidate Shin-side4W3L; other2W3L2D.
  Both engines combined Shin-side7W5L2D; prior one-sided losses did not recur,
  but changed strata/prefix lengths prevent causal book/formation conclusions.
  Native replay all14 histories equals saved referee; report games match records.
  Twelve resignations, formal repetitions game2/7 at66/80plies.
  [Result](docs/experiments/learning/data/2026-10-18-book-match-result.md).
  Report SHAc47fbe4a9b5d21063f0affac3b4854da29e18eb9f24c848484ba9a42293f7e59.
  NEXT recommend saved-only review games5/6 (both-color losses) and11/12
  (first both-color wins), support/advancement and king safety. Result-selected
  diagnostics, not labels. No more games/training yet; adoption held.
- Saved-only four-game review COMPLETE (5/6/11/12); no search or learning.
  Game5 candidate built anaguma but 2-file pressure displaced guards; game6
  candidate had K8b/S5c,S8c/G5b,G7b but central exchanges removed defenders.
  Game11 candidate won after king escape into enemy camp, not sustained thickness.
  Game12 S8c recaptured N on7b and promoted pawn on8c while central guards stayed.
  Pairs diverge atply9/18; no same-position causal attribution or preference labels.
  [Review and next direction](docs/experiments/learning/data/2026-10-18-book-match-review.md).
  NEXT recommend pause this candidate's repeated opening trials/deep case searches;
  audit existing training coverage of exchanges/remaining defenders before choosing
  data expansion or teacher changes. Mixed learning remains an option, not proven
  better by these games. No data relabeling/extra experiments/deployment performed.
- User requested continued work with checkpoint commits. Book-stage implementation
  and reports committed59f7046 (not pushed in this turn).
  Saved-only coverage audit COMPLETE: accepted255train/63validation, one root/game,
  only Shin-side turn, selected24..80ply. Train progress>=.5:119, validation25.
  Actual next12plies include GS capture85/17, own near-king GS capture36/2,
  own GS immediate recapture44/9 (train/validation). Teacher PV12 counts89/21,
  30/7,46/12. These are event proxies, not good/bad thickness labels.
  Three tests pass, all318 saved PV12 native legal/Board matching. No new search.
  [Coverage and next design](docs/experiments/learning/data/2026-10-18-training-coverage.md).
  Audit SHA f11a435d3b0ae647dc84c46b7109cc1a61ea8dbfb42fe66206efd622572dbb2c.
  NEXT design small time-separated multi-root extension within existing train
  games (tentative total<=3/game), preserve run split, equal game weights, current
  teacher and zero-base restart/projected optimizer. Fix selection and search
  budget before execution. No extra roots selected yet. Validation remains exposed;
  do not cherry-pick exchange events or mix recent evaluation games into training.
- User requested push/continuation:59f7046 and2671fa7 pushed to main.
  Temporal selection COMPLETE: original+24/+48plies, no score/progress/event
  selection/refill; same318 games/splits. Additional501train/124val,11 beyond
  saved game endings excluded; no collision/legality/repetition exclusions.
  396 additions beyondply80. Native/Board625 roots match, zero cross-split runs.
  Selection SHA3c9921f8cd477c0c4008b6a2476deb025656b04d086e0aba1acec3a4c71de89e.
  PREPARED625 teachers + static frames in2026-10-18-temporal-teachers-v2.
  Reuse old318 teachers separately; no candidate params used. Same depth15 with
  watchdog300seconds. Native match referee avoids old underpromotion crash.
  v1 preparation retained, zero searches, superseded after pre-run import fix.
  Related13 tests pass; USI ready/no go. Plan SHA
  11627de89e378595069283c7d0b07bb7d1646a1b39b962766d5fbd9794ffc47a.
  [Plan/command](docs/experiments/learning/data/2026-10-18-temporal-teachers-plan.md).
  NEXT external: `python3 -m tools.learning.constraints.temporal_teachers teachers`.
  No prepare/build needed. After completion inspect exclusions/cp distribution
  and equal-game weights1/(G*m) before implementing/running weighted training.
  Selection no longer applies archivedabs(cp)<=1000; don't hide late saturated
  positions or select replacements. Original validation remains exposed.
- Temporal teachers COMPLETE625:619accepted/6excluded,0failed. All6 train:
  repeated PV5,mate1. Bindings/raw records/checksums/aggregate verified.
  Combined original+new750train/187validation from255/63 games; train241x3,
  13x2,1x1 roots; validation61x3,2x2. Equal-game1/(G*m) weights confirmed.
  Addedtrain abs>=1000:116/495,>=3000:16/495; latter2.16% total weight,
  1.25% zero-delta absolute score-derivative mass (not parameter gradient).
  No post-score exclusions/refill. TeacherSHA
  d4314ebdd4306b3f4132bbfb6a4f59d86965327050b559f9c50aad92dbd43a18.
  [Result/next implementation](docs/experiments/learning/data/2026-10-18-temporal-teachers-result.md).
  NEXT implement weighted search-only objective/projected runner, zero-base200,
  same caps with all750train roots; original/added metrics separated. Test
  equal-game weighting, old-objective equivalence and finite-difference gradient.
  No training/search/game/deployment during this teacher-result review.
- User authorized weighted implementation. PREPARED temporal-training-v1:
  750train/187validation,107964 train-only keys, one zero-start search-only run,
  equal-game objective/gradient1/(G*m), existing200/caps/projected correction.
  Frozen projected/old objective untouched; new weighted modules separate.
  Old projected-search delta compared on same cohorts after training, no old
  retraining. Metrics original/added/all and side/outcome, weighted per subgroup;
  native+smooth,151 old non-teacher root diagnostics retained.
  Related45tests pass incl finite differences, equal-game replication, old mean
  equivalence, cap checks/resume. Native zero1088 positions/packed parts match.
  No real training checkpoints/search/games/deployment yet.
  [Plan/command](docs/experiments/learning/data/2026-10-18-temporal-training-plan.md).
  Plan SHA45856588f3fd9947f7a290c34c22c981b5567a788a8e639e6abeeea061ef62fa.
  NEXT external: `python3 -m tools.learning.constraints.temporal_runner run`.
  No prepare/build needed; final train-stopped state, no validation selection.
- Temporal training COMPLETE200/update_budget;114 corrected updates, final loss
  .650286389, smooth train impact99.99864cp. Bindings/state/caps/last loss checked.
  Additional train fit improves, but original/additional validation both below
  old candidate. Val all outcome/search+.117914/.131353% vsold+.453099/.179968%.
  Losing-game outcome loss worsens train−2.41226%,val−2.948122% (old−.787046,
  −1.175095). Of373 train loss roots,137 teacher-down/candidate-up; validation
  53/95 likewise. Not solely optimistic teachers; shared fitting tradeoffs possible.
  [Result and next comparison](docs/experiments/learning/data/2026-10-18-temporal-training-result.md).
  Comparison SHAd100aaf8938fa7cc0f4baf10d6d61f728e9ffc3eede1d137061baa5ce95858a1.
  NEXT proposed one50/50 mixed comparison on SAME750 weighted rows/zero start/
  caps/budget, current search result fixed control; judge loss strata and original
  search consistency separately. No rate sweep or new data simultaneously.
  Prior mixed underperformance remains evidence; no guarantee of benefit.
  Hold temporal candidate games/adoption/budget extension. No new run prepared.
- User approved fixed50/50 comparison. PREPARED temporal-mixed-v1, same750/187,
  keys/weights/caps/projected200, zero start. Reuses saved old-search and temporal
  search comparison; only mixed training/native evaluation runs anew.
  Related48tests pass; control checkpoint/loss/caps/checksums verified on load.
  No real mixed updates/search/games/deployment yet.
  [Plan/command](docs/experiments/learning/data/2026-10-18-temporal-mixed-plan.md).
  Plan SHA7d898f1a31d2add717ea785bc12fb77d3d2f93c90b15d224e7f196237e97f37f.
  NEXT external: `python3 -m tools.learning.constraints.temporal_mixed run`.
  Summary includes loss stratum plus original/added/all. No ratio sweep, no
  validation checkpoint selection; interpret outcome and search tradeoffs together.
- Mixed COMPLETE200/update_budget; loss.6198657166692091,110 corrected updates.
  Train-loss outcome−.189044% vs temporal-search−2.41226%; val-loss still
  −2.398772% vs−2.948122%, old−1.175095%. Val all outcome/search+.214871/
  .121815% vsold+.453099/.179968%. ValBlack outcome−.3561%,White+.803076%.
  One exposed White-loss original root dce17654..:1:62 changes−305->−192cp;
  smooth+113.2668,not cap violation (100cp constrained train only).
  Bindings/checkpoint/last loss/train caps/control reuse/sidecar verified.
  [Result and pause decision](docs/experiments/learning/data/2026-10-19-temporal-mixed-result.md).
  Comparison SHA519057bae412e3237dc8d6df441ceec76131cf39210ea7634ed0324f8ad2c839.
  Recommend hold games/adoption/budget extension/ratio sweep for this series.
  NEXT if continuing: saved train-only group-gradient conflict/boundary diagnostic,
  compare original/additional and win/loss groups before proposing features or
  relaxed caps. No claim of proven representation failure. No new run prepared.
- Train-only gradient conflict audit COMPLETE (search/mixed zero/final4states).
  Full-cohort1/(G*m) contributions reconstruct total+L2. Mixed win/loss cosine
  −.8213 zero/−.8361 final; original/additional+.2896/+.2147. Atzero no caps
  hit yet mean descent worsens loss-group mixed objective locally. Final position
  correction flips loss-group first-order change from positive to negative;
  constraints not sole cause and may protect this group. No representation proof.
  [Diagnostic](docs/experiments/learning/data/2026-10-19-gradient-conflict.md).
  Audit SHA92a05627df9c1fbcc0e7745477b61201240cfbdaa83b7445f84d903682a8d0c2.
  Two tests pass; hypothetical directions only, no saved candidate updates/search.
  NEXT if continuing: bounded train-only feasibility diagnostic of common
  win/loss improvement under SAME caps before accepting new optimizer/feature
  changes. No ratio sweep, cap relaxation or games recommended yet.

## Previous direction: thickness through move comparisons (2026-10-15)

- User agreed to follow the overall review: specify when to build/maintain
  thickness and when to stop advancing before designing another learning run.
- Prepared discussion pairs from the same three previously reviewed train
  games: A Black67 G5h6g vs R6h6g (recapture/rebuild mutual support with S5f);
  B White68 G5c6d vs G5c6c (support S7e/P6e vs retain rear support);
  C Black115 P8f8e vs horse6f5e (continue attack vs remove pawn threatening G5f).
  C is the normal Black side of a White-Shin run, not a Shin failure label.
- Provisional preferences A gold/B advanced gold/C horse capture are discussion
  proposals, not confirmed labels or best-move claims. Actual continuations
  verified; alternatives' later play and compensation remain unexamined.
  Source/split SHA matched; existing probe --replay only verified six legal
  branches, child occurrence1 and independent Board SFEN agreement. No params
  loaded, no new evaluation/search/learning/games or feature/tool framework.
- These three seen games are teaching examples, not unseen validation. Before
  learning, confirm preferences and check same-root alternatives, then design
  observable update scales and game-disjoint evaluation. Old20 conditions are
  not mandatory for new work. Runtime/books/25cp/closed candidates kept.
- [Discussion and proposed success criteria](docs/experiments/learning/gold-silver/2026-10-15-thickness-move-pair-discussion.md).
  results/learning-pilot/2026-10-15-thickness-move-pairs-v1/report.json
  SHA b4cb8eeefed85c4900318967cd2538d4f0bb057061867a5b9791120eb3ac1022.
- User approved same-root comparison. Fixed3roots xdepth15/20 MultiPV2,
  restrictedpair/thread1/hash64/ON/bookOFF/fresh/30s/max6/no retries.
  COMPLETE PARTIAL5/6: A15 G6g-104/R6g-748;A20 -130/-801;
  B15 G6d-122/G6c-300;B20 -116/-389;C15 P8e-411/horse5e-725.
  C20 timedout,closederror1;no retry/refill,failedattempttranscript unavailable.
  Currentbaseline alreadyranksA/B desiredmoveshigher amongpair,notunrestricted
  bestmove proof. Arookrecapture leads...R7f/R5g/G6g;BpassivegoldallowsSxP6e.
  C preferredP8e line ...Sx8e/horse5e,thenR3h/P*8d/Kx8d: attackfirst then
  pawncapture protectsG5f inthatline. Do NOT forcehorse-first stylelabel;
  notanestablishedblunder orproof ofgold safety,depth20missing.
  A/B keepasbasicchecks,C ascounterexample;threepairstrainsetnotcreated.
- Saved5records/10PV commands/rawscores/legalreplay/Boardtrace audited;
  allprotectedruntime/source/isolatedcopySHAandnewbackupcopiesverified.
  Auditacceptssavedrecords only,complete_scopeFalse. Searches6attempted,
  no separateQS/learning/games/export/adoption/featurechanges.
  comparison-attempt-v1.json inpairdirectorylocksrun;donotbypass.
  [Comparison result](docs/experiments/learning/gold-silver/2026-10-15-thickness-move-comparison.md).
  results/learning-pilot/2026-10-15-thickness-move-comparison-v1/report.json
  SHA4bade11e36bd0c775ac48ba80ede60b6099153b013587f4b8f00d0b8c28b7510.
- Userauthorized boundednextcandidate review. Reusedsame2train games,2pairs
  fixedbeforecurrentsearch fromactualsupportmovevsprioropponentPValternative:
  A Black59 S4g5f vs B7g6f;B White60 G5b6c vs G5b4c. No newgames/test/val.
  depth15only/MultiPV2/restricted/thread1/hash64/ON/bookOFF/fresh/30s/max2,
  complete2/2,errors0,no retries/refill. A S5f-14/B6f+66,gap-80cp;
  B G6c-88/G4c-25,gap-63cp. Audit4legalPV/rawscores/trace/inputs/copiespass.
  A bothPVdevelopS5f fromdifferentsources andknightexchange,so notclean
  stylelabel. Bprovisionalfirstcandidate: G6c/P*6e/G5c supportsS6d thenS7e;
  alternateG4c/B4b/P3e isdifferentviablecentralplan. ShortPVno immediatefree
  gold/silverloss,notasafetyproof. Neitherlabelconfirmednor63cpgeneraltolerance.
  OldC20timeoutnotrerun. No learning/newfeature/games/runtimechanges.
  [Two style candidates](docs/experiments/learning/gold-silver/2026-10-15-thickness-style-candidates.md).
  results/learning-pilot/2026-10-15-thickness-style-comparison-v1/report.json
  SHA6914a03a7f1554d0960f9d9d68f5cf9a640ae9a8934b45e85aa55c23ed5efa01.
  Parent2026-10-15-thickness-style-candidates-v1/comparison-attempt-v1.json
  locks2searches;donotbypass. Theseareseen illustrativegames,notvalidation.
- NEXT consultB gold/silver/pawnplan preference andsafety/learningdesign.
  No automaticmorecandidatehunting/search/training/adoption.
  Userrequestedonecoarsecommit/push ofdiscussion/comparison/candidate reports
  andMEMORY. Savedrawlogs/scripts remaininignoredresults;reports recordSHA.

## Review handoff (2026-10-14)

- User requested a review of all learning work, then documentation, commit and
  push for Sol to read before continuing. The [overall review](docs/experiments/learning/2026-10-14-overall-learning-review.md)
  separates verified observations, hypotheses, and prioritized proposals.
- Initial mechanics/safety work was appropriate; tiny updates, sparse evidence,
  reused validation and teacher/goal mismatch limit usefulness judgments.
  No candidate has demonstrated sufficient style or strength benefit for adoption.
- Recommended next design: evaluate when to build or abandon thickness through
  move comparisons; choose observable update scales in isolated experiments;
  compare search-only, outcome-only and mixed teachers for strength learning.
  Keep losing games. Do not infer playing-strength loss from outcome-label loss.
- Retain runtime isolation and data provenance, but do not treat old 20-update
  settings as universal requirements for new experiments. Preserve closed runs
  and their attempt markers. New experiment settings remain to be designed.
- This handoff is documentation only: no code changes, experiments, audit reruns,
  or adoption. User intends to continue with Sol; the review is not a fixed
  execution plan. Historical NEXT entries below describe their original stages.

## Project and runtime

- Rakuyou is a personal experimental fork of Gikou 2. Preserve upstream
  copyright headers and existing C++ conventions.
- On Apple Silicon, build the SSE4.2 engine as x86_64/Rosetta. Read
  [development instructions](docs/development.md) before build or learning-data
  work. Run Python tests from the repository root with
  `python3 -m unittest discover -s test -t .`.
- Current runtime data in `bin/` is user state. Do not overwrite it during
  experiments. Last verified identities:
  - `bin/release`: `6f7891c4957e1bf37b1e80c37ad0c9cf83f34ca974e87be05fb05dd5c1f4c2ac`
  - `bin/params.bin`: `6bbc573306839fe019634dd94b06af7c22834a641e8bc060e23889ae9b3b2195`
  - `bin/progress.bin`: `ddf60a3180f768d9756b83cd4fe50a18b9e93855d1ad7281566934fb7c53a042`
  - `bin/probability.bin`: `dc2b18f1eaa7551822901eab7b68c6f279cc449ef527462b611b5d9510cb6c1a`
  - `bin/book.bin`: `cd42c35f48db3148a2c2f312887313b43135074dd3c0fa6bcd2fb04e66ac28c8`

## Current engine and book decisions

- `ShinYonenagaGyoku` defaults ON. At the initial position it selects Black
  `5i4h` or White `5a6b`, subject to legal root restrictions. The 25cp opening
  king-location preference is retained; retreats remain legal. Do not change
  these settings implicitly.
- The common 17-position book is
  `books/shin-yonenaga-book-v1.txt`, SHA-256
  `d080bc78583695da22641509ca93682653baa4761cb633f4f144ec1aef7c7e07`.
  Black's six-position book is
  `books/shin-yonenaga-black-book-pawn76-right-side-experiment.txt`, SHA-256
  `cb8d7e3e3a4ed2817752ea93d4890837fa43c91db752b5ce3a1dc534f38bb7eb`.
  White's 11-position v2 is
  `books/shin-yonenaga-white-book-v2-experiment.txt`, SHA-256
  `28e59ec12cb86ada7280687d130e29bdb28eb0d550840d634c73e003aa2ffc62`.
- Use the combined file explicitly with `ShinYonenagaGyoku` ON, `OwnBook` ON,
  and `BookMaxPly` 20. GUI settings do not switch automatically. Uncovered
  positions go to search; there is no standard-book fallback. Regeneration and
  source locations are in [books/README.md](books/README.md).
- The books are bounded operational choices, not proof of playing strength.
  White v2 is frozen. Black's pawn76/right-side six is the current operational
  choice; the pawn36 addition and other candidates remain unadopted.

## Learning work: closed, no candidate adopted

- The tempo-three-coefficient, four-feature king-safety, and one-feature
  gold-silver-pair experiments are closed. Current evaluation and runtime files
  remain the baseline. Do not resume learning, tune coefficients, expand data,
  run more searches/games, or adopt a candidate automatically. Wait for the
  user's direction before starting another experiment.
- Supported central fifth-rank pawns: authorized single20-update run is closed;
  selected0,baseline retained,no candidate adopted.
- The final pair-feature check selected only the five-update candidate for
  review. Validation re-quiescence search showed no PV or leaf changes; six
  normal-search roots had unchanged best moves and mixed PV/score changes.
  Adoption remains on hold. See the [final pair review](docs/experiments/learning/gold-silver/2026-10-12-pair-final-search-review.md).
- The expanded pair run used 143 training and 35 validation positions. Its
  validation improvement was small and layer results mixed; it is a mechanics
  observation, not evidence of playing-strength gain. See the [expanded
  result](docs/experiments/learning/gold-silver/2026-10-12-expanded-pair-learning-result.md)
  and [teacher/leaf audit](docs/experiments/learning/data/2026-10-12-pair-expanded-teachers-and-leaves.md).
- Earlier tempo and king-safety results, data preparation, and implementation
  notes are indexed in [learning reports](docs/experiments/learning/README.md).
  Preserve test splits and do not use them for tuning. Prior input diagnostics
  and qualitative game reviews exposed some test data; do not call the whole
  split unseen. Draw outcomes and max-ply draws have their recorded
  masking/adjudication limits. Existing `results/` attempt markers
  prevent reruns; never remove or bypass them.
- The 47-run self-play corpus has 2,740 games and 475,347 moves. Historical
  parameter/progress/probability identities are unknown. Existing train,
  validation, and test splits and their run-level separation are documented in
  [learning feasibility](docs/experiments/learning/framework/2026-10-11-learning-feasibility-plan.md).
  Gikou's normal `--learn` resets parameters/material; experiments used a frozen
  baseline plus deltas instead. Do not treat self-generated teachers as an
  independent stronger teacher.

## Current work: outcome-based self-play learning

- Userrequested outcome-based self-play learning;reuse existing scaffolding,
  notredo corpus/splits. Previous saved/pushed checkpointbc1156a;outcome
  preparation andresult are saved in the nextcoarsecommit. Prior trials kept.
- PREPARATION complete using unchanged143/35 ROOTS,one/game,originalrun
  split31train/8val/8test. Rawterminal labels revalidated all178;Shin side and
  historiesmatch. Decisive96train(48wins/48losses),23val(11wins/12losses).
  Truncateddraw47/12 maskedfromloss/keys/denominator,keptforimpact;White
  draw24/6. No formal draw labels,winning-White target1. No newtestgames.
- NewlossmeanlogisticCE sigmoid(cp/600),equal selected-game weights,deltaL2.
  Use currentstaticROOT evaluation+existing sparseKP/PP,no cp teacher ormove
  imitation,nonew normal/QS/data selection. Zero178/native packed baselines
  match;outcome finite gradients and masks8tests pass. Sourceolder-game runtime
  hashes unknown;reusedvalidation notunseen,notwinratecalibration/strengthproof.
- Train-only25290keys,initialloss.6815263001,L2_1e-6 atcap.01 ratiosmedian
  .249%,p90.934%,87weakkeys>25%. Native staticcapmax5cp;progress/tempo/etc
  protected. Oldbackups+newextras verified,zero checkpoint+labelaudit pass.
  [Outcome preparation](docs/experiments/learning/data/2026-10-13-selfplay-outcome-preparation.md).
  results/learning-pilot/2026-10-13-outcome-preparation-v1/report.json
  SHAac1edd4bbe2d15552bd980aebc05a3179174f9929b57af615ea1c3f131295d9e;
  saved-label-auditSHA34af3efa9e216c9988090509fb76732fac0aee85df674a97c068ebb6980c0ee9.
- Userauthorized firstoutcome20-run COMPLETE,unchanged96/23 decisiveroots,
  draw47/12masked,fullbatch96,L2_1e-6,rate/step.001,cap.01,averaging.9995,
  saved0/5/10/20,selectedfixed20. No oldcandidateinitialization.
  Trainintegerloss+.10348%,smooth+.10832%;valinteger+.002929%,smooth+.002176%.
  ValBlack-.01502%,White+.01456%,wins+.02935%,losses-.02968%;8valinteger
  changes,4outcome-directionbetter/4worse. No strength/generalizationclaim.
  Valdraw6/12 change+1cp(mean+.5),eachside3/6;no outcome lossfor draw.
  Whole178integermax3cp,smoothmax2.470;avgmax.00491154,current.00763347,
  caphits0. New3guards pass;20trajectory/gradients/averages/4checkpoints exact,
  packed712scores/labels/summary auditmatch. Oldbackups,new7files+audit2
  verified. No new normal/QS/games/selection/tuning;runtime/books/oldcandidates
  kept. Candidate savednotadopted. Outcome prep learning-attempt-v1.json locks.
  [Outcome firstresult](docs/experiments/learning/data/2026-10-13-selfplay-outcome-first-result.md).
  results/learning-pilot/2026-10-13-outcome-run-v1/report.json
  SHAe35097e34aa32eaafea939f2f04870bf5f6a5ea213a8ab97cd612b37db03c8bc;
  auditSHA1478201f8a9e7b77c14c0053876318c7e1b8c8da3d336d338d492b463e6bb4cc.
  average-20.txtSHA81ed1ad3a9b37827df31be85e4617d2dc39a96d311db3bd70853cb964dc474d3.
- Outcome pilot committed/pushed56e5657. Userauthorizedfixed20normalcheck;
  COMPLETE6valroots xbaseline/candidate depth15/thread1/hash64/ON/bookOFF/
  fresh/30s,12searches,no exclusions/retries/refill. Same6strata minSHA
  20261011:id chosenbeforequality. Existingexporter/zeroSHA/canonicalguard
  reused;changed350216bytes onlyKP/PP,178static historiesmatch20candidate.
  Operationalengine+baselinefiles isolatedandunchanged;no newbuild/QS.
  Bestchange1/6(White-loss32 K7a8b->G4a5b),PVchange6/6,cpdiff-19..+56.
  White-lossline G5b,R5h,G6b centralgolddefense butlaterR5a+ invasion;
  receiveresilience/strengthnotdemonstrated. Samebaseline6best/cp/PV/nodes
  reproduced. New2guards andbyte/PV/provenanceauditpass;inputsbackupverified.
  [Outcome normal-search](docs/experiments/learning/data/2026-10-13-selfplay-outcome-normal-search.md).
  results/learning-pilot/2026-10-13-outcome-search-review-v1/report.json
  SHAd96d50ff65cc9b5b68905de49f85a957a2d204130b1df2e59454baf4af71d7e0;
  auditSHAa34498cd5d298eb775c5ff6988eae6bdcd4d77e70f25ff333a6ea6d9226e766b.
  ExportedparamsSHA4e4c73c77060b7a40e782c9daf189a67bcb7acb1fc571f34af7acd59f22f4ed5,
  isolatedonly/notadopted. Run normal-search-review-attempt-v1.json locks12.
  Correctedpriorimitationreportstrata: e3cc..:21:35 isBlackdraw,617d..:3:47
  Blackloss;oldraw/score/exclusionunchanged. No newtestgames orlearning.
- UserauthorizedsingleWhite-loss root K8bvsG5b contentcheck;COMPLETE4normal
  searches (two models xdepth15/20) restrictedMOVES[7a8b,4a5b],MultiPV2,
  thread1/hash64/ON/bookOFF/fresh/30s,no retries/exclusions/learning.
  ALL4 preferG5b. Baselinegold/kingcp depth15 -55/-140,depth20 -128/-176;
  candidate15 -149/-153,20 -198/-231. Goldadvantage85/48 baselinevs4/33
  candidate;notlearner-createdstrength. G5b supportsS5c/P6c butR3b support
  removed,castlingdelayed;PV20laterK8b. Same8PV endpoints delta0..+1cp only.
  Fixedcandidate impactssearchtree,doesnotdemonstratebetterresilience/wins.
  [King/gold contentcheck](docs/experiments/learning/data/2026-10-13-outcome-king-gold-content-check.md).
  results/learning-pilot/2026-10-13-outcome-king-gold-comparison-v1/report.json
  SHAc69b3b14af588cbfd1e8245f3b5a2c65b16ca0476eb710ca807b9a18c22092cd;
  auditSHAec2fefd988bfc6be393fc50eeec254e86b0d1148ae72645c366f89560d1fcee2.
  Parent king-gold-comparison-attempt-v1.json locks4searches. New2guards pass,
  commands/PV/staticendpoint/inputaudit andbackupverified. Runtime/books kept.
- Normal/content checks committed/pushed3d2664e. Userrequestedmoreoutcome
  learning;authorized384/96 selection/staticaudit only,conditions unchanged.
  COMPLETE PARTIAL:train383/val80 roots,supervised256/64 asplanned;
  masked127/16. Strata trainwins/losses each64,Bdraw63/Wdraw64;
  valdecisiveeach16,Bdraw14/Wdraw2. Allselectedgamesnewrelative263usedkeys.
  Underoldrun split only2unusedWhiteDraw games exist,14short beforeselection.
  Nativeactual-nextmovehistory repeats exclude3drawroots (trainB1,valB2),
  legalbutchildrepeats,notformalrepetitionadjudication. NO replacement/refill.
  Raw39train/valruns reextracted withold24-80/depth15cp/abs1000eligibility;
  no cp/feature/improvement ranking,seed20261011/SHAroundrobin,one/game,
  predeclared runcap24each (sizeallocationchange only),prefix/root isolation.
  Train31/val8run,max24each;testkeysmetadataonly,no rawtestgames.
  Saved463labels/histories/nativeSFEN-Huffman auditsmatch;3tests pass;
  oldbackup+new7files968008bytesverified. No searches/QS/updates/gradient
  extraction;runtime/books/oldcandidates unchanged,selection_completeFalse.
  [Outcome expansion selection](docs/experiments/learning/data/2026-10-13-outcome-expansion-selection.md).
  results/learning-pilot/2026-10-13-outcome-expansion-selection-v1/manifest.json
  SHA68a62bb9ba5a4abaad369ab230c9c0ee63ff93d69afa6c3c330d5c1f28fd067b;
  auditSHA89133379b680075f777d539272882de0bfec25038bb6d5a5e1400e07cfbc4cd9.
- Useraccepted383/80 partialdataset+oldWhiteDraw6 SEPARATEdiagnostic and
  authorizedconnection/scaleaudit only. PREPARATION COMPLETE469zero roots
  (383train/80newval/6old diagnostic),sameKP/PP/logistic loss/masks/updater.
  Newrawlabels/histories/packed/factors reaudited469;old6 gamesdisjointfrom
  newsets,allmasked,notcountednewval. Train-only40052keys from256decisive,
  val64decisive,draw127/16 plusold6. Initialtrainloss.7018227312 (newdata,
  notcomparabletoold .6815). L2_1e-6 capratiosmedian.601%,p90 2.223%,258
  weakkeys>25%(~.64%). Samecapstatic469max5cp,protectedlanesfixed;
  gradient10finitechecks/zero checkpoint exact. No valqualityloss measured.
  New2guards pass;oldcopies+new28files45290476bytesverified. No searches/
  QS/updates/refill/newgames/oldcandidateoverwrite;runtime/books kept.
  [Expanded outcome preparation](docs/experiments/learning/data/2026-10-14-outcome-expanded-preparation.md).
  results/learning-pilot/2026-10-14-outcome-expanded-preparation-v1/report.json
  SHA1034b6b043f079463b27e65724d016c08ceedb38f069064c6c6b58d0f0cc62c0;
  saved-label-auditSHAafd61f4f96ebcff7534af60d1b0630cca5d7b4bd8e290b211058affa069365a9.
- Userauthorized expandedoutcome20 COMPLETED unchanged256/64 decisive,
  draw127/16+oldWhite6 separate. Zero/currentbase,full256,L2_1e-6,step/rate
  .001,cap.01,average.9995,save0/5/10/20,selectedfixed20. Old96/23 untouched.
  Trainintegerloss+.07905%,smooth+.07903%;newvalinteger+.006343%,smooth
  +.000645%. ValBlack-.01581%,White+.02840%,win+.04558%,loss-.04929%;
  35valintegerchanges19towardwinner/16away. Winner-up/loser-worse persists.
  Newdraw16 changes4(mean+.125cp),White2changes1(+1);oldWhite6 changes
  [0,+1,+1,+1,0,-1],separate(mean+.333cp). No drawoutcomeloss.
  Whole469integermax2cp,smoothmax2.284;avgmax.00491140,current.00763850,
  caphits0. New3guards pass;20train-onlytrajectory/gradient/averages/4states
  exactaudit,1876packedscore/label/summary checks match;oldbackups+new8files
  60352380bytes+audit2 verified. No normal/QS/games/tuning/refill;runtime/
  books/25cp/oldcandidates unchanged. Savedcandidate,notadopted.
  [Expanded outcome result](docs/experiments/learning/data/2026-10-14-outcome-expanded-result.md).
  results/learning-pilot/2026-10-14-outcome-expanded-run-v1/report.json
  SHA4e56b5c65dd751b8875480ab93238e5e90d02452a0c4469932a809600efa7241;
  auditSHA58fb7b54f7ae6ca840622b7a17ebaa7cb05e39f711d3aaedeb138671ad191ed6.
  average-20.txtSHAf202d90b3b62f25326006f5e2875fe1f9ac281fd134b3d359eddf5a9a8e3abc5.
  Expandedprep learning-attempt-v1.json locks20;neverretry/bypass.
- Saved-data loss diagnosis COMPLETE4validation integer-up losses: earliest
  Black25,Black59/White62 largestrawsmooth,positive-staticWhite66. No new
  searches/probe/updates/games. SourceSHA/labels/rootSFEN replay match;
  PP accountsmostupwarddelta inall4 (KP+.024..+.160,PP+.688..+1.407cp).
  Early/fightingpositions cannotblame finaldefeat entirelyonrootshape;
  White62 showsreal kingpressure (P7d/G*7c). Othercases priorsearch/static
  differ,oldruntimeunknown;notproof ofblunders orcurrentstrengthdecline.
  Keep losinggames;do notdiscard unilaterally. Consultteacher weighting/
  auxiliarysearchtargets before anynexttrial;no conditionchange decided.
  [Loss-position review](docs/experiments/learning/data/2026-10-14-outcome-loss-position-review.md).
  results/learning-pilot/2026-10-14-outcome-loss-position-review-v1/report.json
  SHAd6b893d2314d74e30038cdadd0b1721749aa64880cf421e4a09e47e86e529906.
- Expandedselection/preparation/run/lossdiagnosis committed9186105;notpushed.
  Userauthorized trial: savedprogress w=.25+.75*p,normalizewithin4trainstrata to
  preserve64each/total256;zero/currentbase andallotherconditionsunchanged.
  Existing256trainprogress .195.. .820;unbalancedrawweights win79.441 vs
  loss75.756,so stratum-normalization needed. Unweightedvalidationunchanged.
  Compareterminaldistance/hybridteachers alternatives;progressfirstisminimal,
  notguaranteedfix ofsharedPP orstatic tacticalblindness. Newisolatedrunner/
  objective/auditor reusebaselineguards/updater/evaluation;7tests pass and
  actual256 finitegradient10keys maxerror3.32e-13,totalweight256 exact.
  Fixedsingle20run COMPLETED atresults/learning-pilot/
  2026-10-14-outcome-stage-weighted-run-v1;stage-weighted-attempt-v1.json
  inexpandedprep locksrun. Weightedtrainloss+.08570%,equaltraininteger
  +.08090%/smooth+.07891%. Valinteger+.006342%/smooth+.002043%;previous
  +.006343%/+.000645%. Valwin+.04558%/loss-.04930% integer;loss smooth
  -.04829% vsold-.05016%,stillworse. Black-.01218%,White+.02479% integer.
  Val37changed20better17worse;oldcandidatevsnewval80only2integerchanges,
  max1cp(oneBlacklossdown,oneWhitelossup). Drawval16/old6 integerunchanged
  versusoldcandidate;baselinevaldraw4/16mean+.125cp,old6+.333cp.
  Whole469maxinteger3cp/smooth2.388;avgmax.00491108,current.00763567,
  caphits0. Full20trajectory/averages/weights/4checkpoints and1876packed/
  label/summary checks auditedexact;oldbackup/new13files212950151bytes+
  audit2 verified. No additionalsearches/QS/games/tuning/adoption;baseline
  runtime/books/25cp/oldcandidates preserved. Candidate saved,notadopted.
  [Stage-weighted result](docs/experiments/learning/data/2026-10-14-outcome-stage-weighted-result.md).
  reportSHAe5761371cb3d48ce22a5c55b2c7e686421782bd4f50a8ecabc323e7998dc7344;
  auditSHAa36b075a59c8d06e64cd73b6442ad45e6cdfbe26ae39536b15d759e628886efc;
  average20SHAa9fa96a514378dc31513609bf850323f341a4e4d5caadcecb23a57fd6cfd8605.
  [Stage-weighting plan](docs/experiments/learning/data/2026-10-14-outcome-stage-weighting-plan.md).
- NEXT consultnextdirection;stage-weightedtrialclosed.
  Expandedtrialclosed;no automaticfurther
  learning/tuning/refill/reselection/dataextension/search/games/adoption.
  Userrequestedcoarsecommit ofstage-weightedimplementation/plan/results;
  pushnotrequested. Existing7tests andsaved-resultaudit passed.

## Next research direction: thickness and territorial control

- The user wants to explore thickness as a defining Shin-Yonenaga-Gyoku style;
  a stylistic feature may be worth adopting even without measured strength gain.
  Keep style effects and strength evidence separate in any future decision.
- Web consultation suggests thickness is useful, sustained control of an area
  for both attack and defense, not a universal numeric pattern. A high pawn
  foothold supported by gold/silver can both enable progress and deny the
  opponent a foothold. See [厚みを作るときに意識すべきこと](https://sakurai-shogi.com/araki-20240216/)
  and [厚い: 将棋用語](https://xn--pet04dr1n5x9a.com/%E5%B0%86%E6%A3%8B%E7%94%A8%E8%AA%9E/%E5%8E%9A%E3%81%84.html).
- Keep candidate aspects distinct: supported pawn territory, gold/silver
  advancement, safe king placement, and local influence around a meaningful
  front. Raw whole-board attack counts can reward irrelevant control; local
  attack balance is better treated first as a diagnostic. Traditional
  Hashi-gyoku Ginkanmuri descriptions are references, not direct definitions
  of this engine's Shin-Yonenaga-Gyoku.
- Three train-run games/four windows have now been reviewed. User agreed to
  investigate usefulness using current-evaluation teachers, with ONE feature:
  count unpromoted fifth-rank pawns on files3-7 directly defended by an own gold
  or unpromoted silver, once per pawn. No control-surplus gate, advance-distance
  bonus, or king feature. Signed coefficients;single20-update trial now closed.
  Evidence and limitations: [supported-pawn review](docs/experiments/learning/gold-silver/2026-10-12-supported-pawn-thickness-review.md).
- Existing143/35 frozen leaves checked statically: presence49/10; Black-owned
  pawns27/5,White-owned22/5;nonzero net49/10,max2per side. Draw presence15/47
  train,4/12validation;validationBlack-loss stratum0/6. No automatic refill.
- Update0 preparation/audit complete with new supported-pawn-probe and
  tools/learning/gold_silver/supported_pawn_preparation.py (no --run entry).
  Frozen teacher/leaf hashes preserved;native178 baselines and356 root/leaf
  independent counts match;zero candidate matches old178 cp baselines.
  L2 fixed1e-6:train gradients[-3.4664e-6,-5.9175e-6],cap regularization
  ~14.4%/8.45% of initialsignal. Coeffcap.5cp,20updates/batch128/seed20261011.
  Four static perturbations includingcaps give max1cp whole-position difference.
  New4+existing3 focusedtests pass;local independentbackup190files verified.
  Report: [preparation audit](docs/experiments/learning/gold-silver/2026-10-12-supported-pawn-preparation-and-scale-audit.md).
  Saved results/learning-pilot/2026-10-12-supported-pawn-preparation-v1/;
  reportSHA060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4.
- Preparation committed16b4c49 before actuallearning. One20-update run complete
  with same143/35/L2/settings,selected0(no improved validationcandidate).
  Saved20avg[+.240306,+.241382]cp per pawn,raw[15748,15819];current20delta
  [+.380489,+.376393],capsnotreached. Trainintegerloss~.006466%improves;
  validation~.024816%worsens:White~.053319%worse,Black/drawunchanged.
  Validationonly1leaf changes1cp;Black-supported6e/7e withS7f getsbonus,
  Whitebase272->271 while savedteacher646. Whole root/leaf max1cp;
  smoothmax~.482cp. No strength/style benefit demonstrated.
  New4guardtests pass;20step RNG/gradient/trajectory and4checkpoints replay
  exactly;old190+new10backupfiles verified. All runtime/books/oldcandidates kept.
  Report: [learning result](docs/experiments/learning/gold-silver/2026-10-12-supported-pawn-learning-result.md).
  results/learning-pilot/2026-10-12-supported-pawn-run-v1/report.json SHA
  39dd3c5a4817e8c9ee99adca77dff55773df874e07300e31d2efd9e981019650.
  Prepdir learning-attempt-v1.json locksrun;neverbypass. Allcandidates saved.
- Supported-pawn result implementation/report committedc345e5f. User wants
  to finish thickness investigation before considering theme-free learning.
- Closed Gold experiment: supported gold advancement, reviewed in3train games.
  Score own unpromoted gold defended by another gold/unpromoted silver:
  ownrank1-2=0,3=1,4=2,5or further=3. Allfiles,once per gold,no king bonus
  or control-surplus gate. One-hop support still counts some fragile chains.
  [Gold advancement proposal](docs/experiments/learning/gold-silver/2026-10-12-supported-gold-advance-proposal.md).
  Saved reviewSHA13867a499ce997900e947c1add9e0f890d51c64ae28ebc08952db3ef8da49f07.
- Existing143/35 leaves: presence41/15,nonzero net36/12,maxscore2.
  Qualifying gold occurrences at ownrank3:44train/17val;rank4:2/2;rank5+:0/0.
  Main limitation:24-80ply sampling misses deep rising formations. Train-only
  initialgrad[-2.8616e-6,-3.8098e-6];L2_1e-6 capratio~17.5%/13.1%.
  These were pre-supplement measurements;later preparation/result below.
- User authorized the small supplement. Selected16train/8fresh-validation
  roots from savedgames:8side/height/support buckets each2/1,Shin own foremost
  gold only,one root/game,seed20261011,window24-120,run caps4/2,no outcome/cp
  quality selection. Exclude239previously used games andcross-split/test keys.
  All24 native histories legal/SFEN-Huffman exact,no exclusions/refill. Roots
  train87-116ply/12runs,val82-116ply/6runs. Supplemental draw3train/0val;
  if allaccepted combined159/43 hasdraw50/12. Some attacking golds included.
  Selectionstage:5tests pass;oldbackup+19newfiles verified,teacher/QS/updates0.
  [Supplement preparation](docs/experiments/learning/data/2026-10-12-gold-advance-supplement-preparation.md).
  results/learning-pilot/2026-10-12-gold-supplement-preparation-v1/manifest.json
  SHA06d59cc954ccae8e464b05b26f3c3fe4eb3008b23d6a538aa08267ae90dc1938.
- Authorized Gold teacher/leaf preparation is complete: additional16/8 all
  accepted;combined159/43,draw50/12. No exclusions/retries/refill,updates0.
  Old178 teachers/leaves reused byte-identically;new24 depth15 teachers and
  new24 qsearch calls only. Runtime/books/25cp unchanged;no adoption.
  [Teacher/leaf and zero audit](docs/experiments/learning/data/2026-10-12-gold-advance-teachers-and-leaves.md).
  Goldprep report results/learning-pilot/2026-10-12-gold-advance-preparation-v1/report.json
  SHA99c40167875f063baaea07052c5a6c161f5a272edd8f1910498b6aa9852002fc.
  Goldteacher report SHA7688a8e3df760a389f327a55a67632798ad6f41c510b48f53807b37622896951.
- Goldleaf presence52/19,nonzero net46/16;values2 gold7/4,values3 gold5/3.
  Supported4th-rank-or-higher goldpositions10/6 (newsubset8/4 allownside).
  Initialtraingrad[-2.121850831e-6,-3.800665585e-6];L2_1e-6 atcap.5
  ratios23.56%/13.16%,needs_reviewFalse. Opening signal close to25% guide.
  Zeroevaldiff0;static cap perturbations wholepositionmax3cp;no validationloss
  measured. Newprobe results/gold-advance-tools/gold-advance-probe
  SHA7735d0cbf2bccdfefb9474643e413c5b3913a40da0824947562cf8b7ba1074f0.
  Makefile/oldprobes unchanged;native20fixtures and9focusedtests pass.
  Preservedparent190+selection19 copies;new38files backedup/verified.
  Saved-results read-only audit accepted;404 root/leaf independentcountchecks,
  normalizedcrosssplit/test-key overlaps0. No test quality or newtestgames read.
- User authorized one20-update Gold run;COMPLETE and closed,no adoption.
  Same159/43,L2_1e-6,batch128,seed20261011,rate/step.05,cap±.5.
  Selected5 by unchanged integer-validation+L2 rule;average[+.107318,+.115765],
  raw[7033,7586]. Integertrain improves.010856%,validation.001307%:
  Black.002520%,Whiteunchanged,draw.004826%;only2validationleaf1cpchanges.
  FULLPRECISION validation WORSENS .001569%,so tinyintegerbenefit isrounding
  sensitive. One improvedexampleisattackinggold,notpuredefensivethickness.
  Average20[+.228069,+.233064],raw[14946,15274],integertrain+.021327%,
  validation-.041141%,White-.079511%,draw-.143246%. No caphit.
  Wholepositionmax1cp(selected5),2cp(trainroot20);smoothleafmax~1.396cp.
  All4 candidates and20trajectory saved. Fournewguards pass;arithmetic
  RNG/gradient/trajectory/4checkpoints audit exact;oldbackups+new22files and
  audit2files verified. No newteacher/qsearch/normal searches/games/testquality.
  Runtime/books/25cp/oldcandidates unchanged;no additional tuning/extension.
  [Gold learning result](docs/experiments/learning/gold-silver/2026-10-12-supported-gold-advance-learning-result.md).
  results/learning-pilot/2026-10-12-gold-advance-run-v1/report.json
  SHAcc92ce508ed449d09697d3ca101b7e24b1f22f9eddc510aca3327d171e48ca60;
  auditSHA5ec0cc12f5fb3f29b736ab7f59343501624212d1707b2e6ffebac7b03d8b3b91.
  Goldprep learning-attempt-v1.json locksrun;never remove/bypass.
- User authorized final qualitative check of BOTH front gold/silver and
  union-of-three-forward-square geometric control balance. COMPLETE:
  same3train games/11snapshots,searches/updates0,no validation/testgame reads.
  C105/114/115 has3/3 superiorcells yet supporterG5f getscaptured116;
  B68/88 worksinlocaladvance/recapturewithoneinferiorcell. A59 initially
  superior5/6 yet N*5e capturesS6g66;Grecapture67 restoreschain.
  Pins/drops/exchanges notmodeled;thissimplefeature cannotdetectweaksupport.
  Featureheld,no learning/extension/adoption. Runtime/books kept.
  [Front gold/silver review](docs/experiments/learning/gold-silver/2026-10-12-front-gold-silver-control-review.md).
  results/learning-pilot/2026-10-12-front-gold-silver-review-v1/review.json
  SHAb6a1191e4a66bf39dfe791f83d28d759af10eff6932907ec8357c638b304b0b4.
  Geometrysanity+11colorrotationchecks pass. Goldpilotcommitted767642e.
- Front gold/silver review committed8e3e77e. Thickness phase closed;user
  requested transition to learning from the TWO historical Shin games.
- TwoKIF input preparation COMPLETE: local/kifu/2011-12-21-bonkras-yonenaga-prematch.kif
  and2012-01-14-bonkras-yonenaga.kif,CP932,SHAverified. Nativeall198moveslegal,
  Board/nativeallSFENmatch,CSA2lineDB roundtrip exact. BothWhiteYonenagalosses;
  White decisions42+56=98,93uniquepositions,5shared. No wins/draws.
  No train/validation split assigned,no searches/updates,all runtime/books kept.
  [Two-game input preparation](docs/experiments/learning/data/2026-10-12-historical-two-game-learning-preparation.md).
  results/learning-pilot/2026-10-12-historical-two-game-input-v1/input.json
  SHAea00042097935e0174ac3bcd1c7f9165e809476cb1ff427b300fb741cd88fedb.
- User authorized small actual-vs-alternative comparison;COMPLETE8roots:
  eachgameWhiteplies22/42/62/82 fixedbeforesearch,16fresh depth15 searches,
  thread1/hash64/ON/bookOFF/30s. SameoperationalSHA isolatedbaseline reused.
  Allcompletedcp/legalPV,no exclusions/retry/refill. Actual=best2/8.
  Samebestprematch82 N*7c differs449cp unrestrictedvsforced;separate-tree
  scorescannotbeusedasreliablequalitygate. No coefficient updates.
  results/learning-pilot/2026-10-12-historical-move-comparison-v1/report.json
  SHAd7825b838e41f8f544107874ef6571e6c1e65cfae250274b0c19d013dcd9dacd.
  Inputdir move-comparison-attempt-v1.json lockscomparison;neverretry/bypass.
  Savedcommands/PV/cp audit16 pass;new7files backupverified;runtime/books kept.
  [Comparison and pilot plan](docs/experiments/learning/data/2026-10-12-historical-move-comparison-and-pilot-plan.md).
- User authorized sparseKP/PP imitation PREPARATION;COMPLETE6/6pairs,
  new12qsearchcalls,zero47leaves+41roots match baseline,updates0,no refills.
  7190activecoefficients(KP1138/PP6052);4801 appearinonepair only,6pairs
  insufficientforgeneralization. KP3scorelanes/PP0,2 only;progress/tempo
  protected. Canonicalmirror/color/swap keys;nativeactualtableperturbation
  verified,47symmetrypositions,88zeroevalpositions,5focusedtests pass.
  [Sparse prep and scale audit](docs/experiments/learning/data/2026-10-12-imitation-sparse-preparation-and-scale-audit.md).
  results/learning-pilot/2026-10-12-imitation-preparation-v1/report.json
  SHAc119a11de5a9b53655c0396ade1deb3da5d0491516710675b2f822da9f22cc96;
  saved-results-auditSHA4a701a83029fc3d5ec63c4d1c7814b3e1e6ef767bdddc808ab3b61b85bd45116.
  Sourcecomparison imitation-leaf-preparation-attempt-v1.json locksqprep.
  Nativeprobe results/imitation-tools/imitation-probe
  SHA5885a3f7334cc0654b8f6b8c2ffc21f76dbbaadee57b537975d7ff1c5572fd0c.
  Oldverifiedbaselinecopies reused,new11files+audit4backupverified.
- User acceptedperkeycap±.01 andone20update;COMPLETE/CLOSED.
  Full6pairs eachupdate,L2_1e-6,RMSprop rate/step.001/decay.9975/eps1e-12,
  averaging.9995;save0/5/10/20,fixed20averagecandidate(no reselection).
  Pairintegergaps[-14,286,570,37,-133,412] ->[-16,283,566,34,-137,409];
  all6move towardactual by2-4cp,nonechangesorder. Pairlossinteger improves
  .34529%,fullprecision.34774%. Thisistrainingfit,notstrength/styleproof.
  Val35integerteacherloss+.10548%,Black+.11294%,White+.09691%,draw-.02126%;
  smoothall+.07790%,draw+.10609%(roundingreversesdraw sign). 11valleaf1cp
  changes;root9/35,trainroot2/6. Wholepositionmax2cp,smoothmax2.508cp.
  Finalavgmax.0049146cp,currentmax.00764364,capshits0;all7190rawnonzero.
  New5tests pass;20trajectory/gradients/4checkpoints exactarithmeticreplay;
  nativepacked352score checks match. Oldbackups,new11files+audit2 verified.
  No newsearches/qsearch/games/dataset changes;runtime/books/oldcandidates kept.
  [Imitation result](docs/experiments/learning/data/2026-10-12-historical-imitation-first-result.md).
  results/learning-pilot/2026-10-12-imitation-run-v1/report.json
  SHA8738582ae7a3590e87140b240b905a458510d1af6f11d7d4c34f2edee6845707;
  auditSHAced22e4266f2a2208476d2ba99ed2ff6ae84a740be5b7b6d6c40600d5ebacabd.
  Candidateaverage-20.txtSHAe13e34bcfd26ba99e5baf3a65bb15f1684685ab882bb102706b5fe3e367c5e8b,
  probe-only sparseoverlay,NOToperationalUSI. Prep learning-attempt-v1.json locks.
- Two-game pilot committed/pusheddf1f7d4. User authorized saved20only normal
  searchcheck;COMPLETE12rootsx2 depth15/thread1/hash64/ON/bookOFF/fresh/30s.
  Fixed6train+6oldvalidation(1/sixstrata,minSHA20261011:id,no score/feature
  selection);no extra learning/tuning/reselection/refill/testgames.
  Exporter reusedfrozenprobe patch,zeroexportSHA=baseline,changed97234bytes
  onlyallowedKP/PP lanes;88static fullhistories reproduce saved20candidate.
  Candidateenginebyte-identicaltooperational inisolatedruntime;sourcebin kept.
  Trainbestmovechanged3/6,actualbest0/6,PVchanged6/6,cpdiff-126..+114.
  Diagnosticbestsame6/6,PVchanged6/6;5validcpdiff-15..+187;candidateBlack-draw
  id e3ccacfa..:21:35 PVrepetitionexcluded,no refill/retry. Smallstaticdelta
  changessearchtree;searchscoreincreaseisnotstrengthproof. Baseline6best/cp/PV
  matchpriorcomparison;1nodescount differsby1(recorded). No adoption.
  [Normal-search result](docs/experiments/learning/data/2026-10-12-historical-imitation-normal-search-review.md).
  results/learning-pilot/2026-10-12-imitation-search-review-v1/report.json
  SHA5d18c80d6d39c4336e8c69e2f15e3dd0ed74168fbff64d0a36712c6d2f433726;
  auditSHAf29fb8d802909687b06b34b40d8de5e8dd464e43bca27e9361de5da1f964ce70.
  ExportedcandidateparamsSHA5483b619c17a675891187526c7839db0f6d28e7c5b01422aa3e376b855126b10,
  held inisolatedcandidate/bin/params.bin,NOToperational.
  New3tests pass;commands/PV/bytes/auditsverified,new11files backedup.
  Run final-search-review-attempt-v1.json locks24searches;neverretry/bypass.
- User requestedcontinue withdata-design consultation;DESIGN ONLY complete.
  Recommendprematch train/Denousen validation,operational-basezero restart,
  notold20continuation. Afterply20:32/46White roots,unique32/46,crossgame0.
  Bothlosses,no win/draw. Propose12/12 evenlyspaced White roots
  floor(i*(n-1)/11),i0..11;no score/featurequalityselection. NOTyetselected.
  Atmost48normal+48qsearchforpair prep;reuseidenticalsaveddataafteraudit if
  available,no oldattemptbypass/refill. Estimatefewminutes..10min provisional;
  48normalx30s timeout=24min upperbound,QS extra.
  [Game-level design](docs/experiments/learning/data/2026-10-12-game-level-imitation-data-plan.md).
  results/learning-pilot/2026-10-12-game-level-imitation-design-v1/design.json.
  Old2games BOTHalreadyused:prospectivegame-leveltransferdiagnostic only,
  NOTunseenvalidation. Valgame mustnot contributegradient/keys/L2selection.
  KeepKP/PP/cap.01/position10,outcomelossOFF;old35side/drawguards.
  Separatecorpus47runs train31/val8/test8 onlyfuturestrength-learning route,
  notautomaticallymixwithhistoricalimitation;maxplydrawoutcomemasked.
- User authorized12/12selection+staticaudit,requestedavoiddeepchasing.
  COMPLETE24/24nativehistories+actualnextmoves legal/SFEN-Huffman exact,
  no repeatedhistory,exclusions/refill0,crossgame root overlap0.
  Trainprematch plies[22,26,32,38,44,50,54,60,66,72,78,84];
  ValDenousen[22,30,38,46,54,62,70,78,86,94,102,112].
  No newnormal/QS/updates. Actualusablepairs notyetknown(endgame mayexclude).
  Reusablebaselinecomparisons train22,val22/62;atmost42newnormalafterreuse
  identityaudit,QS cap48. No rerunofclosedattempts/replacementifreusefails.
  [12/12 root prep](docs/experiments/learning/data/2026-10-12-game-split-imitation-root-preparation.md).
  results/learning-pilot/2026-10-12-game-split-imitation-roots-v1/manifest.json
  SHA95eb72a4849025fcf7498c7b751b3c3d387c86cc3bfb0ef82ace7730dd67bc67;
  auditSHAc16cd92136a6047244a5e0bbf2a0de629265c49e76b2a000161e959fdcaac817.
  Threefocusedtests pass;input/source/selectionaudit andold/newbackupsverified.
  Runtime/books/25cp/old20candidate unchanged. Pendingcpteachersnotgenerated.
- User steered2026-10-13: adoption reservedforfinaldecision;furtherstudy
  permissibleifpromising. Do NOTretainold automatic"hold/closeevenifpromising"
  ascurrentinstruction. Currentevaluation/books remain until explicitadoption.
- Transferprep attempted42new+6reused comparisons;47responses saved/audited,
  lastforcedDenousen112 recordmissing becauseForcedmove-mismatchguard
  mishandledspecialterminal. Unrestricted112 alreadyresign/mate,excluded.
  Preservedfailedreport+source;fixedguard andmockregressionpass. NOsearchretry,
  refill,markerbypass. Saved4train/4validation pairs finishedSTATIConly.
  Eachsplit7same-best(no pairs),1terminalexcluded. QS16calls only.
  Newpreparedstats trainkeys5391 fromPREMATCHONLY,no validationgradient/keys,
  L2capratiosmedian.00952%,p90.0671%,max.4977%;crossgame leaf overlap0.
  Zero110positions match,cap auditmax5cp. 1incompletesource response disclosed.
  results/learning-pilot/2026-10-13-imitation-transfer-static-audit-v1/report.json
  SHA392ea00497689cbe0ecc917f0ff9cbdb7a6558f459129311fc72de61353bbcce.
- Authorizedcontinue one20 transfertrial COMPLETED unchangedsettings:
  full4trainpairs,L2_1e-6,cap.01,step/rate.001,average.9995,fixed20average.
  No outcomelearning. Trainintegerloss improves.3354%,smooth.3509%;val
  integer+.0345%,smooth+.0357%. Alltrain gapsimprove1..4cp;valonly1/4
  integergapimproves1cp,3unchanged;smooth3improve/1worse. No rankingreversal.
  Old35diagnostic integerall+.0910%,Black+.0399%,White+.1498%,draw-.1216%;
  smoothall+.0207%,Black-.00618%,White+.0517%,draw-.0741%. Changesmax1cp.
  Whole110integermax2cp,smoothmax2.588;avgcoeffmax.00494164,current.00770102,
  caphits0. Train-only20gradient/trajectory/4checkpoints exactaudit and440packed
  scorechecks match. New2prepguards+1terminalregression+2pilotguards pass.
  No candidate normalsearch/games,tuning,refill/split swap. Runtime/books/old
  candidates intact. Candidate saved,notadopted;decision stillopen.
  [Transfer result](docs/experiments/learning/data/2026-10-13-game-split-imitation-transfer-result.md).
  results/learning-pilot/2026-10-13-imitation-transfer-run-v1/report.json
  SHAaa2d78166e3558f2c376ffa8dfe12577b89a7cdcf8ce14c2a234f813662410a2;
  auditSHAcf285107bbd35995362815c2f6df79f02ece9726559742f907eb03957fac6cc9.
  average-20.txtSHA7f1a6e4b35353ad307a0ee6fda8eca1b68b9d13262c16f7b4356510e7203fb9b.
  Rootprep transfer-preparation-attempt-v1.json andstaticprep learning-attempt-v1.json
  lockoriginalattempts;neverretry/bypass. Failedprep provenance staysimmutable.
- NEXT discuss finaladoption/depth decision. Tinytransfer signal notrobust:
  only4previouslyexposed valpairs/1integercp benefit,draw mixed. Recommend
  pause this2gamepilot rather thanincreasecoefficients;further independent
  evidence wouldbe neededforadoption/deepening. User hasnotordereddeployment
  ornewdataset. Userrequestedcoarsecommit+push ofnormal-search/rootprep/
  transferimplementation andreports;check git history/status for revision and
  remote synchronization. No further experiment requested in this save step.
- Deferred ideas: historical2games and Doronuma-ryu Furibisha-yaburi can guide
  motifs;no book ingestion/new dataset authorized. Theme-free game learning
  using moves/outcomes is for AFTER the thickness phase. Native Gikou combines
  move imitation,win/loss prediction,depth consistency and resets parameters;
  a current-base delta route would need separate planning. Our pilots use
  current-base cp teachers and do not explicitly teach Yonenaga's style.
- User knows Shogi but not learning: explain effects with piece coordinates
  and concrete worked/failed formations,using plain language.
- Old gold-silver examples already exposed games23/50 of test run
  `shin-black-silver38-pawn76-trial-r2`; this turn reread them before confirming
  the split, then excluded them from new case selection. Keep this exposure
  documented; do not rebuild splits or claim those games are unseen test data.

## Repository organization and data safety

- Tools and tests are physically grouped by books, analysis, and learning
  themes. Their usage and build details live in `docs/development.md`; avoid
  adding inventory/status prose to README files.
- Progress, current decisions, next steps, and temporary execution limits live
  here. READMEs describe directory roles, usage, and links. Experiment reports
  preserve methods, outcomes, uncertainty, and historical decisions.
- Raw games, search outputs, checkpoints, and audit JSON live in ignored
  `results/`. Reports record paths and SHA-256 identities. Historical audit
  metadata may contain old source paths; use its recorded revision or preserved
  source copy when reproducing old results.
- Important raw data has not been independently backed up outside this
  workspace. Never delete originals before a separate backup is verified. Keep
  third-party KIF and large raw game logs out of Git.
- Public documentation must use repository-relative paths or neutral
  placeholders, never personal home-directory paths. Avoid causal or strength
  claims unsupported by the experiment design; small game/search samples are
  descriptive.

## Recent repository maintenance

- Experiment reports are grouped under `docs/experiments/{books,learning,
  openings,selfplay}/`; each theme README is a durable index. `configs/` and
  `positions/` remain at their established paths.
- Two supplemental White-book analyses formerly kept in ignored `results/`
  are now tracked under `docs/experiments/books/white/`; parent report links
  point to them. Raw JSON remains in `results/`.
- Book source JSON is grouped under `books/sources/`, held candidates under
  `books/experiments/`, and retired reproducible sources under `books/archive/`.
  Active book text paths and contents were preserved during cleanup.
- Tools and tests were moved into category packages; imports and CLI entry
  points were updated. The last full verification after that move passed 196
  tests. No engine/evaluation code changed in the organization work.
- `docs/development.md` now covers build, tests, and durable data safeguards;
  dated learning-stage instructions belong in experiment reports.
- Previous pushed research-direction checkpoint: `52c8a33`. Recheck `git status`
  and recent history on resume; the supported-pawn review is a later change.
