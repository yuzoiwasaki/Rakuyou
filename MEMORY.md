# Rakuyou resume map

Updated 2026-11-14. Read this on resume; open linked reports only as needed.
This file holds current state, durable constraints and next steps, not a changelog.
Earlier details remain in experiment reports and Git history (`a87f406:MEMORY.md`
is the last full historical map). Historical NEXT headings are not active tasks.

## Current objective and collaboration

- **NEXT: review completed rank0/10 eight-game batch (do not rerun)**:
  [Result/audit](docs/experiments/rank-counter-match-2026-11-14/result.md).
  User completed8 in~3h. rank0 1W3L; rank10 2W2L; four scored pairs mean+0.25.
  Read-only audit8 histories/1151 timed go/252 bindings/options/env/clocks passed.
  Black central bothlose; Black static bothwin; White fourth bothlose; White
  third rank0lose/rank10win. Third-rook FIRST divergence is NORMAL Black17
  S6g vsK2h, so not clean correction causality; fourth also normal-side19.
  [Paired viewer](results/teatsui-rank-counter-match-2026-11-14/review.html)
  all4 pairs,1247 native-matched states. Defaults08/07(left0/right10), compare
  BOTH WHITE/TOP; starts40, inspect48/60 for central counterplay vs retreat.
  USER prefers RIGHT/rank10: left allows8-file breakthrough and suppression;
  right adds defenders and has S*7f counterplay. Record as favorable style case,
  not causal/strength proof. Viable defense should still add pieces; do not
  turn unsustainable-support avoidance into blanket abandonment/no-reinforcement.
  NOW review Black central games01/02, user requested; [focused viewer](results/teatsui-rank-counter-match-2026-11-14/review-central.html)
  opens44, compare BOTH BLACK/BOTTOM; left0/right10. Check44/48/58, optional72.
  First divergence23 P1f/P9f, later opponent plans differ. Left admits promoted
  silver6g but uses R5d/P*5c; right DOES push P5e47, king-side exchanges follow,
  and R5i is captured72. Do not frame as unconditional refusal to attack.
  USER judges central pair roughly equal: right counterattack intent visible,
  but enemy attack arrives first; wants early N3g to restrain it. Left interesting
  but wants G7h against S7f. Key: restrain/slow enemy so counterplay arrives in time.
  No rank0/10 superiority verdict; preserve both as timing/defense examples.
  Bounded diagnostic now checks left37 P5e/G7h at after36(rank0), right41 P9e/N3g
  at after40 and45 R5i/N3g at after44(rank10); same coefficients, no tuning.
  Frozen known12-ply starts2,3,4,5; support10/D10/ShinON vs fixednormal,10s/d15,
  no tuning or adoption. Prepared scripts/tests and initial failed setup archived.
  No new searches this audit/review turn. User authorized incremental commits.

- **Timing diagnostic completed; next user review, no tuning**:
  [Report](docs/experiments/counter-timing-2026-11-14/result.md),
  [candidate viewer](results/teatsui-counter-timing-2026-11-14/review.html).
  Exactly3 fresh10s restricted MultiPV2 searches;84 legal PVs,115 native-matched
  viewer states, frozen inputs unchanged. Same original per-game rank0/10.
  Common d14 Black: left37 P5e−77/G7h−120; right41 P9e−187/N3g−435;
  right45 R5i−356/N3g−491. G7h PV retains P5e central attack; no tactical
  refutation established. N3g meets P*2e/Px2e/Nx2e: at41 P*2f/Nx3g+/Kx3g;
  at45 Nx2e/Rx2e, allowing opponent activity. Earlier P3f/N3g preparation
  untested, not refuted. Do not force root moves or add arbitrary bonuses.
  Viewer BOTH BLACK/BOTTOM, LEFT played-candidate new PV, RIGHT suggested PV
  (NOT rank0/10 panels). Dropdown for37/41/45, defaults37.
  USER prefers G7h and suggests retreat/advance instead of taking P4e later.
  Current bounded check: selected G7h PV after46 P4e, all8 legal moves of
  Black S3f/S4f, rank0/support10/D10, one10s MultiPV8 search, no tuning.

- **Silver-choice follow-up completed, no tuning**:
  [Report](docs/experiments/silver-choice-2026-11-14/result.md),
  [viewer](results/teatsui-silver-choice-fixed-2026-11-14/review.html).
  Root selected G7h PV after46 P4e (not actual game); all8 legal S3f/S4f moves.
  Initial10s MultiPV8 stops within d11, lower rows mate−2 are not established
  mates; diagnostic-only. One justified additional fixed-depth11 run (11.3s)
  completes all8, rank0/support10/D10 unchanged: S4f5g−246 first, S4f5e−437
  second, both Sx4e−509; other silver moves−1139 or worse. All Black-view.
  Retreat PV S5g/R5b/Rx5b/Gx5b/R*2a/B1c/S6h/R*5h; counterplay retained.
  All176 emitted PVs legal,201 displayed states native matched, bindings intact.
  Viewer BOTH BLACK/BOTTOM; LEFT prior S3fx4e, RIGHT dropdown alternatives,
  defaults S4f5g. Await user review. No superiority/adoption claim.
  IMPORTANT: timed MultiPV depth labels alone do not certify completed iteration;
  engine prints partial candidate results on time limit. Distinguish from fixed
  completed-depth output, never interpret sentinel mate rows as proven mates.

- **User P*5d idea after49 checked, no tuning**:
  [Report](docs/experiments/pawn-interpose-2026-11-14/result.md),
  [viewer](results/teatsui-pawn-interpose-2026-11-14/review.html).
  Selected G7h/S5g PV after48 R5b: P*5d/Sx5d/RxN3c native legal; Silver5d
  blocks rook5b ray but Bishop2b still controls3c. Four completed-depth12 MP2
  diagnostics (3 planned + direct Rx3c comparison),96 legal PVs/94 board states.
  Root48 Black RxR−98 vsP*5d−173. White afterdrop prefers P*5f+265 vsSx5d+234,
  moving S5g before taking. AfterSx5d unrestricted Black Bx3c+−174/RxR−392;
  targeted directRx3c−333 vsBx3c+−47. Do not compare values across searches.
  Bishop-first Bx3c+/Bx3c/Rx3c retains dragon; directRx3c/Bx3c/Bx3c+ gives
  opponent a rook. User idea valid geometry, not forced reply or winning proof.
  Viewer default49 choice; dropdown capture order/White replies, explicit sides.
  Await review; unchanged rank0/support10/D10, frozen inputs verified.

- **CURRENT review: White fourth-rook pair; earlier branch closed**:
  User explicitly stops G7h/silver/P*5d investigation here. Preserve lessons,
  no further searches or move-specific tuning on that branch.
  [Focused viewer](results/teatsui-rank-counter-match-2026-11-14/review-fourth.html)
  games05/06 left0/right10, BOTH WHITE/TOP, opens44; inspect52/64/74.
  Left bishop trade/R2b then2-file/edge attack; right S8d44/R5b46/N7c48,
  S5d52 against P5d while7/8-file pawns advance. Bothlose. FIRST divergence
  normalBlack19 K2h/S6f, no clean causal claim.
  USER: roughly equal/neither good. Right should Px5e instead of N7c which
  becomes target and is captured; wants to repel silver. Left dropped bishop
  cramped, edge attack somewhat forced. Native legality only:48 Px5e legal;
  illustrative49 Sx5e50 P*5d legal (pawn drop attacks silver, not Px5e alone).
  No search/forced-line proof. Next remaining batch review: Black/static bothwin;
  then summarize adoption direction without reopening deep tactical branches.

- **CURRENT: last pair review Black/static (both wins)**:
  [Focused viewer](results/teatsui-rank-counter-match-2026-11-14/review-static.html)
  left04/rank0, right03/rank10, BOTH BLACK/BOTTOM. Opens40; inspect49/59/81.
  First divergence23 G3h/S4f. Left central P5e/N3g then edge attack, giving
  S4f to B at58 while taking lance1a59. Right early3-file silver/rook activity,
  silver trade47–48/R3d49, then S*7e55/P*7d57. Bothwin, no blanket endorsement
  of middlegame or causal claim. USER slightly prefers LEFT/rank0: more natural,
  right major-piece excursions and S*7e awkward. Four pairs: third favors10,
  central/fourth equal, static slightly0. Trial held/unadopted; no tuning.

- **Trigger-pattern comparison completed (zero searches), trial still held**:
  [Report](docs/experiments/rank-trigger-review-2026-11-14/result.md).
 1247 actual states OFF/ON static checked. Games03/04(static) no hits at all;
  good07 only42 P6e: White P6e defendedS5d vs Black R6h/S7f, White−6cp.
  This is temporary attack/exchange into43Sx6e44Sx6e45Rx6e46S*7f, liked by user.
 136 saved candidate PVs moves13–80 in03/04/07/08,1756 unique prefixes legal.
 03 only1 PV hit,root62+14: WHITE P4e/S3d vs Black R4i/N3g, favorsBlack;
  no direct explanation of awkward S*7e55. 04none,07three,08twenty-one hits.
 29 active SFENs annotated by copied native witness probe; all other fields
  exactly match original. Frozen match bindings intact; no source/eval changes.
  Same2vs1 geometry in liked/disliked contexts, no supported narrowing threshold.
  Unreported search branches still unobserved: absence of game/PV hits is NOT
  proof of no indirect influence. Predicate also catches temporary attacking
  exchanges, so future design would need enduring burden vs viable exchange
  distinction, not force root moves or suppress all reinforcement. Not implemented.
  No automatic reopening of closed tactical branch. Next decision with user;
  installed support10/D10 unchanged, rank10 remains an archived prototype.

- **Current adopted baseline (2026-11-13)**: support10 + D10, separate installed
  launcher `bin/teatsui-2026-11-13/rakuyou`, engine id
  `Rakuyou support10 D10 2026-11-13`. GUI registration was NOT changed automatically.
  [Usage/rebuild/rollback](adopted/support-contact-2026-11-13/README.md).
  `ExperimentalSupportChainBonus` default10 (historical name retained), new
  `KingContactDeficitBonus` default10, both0..10; no legacy D-env dependency.
  ShinON/OwnBookON/BookMaxPly20, copied existing17-position ShinBookFile by default.
  Old `bin/release`, root `src/`, data and frozen plans unchanged. Adopted patch,
  base hashes and rebuild script tracked under `adopted/support-contact-2026-11-13/`;
  regular root `make release` still builds OLD source. Separate snapshot/build,
  validation and installation manifests in `results/adopted-support-contact-2026-11-13/`.
  130 static positions x4 settings exact parity;8 depth7 search pairs plus2
  defaults match best/score/depth/nodes/PV; installed launcher from unrelated cwd
  passed both initial Shin moves; patch reconstructs validated source exactly.
  Old experimental no-adoption/default0 statements below describe historical
  status and are superseded ONLY for support/D; other prototypes stay unadopted.
  Latest user emphasis: BASIC aim is thick shogi with supported pawn territory;
  low formation/bait/opposite-flank counter is an OPTION when support cannot
  be sustained, not replacement of that aim. No new strategic feature in the installed baseline.
- Tracked research checkpoint: [patches, source hashes and reports](docs/experiments/rank-commitment-2026-11-13/README.md). Full raw runs remain local/ignored.
- **Latest isolated counterplay-related trial (2026-11-13), UNADOPTED**:
  [Result/design/limits](results/teatsui-rank-commitment-2026-11-13/result.md).
  User authorized trying implementation after pushing baseline. Snapshot-only
  symmetric boolean 0/10cp penalty, tapered by1-progress, for advanced GS support
  of a fifth-rank pawn when enemy major attacks and geometric participants exceed
  defenders (direct plus one rear-slider layer; ignores pins/hands/tempo).
  Not an unsupported-pawn bonus or full counterattack model. Static29 positions
  pass, OFF equals adopted, full/incremental/unmake/color rotation checked.
  Exactly6 fresh10s searches,85 legal PVs, bindings unchanged. Target after33:
  OFF B7g+ vs ON P2e; common d14 White−171/−196, ON final d15−132. Neither G5b;
  OFF also does not reproduce historical S8d. ON permits Rx8e then P*8d/P3e,
  immediate counterplay, not low consolidation then waiting for commitment.
  Central and positive control pairs retain G7h / P*5d respectively, same d14
  scores/PVs. Final target OFF PV flags at added plies5–7; ON/controls none.
  No strength claim or coefficient escalation. User strongly approves ON line's
  timing (see below); do not force G5b. Installed baseline unchanged.
  Artifacts ignored under results; no long matches or new adoption performed.
  [Saved paired PV viewer](results/teatsui-rank-commitment-2026-11-13/review.html)
  now prepared: left trial0 final d14, right trial10 final d15, starts at38.
  All32 displayed states match native saved replay; no new search. Review35/38/44:
  ON gives rank to R8e, P*8d drives rook, P3e then P2f/B*5e; G remains4a.
  USER strongly prefers right/trial10: exploits Black S7f attacking commitment
  and attacks with initiative. P2e/P3e precede S7f; Bx7g+/P2f/B*5e follow it.
  This is a favorable counterplay example despite no prior G5b consolidation;
  do not force a waiting/fortifying move just to match the earlier verbal plan.
  Next bounded check: preserve favorable supported-rank cases and examine nearby
  positions; no coefficient escalation or operational adoption authorized here.
- **Fixed follow-up completed, same trial0/10, no tuning**:
  [Report](results/teatsui-rank-followup-2026-11-13/result.md), six fresh10s
  searches /85 legal PVs, bindings unchanged. Before original root(after31),
  both P8e then P2e/rank relinquishment. Approved line after39 S7f: both Bx7g+
  and identical d14 PV/−241; continuation now P3f/S6g rather than prior P2f.
  Accepted maintained-rank game07 after44 DOES change: OFF S5e4d/Gx4d/P5c+;
  ON S2g3f/P*5g/P9f/P9d/G5i retains S5e/P5d in its short final PV.
  OFF final d13−228, ON final d14−191 (ON d13−63 not stable final score).
  [Review central pair](results/teatsui-rank-followup-2026-11-13/review.html):
  13 native-matched states, starts45, left0/right10. BOTH panels compare BLACK
  (Shin), confirmed game07 metadata. Inherited White/Shin SVG label corrected
  in generator and viewer; compare lower-side Black. USER prefers LEFT/OFF:
  S3f purpose unclear, enemy already has promoted piece so attack decisively;
  liquidation/resulting position looks better. Thickness/rank are assets to USE
  at the right moment, not shapes to preserve at all times. Both preferred
  counterplay and this rejected side effect must be retained. Trial stays held.
  All final PV prefixes unflagged; off-PV branch effects not identified, timing
  differs. No claim of strength, broad safety or forced counterplay. No adoption.
- **Central-choice diagnosis (no tuning)**:
  [Report](results/teatsui-rank-diagnosis-2026-11-13/result.md). All reported
  supported-root PV prefixes:233 occurrences/97 distinct positions, flags0 and
  identical static scores OFF/ON. No direct penalty found in S4d line.
  Exactly2 fresh restricted MultiPV2 fixed-depth13 searches,52 legal PVs:
  both choose S3f−117 with identical PV; S4d OFF−335/ON−243 (different lines).
  Earlier unrestricted timed ranking reversal not reproduced under this
  different search setup. Does not refute user preference or prove causality.
  Off-PV branch effects unresolved. Do not invent attack bonus/force S4d or
  narrow predicate without evidence. Isolated tracing is now complete below;
  trial remains unadopted, baseline intact.
- **Root-branch trace completed, no eval changes**:
  [Report](results/teatsui-rank-trace-2026-11-13/result.md). Isolated binary,
  exactly2 restricted d13/MultiPV2 searches; all reported non-time info fields
  (including nodes/scores/PVs) match original diagnostic;52 legal PVs.
  Qualifying S4d-branch calls ONLY flag White:4494 OFF(observed)/5268 ON,
  no Black flags. S3f has mostly White flags plus9 calls/3 Black positions.
  All2425 distinct hit SFENs checked with original native probe. Counts include
  incremental parent/child evaluations, not independent nodes or causal weights.
  Example White P5e/G5d vs Black R5f/S4d; static effect favors Black's attack.
  No observed direct penalty on Black liquidation; don't narrow rule or force
  S4d. Historical unrestricted timed divergence remains causally unresolved.
  Next useful positional review: defenses R3b/P*5e/S*5g after S4d liquidation,
  rather than assuming trial causes all reluctance to attack. Trial unadopted.
- **Current positional review, no new searches**:
  [Standalone liquidation viewer](docs/experiments/rank-commitment-2026-11-13/liquidation-review.html),
  42 native-matched states, saved root history/PVs tracked alongside it. Both
  panels compare BLACK/Shin. Left previously preferred OFF line vs right
  restricted d13 S4d line (select OFF/ON); common through48 R3b. At49 LEFT
  P*6b but RIGHT P4f, then P*5e/R5i/S*5g. Do NOT present right's defense as
  a refutation of left; own move diverges first. Starts49, user judgment pending
  on whether P4f is necessary or immediate P*6b preferable. No eval changes.
  User authorizes incremental commits; checkpoint5680e37 archives trial/trace
  patches, source hashes and reports. No push requested in this turn.
- **Nov14 continuation and piece-name correction**:
  User correctly notes 4g4f is P4f, NOT G4f; native board confirms. Corrected
  prose/labels/tracked reports; generated move captions were already correct.
  User tentatively prefers P*6b but needs continuation before firm judgment.
  [New review](docs/experiments/rank-commitment-2026-11-13/continuation-review.html),
  [report](docs/experiments/rank-commitment-2026-11-13/continuation-result.md).
  Exactly2 fresh10s/depth15cap searches after49, BOTH correction0/support10/D10.
  Both d15: P*6b -> G7a, White+248; P4f -> S*5e, White+403. Black equivalent
  −248/−403 favors P*6b relatively, not proof of winning/superior play.
  Left +P6c/P*5e/+PxS7b/Gx7b/R9f; right now S*5e rather than ancestor P*5e.
  All30 reported PVs legal;39 viewer states native matched, bindings unchanged.
  Both panels BLACK/Shin, starts50. Await concrete continuation review; no tuning.
- Latest adoption direction (2026-11-12): user wants BOTH support10 and D10
  adopted in principle, then fine-tune concrete issues. Proceed toward deployment
  after bounded confirmation if no major problem; do not endlessly require proof
  of strength. Separate baseline installed as above; learning paused.
  [Confirmation16 instructions](results/teatsui-support-contact-confirmation-2026-11-12/README.md):
  same four arms/binaries/time controls, four16-ply starts vs fourth/static rook,
  source12-ply starts + mutual single-step1/9-file pawn development(indices0,3,4,7).
  Fixed without search/result selection; derived familiar positions, not unseen.
  [Confirmation result](results/teatsui-support-contact-confirmation-2026-11-12/result.md):
 16/16 externally complete; s0d0/s0d10/s10d10 each1W3L, s10d0 0W3L1D.
  Native audit passed16 histories/1914 timed commands/257 bindings/clocks;
  game02 repetition draw, no unresolved/errors. Combined and neither have same
  W/L in all4 starts; not equivalence or improvement proof, no pooling prior4W.
  Saved triage:04 positive late scores then187 mate−22/resign after186S*3g
  (not verified forced mate);07 all arms lose;10 R2b deployment then43B*1g
  drives R2f away and45BxS5c+;13 wins. Focused index-pair3.html at40 compares
  11/neither vs10/both, all saved boards native matched; NORMAL first diverges27.
  [User review of10](results/teatsui-support-contact-confirmation-2026-11-12/game10-user-review.md):
  after40 already bad; earlier34S8c8d forcefully supports rank and is questionable.
  User prefers34G4a5b to guardS5c, then counterattack once enemy silver advances
  and its center of gravity shifts to attack. Native G4a5b legal after33/39;
  no search, forced line or proof entire tactic prevented. Do not force rank
  maintenance before defensive coordination; not a blanket no-advance rule.
  Both10 adoption intention remains, no feature causality/new penalty decided.
  USER clarifies: keep rank only when sustainable. Here addingS still leaves
  too few participants against enemyR+S; don't force defense. Use rank as bait,
  keep low formation, counterattack after enemy commitment. Deliberate bait
  differs from passive submission; no universal count threshold/retreat rule
  or proven forced counterattack. Preserve with prior favorable maintained-rank
  examples and criticism of being pushed back, rather than overriding either.
  USER now leans toward this as better strategic direction than failed attempts
  to add eval encouraging more defensive participants: take rank, but if support
  is insufficient don't commit pieces to holding it; consolidate own camp and
  counterattack on opposite flank after opponent attacks/commits. Tentative plan,
  not unsupported-pawn bonus, forced sacrifice/opposite-flank rule, cancellation
  of support10 adoption, or authorization for a new feature/training/search.
  [Nov13 candidate check](results/teatsui-game10-gold-candidate-2026-11-13/result.md)
  after user asked about evaluation experimentation: static after34 S8d vsG5b
  bothD=0/supportraw0; White static−59/+154cp already favorsG5b. Exactly1
  fresh10s MultiPV2 restricted go, reported common d14 S8d−228/G5b−231cp;
 28 PVs native legal, bindings unchanged. G5b PV includes S7f bishop trade
  then P1e/P1f counterplay, but laterP*8d drivesS8c9b. Actual game line differs.
  Near tie not move-quality proof/approved tolerance; don't add arbitrary bonus
  to force root choice. No new eval term/weight or operational change.
  Integration completed separately as above; preserve this concrete later
  refinement case. Next design bounded improvements only when needed.
  Do not rerun completed matches/preflight. Preserve frozen experiments.
- Latest user direction (2026-11-11): investigate adoption of BOTH support10 and
  D10, with **support10 the priority** (corrects initial D-first interpretation).
  Additional matches and subsequent improvements are welcome; user chooses to
  run long matches externally. No automatic operational adoption or learning.
  [Prepared factorial16 instructions](results/teatsui-support-contact-factorial-2026-11-11/README.md):
  four arms support0/10 x D0/10, candidate ShinON vs fixed normal ShinOFF/0/0;
  four known third/central-rook starts (indices1,2,5,6), each arm Black2/White2.
  Same isolated trial binary for all candidates, depth15cap/10s/thread1/hash64,
  256 added plies unresolved. Plan sealed; local6 + existing10 tests passed;
  ten depth3 preflight searches passed. **Main16 completed externally**.
  [Result](results/teatsui-support-contact-factorial-2026-11-11/result.md):
  s0d0 1W3L, s10d0 2W2L, s0d10 2W1L1unresolved, s10d10 4W0L.
  Read-only audit passed all16 native histories,2222 timed commands/options,
  clocks and257 bindings; no searches. Game06 reached256 added plies, not draw.
  Do not rerun prepare/preflight/matches or modify bound inputs.
  Next review: pair1 games03/04 (D10 fixed, support0/10), first divergence
  candidate15 S3h2g vs P4g4f; combined-only win. Pair2 games06/07 next,
  candidate29 P9g9f vs S5g4f, unresolved vs win. Support at D0 extra win
  pair3 first diverged on NORMAL17; cannot attribute that win to support.
  Four of eight support comparisons first diverge on normal side. Combined
  result promising, not strength/synergy/adoption proof. No tuning performed.
  [Pair1 review prepared](results/teatsui-support-contact-factorial-2026-11-11/pair1-review.md):
  paired index.html starts34, all saved boards native-SFEN matched;70 static
  positions14–48 checked without search. Game04 chain P5e/S4f/G4g at33–38,
  changes to P5e/G5f/S5g at41–42 and P5e/P4f/S5g at43; game03 none14–48.
  At34 game04 K3i/R2h versus game03 K2h/R7h, so no safe/thick claim from chain.
  Later38P*4e39S5g41G5f43Gx4f45Gx5e46R4g+ is active gold play with enemy
  rook entry, not established defensive success. USER at34: left/support0 is
  more natural; right/support10 somewhat unnatural/overextended. In this shape
  rook should be on left, and too few pieces participate at4e, inviting attack.
  Chain alone is NOT a positive style example; winning does not override this.
  No exact rook square/order, blanket left-rook rule, proven blunder/bonus
  causality or numeric change. Next useful analysis: participation at4e and
  after exchanges, whether preparation could make the formation viable.
  USER elaboration: enemy attacking pieces already on4-file; avoid forcing
  advance, add pieces and contain attack. Ideas R2f lateral defense, or P2e
  preparation + P*4f to repel. Against ...R5e user revised to P2d BEFORE
  taking rook with bishop (opponent reply unspecified), not after bishop trade.
  Rook role/lateral participation matters, not a mandatory left-side location.
  Native legality only: at34 P2e legal, R2f blocked by P2f and P*4f by S4f.
  Illustrative assistant branch from28: P2e Px4e Px4e Rx4e P*4f R5e P2d
  all legal, not forced or chosen best plan. Recorded privately; no search.
  [Pair2 review](results/teatsui-support-contact-factorial-2026-11-11/pair2-review.md)
  prepared: index-pair2.html opens44, games06/07 (D10 fixed); all boards match
  saved native SFEN,50 static positions28–52 checked, no search. Right/support10
  at44 P5d/S5e/R5f cooperate vertically while enemy+S6g has entered;43R5f
  escaped that silver's attack on5h. K2h/G3h/S2g remain. Narrow support raw
  differential0 throughout both histories28–52; this P/S/R chain is outside
  feature definition. Not proof of absent search-branch effects or safe king.
  USER: right at44 is acceptable despite enemy+S6g. Contextual acceptable
  example, not safe-king/best-play/win-causality proof. USER clarified reasons:
  retained pawn territory/own positional assets, silver rather than rook invasion,
  and solid compact own-king surroundings. Assistant's rook-participation-only
  explanation was insufficient. Can allow entry if own advantage develops before
  intruder becomes effective; contextual timing, not a proven win/tempo threshold
  or blanket harmless-silver rule. Keep assets, king solidity, intruder role and
  time to effective use together; no automatic scoring change.
  USER connects this to prior Yonenaga book game10 (vs Oyama), enemy tokin
  behind pawn territory: invasion is still a negative, but build/use own assets
  to gain advantage before it becomes effective. Oct31 games10–11 dialogue
  records S6g as tokin preparation/balance, not just forward-thickness support.
  Accepting invasion does not erase its cost or mean ignoring it; avoid universal
  prevent-entry/attack-first rules and crediting thickness for all rear defense.
  [Next pair3 review prepared](results/teatsui-support-contact-factorial-2026-11-11/pair3-review.md):
  index-pair3.html opens32, upper White side; games09/10 support0/10, D10 fixed,
  both wins. Left K7a/G6a,G6c/S8c,S5c with P5e/P2e; right same K/G but
  S7b,S5c, P8e/P7d/N7c. Discuss32 then40–48, right later promotes pawn8i.
  First divergence NORMAL Black19, so no support-causality claim. All saved
  boards native-SFEN matched; no new search. USER prefers support10: support0
  rook-file breakthrough/being pushed into submission is concerning; support10
  uses tokin effectively in attack and White looks good. This is later-plan
  preference AND positional judgment, not just32 shape (tokin appears48).
  No single bad move, forced breach or coefficient causality established.
  USER clarification: tokin itself is not essential; the favorable point is
  attacking the opponent's thin area effectively. Do not turn this into a
  tokin-creation objective or piece-specific preference.
  [Pair4 review prepared](results/teatsui-support-contact-factorial-2026-11-11/pair4-review.md):
  index-pair4.html opens40, White above, left16/support0 right13/support10,
  D10 fixed; both won. Left P*8c after rook-file exchange; right bishop exchange
  and B*3c, then R2b and receives9-file pressure. First divergence NORMAL19.
  All saved boards native-SFEN matched, no search. USER roughly equal; tentative
  naturalness lean support0, support10 also not bad. Not a clear preference0.
  [Four-pair synthesis](results/teatsui-support-contact-factorial-2026-11-11/review-synthesis.md):
  pair1 prefers0, pair2 accepts10 (no explicit comparison), pair3 prefers10,
  pair4 roughly equal. Not preference win-rate tally or isolated D evidence.
  Combined remains promising candidate; no coefficient change justified yet.
  [D comparison prepared](results/teatsui-support-contact-factorial-2026-11-11/d-comparison-review.md):
  index-d-pair1.html02/04 at34; index-d-pair2.html05/07 at44, support10 fixed.
  All saved states native-SFEN matched;28 static snapshots checked, no search.
  D10/game04 is already-disliked overextension, not automatically safe due to D.
  D0/game02 is NOT earlier preferred03; no transfer of user preference.
  Next user review mainly05/07:05 king-side edge attack,35PxB3e36PxS2g+
  37Gx2g then horse lost44;07 is earlier accepted central assets/solid king.
  Black D mostly0 in sampled played states; no search-branch causal inference.
  USER judges05/D0 bad: edge attack failed and invited counterattack; prefers
  07/D10. Favorable positional/style evidence, not forced-loss or D-causality
  proof;04 concern remains. Confirmation prepared separately as above with
  coefficients unchanged; separate baseline adopted after result review.
  Do not convert containment preference into always-prevent-entry rule; this
  acceptable coordination also falls outside the narrow support feature.
  Known development sample; four games/arm cannot establish strength/equivalence.
  Keep both desirable and concerning examples; no tuning midway or pooling old runs.
- Aim for the user's preferred **手厚い将棋**. Completed thickness or a rank pawn
  is not mandatory. Do not force gold/silver advancement merely to copy a shape.
- **Astra** handles ordinary user dialogue, design, review and final-answer drafts.
  **Sol** works in the background on implementation, validation and aggregation.
  This is the user's requested division of work. The user can run long batches
  externally; avoid repeated monitoring of deterministic runs.
- User (~amateur 4-dan) supplies style preferences, concepts and counterexamples,
  not assumed best-move labels. Separate preference, positional interpretation,
  tactical correctness and measured strength; explain with concrete squares/pieces.
- Coefficients remain10/10; separate adopted baseline available as above.
  Learning remains paused; isolated rank-commitment prototype above is unadopted.
- [Private rook-foothold trial](results/teatsui-rook-foothold-2026-11-11/result.md):
  D10/support10 fixed, four timed searches. Static replay detected an enemy rook
  drop foothold after game07 handed over its rook, but both trial groups still
  chose RxB6f; positive old game10 kept P*5d. The 60cp rule remains unadopted.
  Prior [own-side](results/teatsui-local-contact-own-defense-2026-11-11/result.md)
  and symmetric local-contact trials also did not change their target first moves.
  [Saved r60 49→58 PV boards](results/teatsui-rook-foothold-2026-11-11/variation-review.md)
  show a shape the user likes but does not yet trust: beyond the saved PV,
  59R2a2b+ G2c2b 61B*3a is legal and the bishop attacks G2b/S5c. No forced
  continuation or king safety is established.
  Current unadopted experimental baseline: D10/support10/ShinON, without rook60.
  [Bounded continuation](results/teatsui-rook-continuation-2026-11-11/result.md)
  completed two fresh 10-second searches, D10/support10/ShinON, rook term OFF:
  after59 R2a2b+ chose G2c2b (reported d13, White -84cp); after61 B*3a
  chose P*5b (d12, -16cp). Both final PVs use P*5b to support S5c, allow
  B3a2b+ taking G2b, then B3b1d; White holds the captured rook. All25 PVs
  and2 bestmoves native legal, prior bindings unchanged. Different roots/scores
  are not an improvement measure. No forced attack, king safety or sound original
  exchange established. User requested only a little more: close this local check,
  no further search or adjustment automatically; discuss concrete defense if useful.
  All isolated plans, raw records and patches stay private; no operational change.
- [Private pair4 rook choice](results/teatsui-pair4-rook-retreat-comparison-2026-11-11/result.md):
  new D10 game07 after49, one timed two-move search compared the game RxB6f
  with legal R6d retreat. White-view d13 reported scores were −254/−252cp;
  retreat was the bestmove by 2cp, with materially different continuations.
  This does not establish a better defense or explain the later loss.
- Latest agreed workflow: use **bonus10 as the review/experimental baseline**,
  examine concrete discomfort as it arises, and accumulate contextual understanding
  before readjusting evaluation. Not operational adoption; default0 remains.
  Do not add a new scoring rule per example or make tools the objective.

## Current result: narrow bishop-contact versus normal

- [Private audit and viewer](results/teatsui-edge-bishop-contact-vs-normal-2026-11-09/current-state.md):
  eight saved games, four known paired starts, candidate D10/support10/ShinON
  fixed with narrow C0/100 versus original normal. C0 3W1L; C100 0W3L1 unresolved
  (256 added plies, not draw). Comparable3/4, all three C100 losses. All 246
  bindings, 1,033 timed commands and eight legal histories passed audit; all four
  first divergences were candidate moves. Narrow C was inactive in every saved
  actual position; this does not exclude effects in searched hypothetical lines.
  C100 remains unadopted and on hold; use D10/support10 as the development review
  baseline. Pair1 C100 game02 after57–64: user judged the silver retreat and
  return to take a dropped pawn ineffective, allowing a comfortable White attack;
  proposed legal 59G4i3h to support S2g and avoid that round trip. The knight
  attack remains; no best move, safe silver or C effect is proved.
  [Private note](results/teatsui-edge-bishop-contact-vs-normal-2026-11-09/review-entry-pair1-game02.md).
  [Bounded C0 comparison](results/teatsui-pair1-silver-gold-defense-2026-11-11/result.md):
  one timed two-move go preferred G3h; completed d10 gave S1f +353/G3h +444cp.
  Reported d11 S1f `mate -2` may be an unfinished-root score artifact and is not
  mate evidence. G3h lets the knight take S2g but recaptures with the gold;
  no move-quality proof or new evaluation term follows. C/E trials stay ended,
  with private raw/patches preserved; D10/support10 remains an unadopted review baseline.
  Preserve sealed plan/raw/attempt records; no automatic rerun or coefficient change.

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
  Pair5 user review: tentative preference0 because rook-file breakthrough looks
  promising;10 rook seems less effective, but user explicitly does not see10 as
  very bad. Modest preference/positional impression, not a tactical verdict.
  At48 both White K7a/G7b/S6b/S7c; other gold0 G5b vs10 G5a, rook0 R8b vs10 R1d.
  Opponent structures differ. Rook activity is a phase-dependent review consideration;
  do not attribute this preference to king safety or winning alone.
  Pair6 at48 user feedback: +0 G7d is immediately restrained by P*7e, so not
  established thickness, though the shape is not bad. Saved continuation49 P*7e,
  50 G7d7c confirms retreat. Do not infer advance alone restrains the opponent,
  or label the move a blunder. No user comparison with +10 established yet.
  [Design criteria/reference set](docs/experiments/learning/thickness/2026-11-07-style-design-criteria.md)
  prepared:6 qualitative cases/15 saved positions with full histories/source hashes,
  `results/teatsui-review-reference-2026-11-07/cases.json`. Not training targets,
  no numeric labels, no independent validation. Preserve acceptable non-thick forms
  and reversal of preference32→48. No new engine searches or evaluation changes.
  [Non-scoring annotations](docs/experiments/learning/thickness/2026-11-07-position-annotations.md)
  implemented on all15 saved states: chains, raw geometric king/ring attacks,
  unpromoted GS attackers/defenders, enemy pieces in own home3ranks. Pins ignored,
  no legal/effective threat or danger rating. King excluded only from ring defense,
  retained as a GS defender. Native chain bools agree; attackmap parity not claimed.
  `results/teatsui-position-annotations-2026-11-07/index.html` with sixcase/state
  selection and overlays; JSON preserves original feedback, histories and hashes.
  Six geometry/replay/symmetry tests and480 Node UI combinations passed; browser
  visual check not performed. No search/build/evaluation changes.
  Pair6 48 G7d supported by S8c,49 P*7e attacks it while support remains,50 G7c
  supported by G7b/N8a. Support alone is not sustainable restraint.
  Annotation UI is developer observation aid, NOT a user review task. Keep purpose
  sharp; ask user only when their answer changes a design decision, with rationale.
  Compared lowering bonus, safety gating, wider GS bonus: none currently justified;
  prior pair/advance learning reviewed, not reopened. See design criteria addendum.
  Latest user feedback on pair7 game14 after35 (Horse4a): ...K8b is NEUTRAL,
  neither plus nor minus. Horse4a is effective pressure and White struggles somewhat.
  Desired plan: avoid rushing attack, contain the horse and play patiently.
  K8b legal via referee only, not preferred move/teacher. P1e individually unjudged.
  [Containment design](docs/experiments/learning/thickness/2026-11-07-horse-containment-design.md):
  resumed from latest disk state; existing eval represents parts of horse/GS/king
  relations, but sustainable restraint not established. Saved after41 bonus10 d7–11
  PV already has G5b6c N7g6e S5c4b; d14 selects P5e. Candidate organization exists,
  not proof of confinement/superiority or search-pruning failure. Different from35root.
  User CONFIRMS effective restraint incl retreat/reasonable exchange, not physical
  trapping. Sente horse is "もたれ": no immediate concrete attack, aims to acquire
  pieces from gote's attack/exchanges and then break formation. User prefers not
  taking that bait, patiently preserving coordination; not a universal no-attack rule.
  Pair7 discussion is closed for now. User agreed to continue saved-game review
  from bonus10 and defer evaluation retuning until recurring issues are understood.
  No automatic G6c comparison; saved plan not approved best move.
  Pair6 bonus10/game11 at48→54→58: defend8-file with P*8d, exchange2-file
  pawns, then P*8b supports S8c against R8f/S8e. K7a/G6a,G6c/S5d,S8c stay.
  Astra selected; Sol native-checked44/48/54/58 and saved PV (48 already predicts58).
  User: somewhat unnatural; insufficient defensive pieces on8-file, breakthrough
  foreseeable; hand-solid shogi should defend reliably. Not a general ban on2-file
  exchange or proven forced line. Unchanged GS placement/support != adequate defense.
  User specifies: anticipate P*8e then silver attack; return rook to8b to reinforce
  8d, so original44 R8b2b deployment seems questionable. Keep rook's defensive role;
  S8c blocks direct R8b→8d ray now, distinguish backing after moves/exchanges.
  Distinguish pair6 concrete defensive shortage from pair7 latent "もたれ"/reaction.
  Saved44PV already includes P*8e Px8e Sx8e P*8b (actual47 is Rx8e);
  no claim pressure was unseen. Pair6 closed for now: check whether defense remains
  after exchanges before transferring pieces to attack. No numeric penalty/search.
  Details in style-design-criteria final section.
  Pair1 bonus10/game2,40→49,47S5g5f/49S5f4e takes pawn,
  own K2h/G3h,G5h/S2g/R4i unchanged; opponent S5e also active. Do not infer
  thick/safe because placement unchanged or won.
  Astra selected; Sol native-verified40/47/48/49. Existing viewer, no new searches.
  User: silver counterplay not very concerning;43 G4g looks natural to reinforce
  where opponent attacks. Actual43 Px5e invites enemy silver, concerning. User
  allows actual may be best; G4g is a proposed natural defense, not a best-move label.
  Sol native-check:43 G5h4g legal, supportsP5f. Actual43P5f5e capturesWP5e;
  WS4d captures it on48. No alternative search or superiority established.
  [Pair1 bounded comparison](docs/experiments/learning/thickness/2026-11-07-pair1-gold-comparison.md) COMPLETE:
  after42 fullhistory,+10 fixed,MultiPV2,searchmoves5h4g/5f5e,d15/nodes400000,
  watchdog120s,fresh,exactly1go/no repeats. Astra design/pre-go/final review; Sol ran
  and verified.21.384s,d15/351804nodes:Px5e−142cp/G4g−190cp (Black),both unbounded.
  All30PVs+bestmove native legal,bindings intact. G4g supportsP5f thenS5f but other
  flank pressure remains; pawn PV usesP*6d/Gx6d/B9g/Gx5e/B3a+→H2a takes knight,
  unlike actual silver capture.48cp isn't isolated defense value or best-play proof.
  Pair2 +10/game3 48→55: user finds exchange unappealing, not clearly bad; already
  pressed near36 with too few defenders. Enemy S2e/P2f resemble a foothold, so
  giving S+2P risks drops beyond it; no square specified. "Counterattack material"
  was assistant hypothesis. NEXT if needed: discuss defense before the advance; no tuning.
  User's early ideas: B retreat to5i then P3f, P4f→4e counterattack as opponent
  starts, or keep R2h for2-file defense. Timing/order open; human concepts, no
  immediate-legality or superiority claim. Actual R2h→7h19→8h29, B8h→7g25;
  P3g/P4g remain through32. B5i diagonal needs3g cleared; S4f blocks immediate
  P4f preparation at32; S2g blocks direct R2h→2f ray. No search/eval change.
  User reads White P3e(18)→R2b(28)→S3d(30) as a coordinated attack that
  restrains free P3f play; Black P2f(5)/S2g(15) preceded P3e. User considers
  avoiding that formation or finding a P3f counter; cleared3g could admit G/N
  defense as well as B5i diagonal. Timing/line unchosen, no best-move label.
  Output results/teatsui-pair1-gold-comparison-2026-11-07/,finalplan plan-v2.json;
  old pre-go plan/script retained,0old searches. Comparison closed; no more searches
  automatically. User accepts incorporating human intuition here: bring an inactive
  piece to the contested area, adding defense AND restraining enemy advance together.
  User qualifies: no need to fixate on dual-purpose activation. Core conditional idea:
  if defenders suffice, capture a pawn and use pawn drops to repel; if insufficient,
  avoid premature capture, add defenders and slow enemy entry before being breached.
  Count participation AFTER exchanges incl held-pawn resources/tempo; not raw-count
  threshold or universal anti-capture. Actual43 forced breach is not established.
  No formula/weight/training set;48cp isn't approved tolerance. User permits broader
  dialogue from genuine uncertainty; don't force every next case into capture/drop
  theme. Continue saved+10 dialogue; no automatic feature or repeat search.
  Pair8 bonus10/game15,38→49 edge exchange. Bishop9g→8h→9i;
  at49 clear diagonal to enemyS4d, both holdL, W P9c/K7a/R8b. Astra selection,
  Sol saved-history/geometry check; no search. User: edge attack before48 naturally
  targets weak bishop head; success unknown. Bishop effectiveness barely changes,
  don't emphasize its relocation/diagonal as main issue (assistant corrected).
  Natural concrete-target attack is compatible with defensive style; no best-move label.
  Samegame15 at54→64: G2c→3d→4d, supportedS5c, attacksB5e; allowsBlack+P2a
  (no knight capture;N already3c). Assistant sees gold role change, tradeoff unknown.
  User: GxP2b possible, but allowing tokin to activate gold also natural, feels
  Yonenaga-like (user style association). LaterL5c+ may hurt; not whole-plan rejection.
  Activity can justify allowing entry; don't turn defensive-count preference into
  always-prevent-entry rule. Astra selected/Sol saved-check, no new search.
  Sol confirms hypothetical58G2c2b legal pawn capture; actual69L*5f70P4e4f71L5f5c+
  takesS5c (G4d supporter, no other direct White control5c).72G4e73S*5b follows.
  Actual tactical loss distinct from natural gold plan; no alternative superiority proof.
  USER CORRECTION: L5c+ hurts chiefly by creating a promoted piece near king,
  plus captured silver (70WhitePx4f also takesSilver; not one-sided silver loss).
  R8b obstructs king escape. Retract emphasis on lost G4d supporter
  as main explanation. Own rook can be useful defense(pair6) or escape obstruction
  here depending on position; no blanket R8b rule or forced-mate claim.
  Pair5 +10/game10 64→73: user confirms the central defense works locally.
  White R1d supports P*5d through clear2d/3d/4d; Black S5e retreats6f after
  66/72 drops. This does not establish lasting restraint, whole-king safety,
  best play, win cause or bonus adoption. No search.
  Pair3 +10/game6: user's final judgment is that the king-side edge attack was
  wrong in this game and should be approached more cautiously. White P2g+ takes S2g at36;
  another Black silver falls46. White drops S*4e48/S*3f50 and promotes on2g52,
  taking G2g. Silver identity in hand is not traceable. User stresses weakened
  defense/formation disruption and opponent use of gained pieces. In upper-king
  thickness play G/S can matter more than a major piece; B-for-S alone isn't good.
  Contextual function, not general piece-value reversal or tuning. No new search.
  Pair4 +10/game7: user says Black already poor by58 and suspects worsening
  around45 B6f1a+ (takes L); H3g at65 is a target, not effective shelter.
  Saved66 N3c4e attacks it,68 P*4f/70 S*3g chase,72 S3g4f+ takes horse.
  Exact losing move unproved. The later seven-position static audit below checks
  existing evaluation around44/45/48; no new search.
  User now explicitly wants evaluation to value own-king defense more: thin Shin
  cannot rely on B-for-S or lance gain/horse alone when defense is stripped.
  Prioritize defense here; concrete feature/weight undecided, no code change.
  K8b remains neutral; no horse-presence/mobility blanket penalty or automatic tuning.
  Keep operational default0; experiment10 unadopted. No more searches automatically.
- [Seven saved-position static evaluation audit](docs/experiments/learning/thickness/2026-11-08-seven-static-audit.md)
  completed: game06 after32/37, game07 after44/45/48, game10 after64/73,
  ShinON/+10 with no search. Native diagnostic separated Black/White king_safety,
  checked eight-neighbor inputs, raw4 scores, fixed-progress contributions,
  complete evaluation and rounding residual. All7 legal histories/SFENs and
  original239 bindings matched. Game06 own-king-safety contribution falls
  +331→+130cp across32→37 while controls also falls; game07 is already
  -1211cp after44; game10 White own safety stays near+172→+178cp.
  These are existing-term responses, not causal proof or tuning coefficients.
  Follow-up candidate comparison below is complete; no coefficient decided.
- [Pair4 game07 after44 defensive candidate comparison](docs/experiments/learning/thickness/2026-11-08-pair4-defense-comparison.md)
  completed one fresh MultiPV2 search, ShinON/+10, restricted to actual6f1a+
  and user P*4f. Common unbounded d14/495040nodes: -133 vs -548cp;
  28/28 PVs native legal, plan/raw/bindings intact, no retry. User's P*4f
  attacks R4e and is supported by S5g, but its saved PV chooses ...R4d then
  pawn pushes and B1a+, not a continuing-defense line. Actual-root PV uses
  captured lance at4h defensively; actual game has different White response.
  USER REVISION: at44 White has captured Black N4e after37 P4f4e,
  38 ...Px4e,39 Nx4e, a bishop exchange and42 ...R7e. User suspects
  the37 pawn advance was poor and Black was already worse earlier; this is
  not a proven forced loss or identified losing move. USER: assistant's37 G4i4h
  is "not bad", but prefers a plan of S3h4g, K3i3h and G4i4h (king/gold
  order flexible); G4h first is also acceptable, not a fixed move-order label.
  The plan opens R2i's lateral route. S3h4g alone is native legal;
  if K/G vacate3i/4i, rook path3i–7i clears before own N8i. Later moves
  depend on unspecified opponent replies; no superiority established by the
  saved game alone. The later fixed prototype comparison is below.
  A separate branch was discussed but not decided or created.
- [Supported near-king G/S prototype](docs/experiments/learning/thickness/2026-11-08-near-guard-prototype.md)
  tested one isolated correction: count unpromoted G/S within king distance2
  with non-king own support, add10cp per Black−White count; existing support
  bonus10 stayed fixed. Off matched original; native full/diff/unmake/rotation
  and target fixtures passed. Four fixed searches completed: game07 after36
  p0 preferred actual P4e (-247 vs G4h -353), p10 preferred G4h (-292 vs
  P4e -405), all common d15/3 roots; game10 after65 retained P*5d at both
  0/10. G4h PV includes S4g/K3h; S4g first temporarily loses local support.
  USER: S4g is optional; G4h first is acceptable if it advances the defensive
  plan. S4g's immediate ranking need not recover for this trial to proceed.
  This is a prototype candidate, not strength proof or operational adoption.
- [Unrestricted three-root check](docs/experiments/learning/thickness/2026-11-08-near-guard-generality.md)
  completed with the same isolated binary, lambda0/10 and support10:6/6 fresh
  searches, all common d15,90 PVs native legal, bindings unchanged. At game07
  after36 unrestricted baseline already chose G4h; trial chose S4g. At unused
  game11 after43 both chose R2b (earlier rook concern remains), at game15
  after59 both chose G3d (only the initial gold activity preserved). The
  restricted P4e→G4h shift is not a demonstrated general improvement.
  USER DIRECTION: anticipate the opponent's attack and add or preserve the
  defenders that can participate, including their location and role after
  exchanges; this is not limited to rook defense or nearby G/S counts.
  Near-guard support can count R8b and later P*8b support equally as one,
  although participation on the 8th file after silver movement/exchanges differs.
- [Rear-participation prototype](docs/experiments/learning/thickness/2026-11-08-rear-participation-prototype.md)
  replaced near-guard10 with one isolated 0/10 term; support10/ShinON stayed
  fixed. Static R8b-vs-P8b participation differed as intended, but four fixed
  searches chose R2b at game11 after43 under both settings; positive game10
  after65 kept P*5d under both. All common d15, 60 PVs native legal, bindings
  unchanged. Trial PV later uses S8c7b→S8e7f→P*8c, so it is not the same P*8b line.
  USER: P*8b gets pushed back. This prompted the candidate comparison below;
  term10 remains unadopted.
- [Pair6 game11 gold defense comparison](docs/experiments/learning/thickness/2026-11-08-pair6-gold-defense-comparison.md)
  completed one same-root White MultiPV2 search at after43 with original fixed
  engine/ShinON/support10: legal G6a7b supports S8c/R8b but blocks S7b retreat
  and R2b path. Common unbounded d15: G7b -443 vs actual R2b -195cp; best R2b.
  30 PVs native legal, bindings unchanged. G7b line meets a different central
  attack and White also counterattacks; this does not reject defense as a policy.
  This led to the single contact-deficit trial below; no move-quality label.
- [King-contact deficit prototype](docs/experiments/learning/thickness/2026-11-08-king-contact-deficit-prototype.md)
  added one isolated 0/10 term for enemy-vs-own controls next to each king,
  with near-guard/rear terms off, support10/ShinON fixed. Off matched original;
  full/diff/unmake/rotation/12 fixtures passed. Six fixed fresh searches all
  common d15, 90 PVs native legal, bindings unchanged: game06 after28 changed
  from actual edge P1e at0 to S5g4h at10; game07 after36 kept G4h and positive
  game10 after65 kept P*5d at both. The move change fits the user's caution
  about king-side edge attacks but is not a best-move/strength proof.
  Term10 stays unadopted; no coefficient, operational code or branch change.
- [Contact-deficit versus normal result](docs/experiments/learning/thickness/2026-11-08-contact-deficit-normal-comparison-preparation.md):
  eight saved games and four known starts audited; original support10/ShinON
  fixed for both candidate arms, normal ShinOFF/support0. Contact0 1W2L1
  unresolved (256-ply limit); contact10 1W2L1 repetition draw. Comparable3/4,
  paired score difference total +0.5. All histories legal, 987 timed commands
  and bindings checked, no large clock anomaly. Private `results/teatsui-contact-deficit-vs-normal-2026-11-08/`
  has audit and all four pairs' 32/48/64 viewer. Pair4 first diverges on the
  normal side; results do not establish coefficient causality or strength.
  First local review completed; positive style feedback is recorded privately in
  `review-entry-pair3-game06.json` in that results directory. Not strength proof.
  Second local review completed; private judgment and deferred adjustment request
  are in `review-entry-pair2-game03.json`. Later evaluation work should more strongly
  discourage own-king-side edge attacks whose consequences weaken defense; no
  blanket edge-attack ban or coefficient specified. No tuning now.
  Any edge-attack penalty amount remains undecided; the suggested -10 was only
  an example. Third local review completed; private judgment is in
  `review-entry-pair4-game07.json`. Retain the contextual concern about handing
  an opponent a rook when the own formation is lopsided and thin; no blanket
  exchange ban or retreat square specified. The edge concern led to the small
  private trial below; the rook-exchange concern remains contextual.
- Private `results/teatsui-king-edge-shield-2026-11-08/result.md`: edge-shield
  0/40 trial kept contact-deficit10, support10 and ShinON fixed. Off matched
  prior D10; 20 fixtures and six approved fresh searches passed (common d15,
  90 legal PVs). Main game03 after54 chose 2e2d at both settings and advanced
  P1e later; the original timed P1e first move did not reproduce even at0.
  Silver-preparation and positive P*8d roots kept their first moves. Edge
  suppression/strength improvement is unconfirmed; the new term is unadopted.
  [Private same-root timed follow-up](results/teatsui-king-edge-shield-timed-2026-11-08/result.md):
  two approved fresh 10-second searches also chose 2e2d at both settings;
  29 legal PVs, common last nonbound reported depth14. Both later push P1e,
  while the original game chose it first. Fresh searches lack the game's TT
  history; the cause of non-reproduction is unknown. No adoption or extra go.
  [Private three-case edge-pawn reference](results/teatsui-king-edge-shield-2026-11-08/edge-pawn-natural-reference.md)
  registered three pushes that the user now explicitly wants to avoid.
  The old game15 move was called natural earlier, but the user clarified it is
  natural yet bad; the prior assistant reading as an acceptable example is
  withdrawn. Rook location is not very relevant to this judgment. All three
  have focal E0→1; loss causality is unproven. In old game15 the original
  White-side score was −141cp before P9e, with its large decline only much
  later (86 −151→88 −721→90 −1576); keep the user's avoid-it judgment separate
  from an unproven blunder claim. Details are in the private reference above.
  [Private 100cp replacement trial](results/teatsui-king-edge-shield-100-2026-11-08/result.md):
  fixed D10/support10/ShinON, edge0/100 only; static off/flip/full-diff checks
  passed. Six fixed 10-second fresh searches, 88 legal PVs: new game03 after54
  chose 2e2d at both settings (actual P1e first move still unreproduced);
  old game15 after39 chose the user-disliked P9e at both, even while the
  White edge deficit remained through its saved 100cp PV; positive P*8d held.
  Suppression/strength gain is unconfirmed. Keep 100cp unadopted; no further
  coefficients, roots or searches are authorized automatically.
  [Private same-root c comparison](results/teatsui-king-edge-shield-100-c-comparison-2026-11-09/result.md):
  one approved timed MultiPV2 go, old game15 after39 White. At common nonbound
  reported d14 the original P9e scored −182cp vs G6b −310cp; 28 PVs legal.
  P9e's edge deficit later cleared by P*9b in its PV, while G6b kept P9d/E0.
  This two-move reading neither proves move quality nor adopts the 100cp term.
  Latest user correction: quiet P1f→1e when the opponent does not contest the
  edge should be excluded; only edge-bishop-head attacks should be mildly
  discouraged. Current E ignores enemy pawns/bishop/contact and is too broad.
  Keep the isolated support10 + contactD10 + edge100 trial (ShinON, near/rear
  off) as historical evidence only. [Private correction](results/teatsui-king-edge-shield-100-2026-11-08/quiet-edge-advance-correction-2026-11-09.md).
  [New narrow bishop-contact trial](results/teatsui-edge-bishop-contact-2026-11-09/result.md):
  D10/support10/ShinON fixed, old E/near/rear off; static off equality and 19
  fixtures passed. Four fresh 10-second searches and59 legal PVs: a chose 2e2d
  at0/100, c chose9d9e at0/100; C cleared when the opposing bishop left the
  edge. Target scope is corrected, suppression and strength remain unconfirmed.
  Keep the narrow term only as a future experiment candidate, not operational adoption.
  None of the three pushes is established as a blunder. [Private saved-score context](results/teatsui-king-edge-shield-100-2026-11-08/score-context-2026-11-09.md)
  separates the gradual old game06 decline, new game03 rebound/late drop and
  old game15 recovery from the user's positional preference.
- No other searches or matches automatically. User can supply shape/function preference;
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

- Basic goal remains supported pawn territory and thick shogi. If participating
  pieces cannot sustain it against the opponent's attack, keep a low solid camp
  and retain the option of using that rank as bait for opposite-flank counterplay.
  Do not force support or replace thickness with a universal bait strategy.

- User explicitly values sufficient defensive pieces in own camp; prefer avoiding
  positions likely to be broken through or pushed back because defenders are too few.
  Track participating defenders (rook included) and what remains after exchanges,
  not only unchanged GS shape. No numeric feature/blanket retreat rule approved.

- Desired flow clarified: use GS/pawn thickness to restrain the opponent's attack,
  then gradually activate major pieces using that breathing room. This is a
  contextual plan, not a requirement to fully suppress all counterplay before any
  attack or a fixed move-count phase rule. Evaluate actual restraint, not just shape.

- User cautions against expanding scope into general major-piece activity scoring.
  In Shin Yonenaga openings, gold/silver activation and formation may take priority;
  temporary rook/bishop inactivity is acceptable. Consider major-piece use from
  middlegame onward, contextually, not a fixed phase switch or mandatory early
  development. Do not add/strengthen activity bonuses or weaken existing evaluation
  from this teaching alone. Focus remains GS/pawn coordination, own king safety and
  responses to enemy pressure. The assistant's broad generalization after pair5
  is qualified by this user clarification (2026-11-07).

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
- Old binary/data and repaired-engine identities remain in frozen plans.
  Adopted support10/D10 binary is separately installed under
  `bin/teatsui-2026-11-13/`; installation manifest preserves old/new identities.
  No learning candidate or additional trial feature was installed.

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
- User preference: do not push new tracked text with personal home-directory names
  or environment identifiers. Check tracked diffs before committing; previously
  removed history does not need rewriting now.
- After the current eight-game comparison, archive needed dialogue and experiment
  records privately, verify that archive, then remove obsolete tracked artifacts.
  Aim for adopted C++ changes, essential regression tests, reusable match tools
  and concise build/design documentation. Detailed user dialogue need not remain
  public. User accepts records remaining in Git history: clean the current tree,
  without rewriting history. Do not remove active experiment dependencies now.
