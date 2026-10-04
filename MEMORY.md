# Rakuyou Development Notes

This is the resume map, not a detailed changelog. Completed experiments and
decision evidence live under docs/experiments/; see its README for navigation.

## Project and Runtime

- Personal experimental fork of Gikou 2, identifying itself as Rakuyou.
  Preserve upstream copyright headers and existing C++ conventions.
- Apple Silicon builds the SSE4.2 engine as x86_64/Rosetta. Read
  docs/development.md before build/data work. Runtime data in bin/:
  params.bin, progress.bin, book.bin, probability.bin.
- Read MEMORY.md, README.md, Makefile and git status before resuming.
- The verified bin/release SHA-256 is
  6f7891c4957e1bf37b1e80c37ad0c9cf83f34ca974e87be05fb05dd5c1f4c2ac.
  This October3 build adds Black dedicated-book loading/probing only; the
  previous a1a5e25a… binary was used for all15 Black focused searches.
  Ignored binaries can survive branch switches; rebuild for changed engine code.

## Engine Behavior and Durable Decisions

- ShinYonenagaGyoku (default ON) controls both the fixed first move and an
  experimental 25cp opening king-location preference.
- Black opens 5i4h (king48); White opens 5a6b (king62), only from the initial
  position/matching one-move history, respecting legal root restrictions.
- Preference favors Black king files1-4 and White files6-9, fading to zero in
  middlegame; retreats are legal. OFF disables both features.
- Keep the toggle and 25cp value unchanged for the current book work.
- Black book design policy: prioritize preparations retaining the king
  on files1-4 and avoid hard-coding an immediate return toward the left.
  Keep left-return candidates as comparisons; retreats remain legal/searchable.
  Do not change the25cp preference or add king-move restrictions implicitly.
- Against normal pawn84 after the silver38 entry, prioritize a balanced
  right-side-king setup with eighth-file defenses and active rook use;
  right-king/twisting-rook ideas are references, not required named openings.
  Keep left-return PVs as evidence/control, not automatic book choices.
- Compare with normal Rakuyou/Gikou using its standard book. Judge playing
  strength, king placement and middlegame transitions, not just one score.
- Completed, book-free, one-thread focused searches are the main move evidence.
  Scores are side-to-move; do not subtract values across different positions,
  ON/OFF, depths or restricted/unrestricted candidate sets.
- Rankings have flipped at depth28/30. Timed-stop results are provisional:
  analyze_positions.py snapshots the last completed MultiPV depth before stop,
  records stopped_early, and distinguishes candidate_bestmove from bestmove.
- StartNewGame() is empty; processes retain some state between games, though
  some search resets occur. Zobrist keys are randomized at startup. Do not
  assume independent games or claim those mechanisms caused observed gaps.

## Current Decision: White Operational Book Frozen

The bounded White improvement cycle ended and work moved to the Black book,
even without proving a winning score against standard
Gikou. White's first operational version is the unchanged v2, 11 positions:
books/shin-yonenaga-white-book-v2-experiment.txt.
The filename stays unchanged for reproducibility; "experiment" in its name
does not indicate the current operational status. No engine/default changes.

- SHA-256: 28e59ec12cb86ada7280687d130e29bdb28eb0d550840d634c73e003aa2ffc62.
- Generate from books/shin-yonenaga-white-candidates.json plus
  books/shin-yonenaga-white-v2-experiment.json using tools/build_shin_book.py.
- Use ShinYonenagaGyoku ON, OwnBook ON, ShinBookFile pointing to that txt,
  BookMaxPly20. Uncovered positions search; no standard-book fallback.
- Scope: standard-book-enabled opponent / Sente fourth-file-rook benchmark.
  Other openings, timed GUI games and a separate Gikou are not fully validated.
- This is an operational choice, not proof of superiority or winning strength.

The one-position pawn25 trial remains on hold:
books/shin-yonenaga-white-book-v2-pawn25-experiment.txt (12 positions).
Its extension retains the 11 v2 entries and adds 2d2e after
7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 7a7b 6g6f 6b7a 7i7h
8c8d 7h6g 2c2d 6f6e. Completed unrestricted White-ON depth28 ranked
2d2e -142 vs 7b8c -172. Normal-OFF depth24 preferred 6g6f (+156).
This candidate is not rejected, but no more searches/games in this cycle.

External comparison completed on October3, preparation commit da37690:
four fresh 50-game runs, v2/trial/trial/v2, depth15, threads1/hash512,
White fixed, standard-book opponent, Ponder OFF, BookMaxPly20, max256 plies.
v2 runs: 18/27/5 and 15/24/11, both41%; total33/51/16 (41%).
Trial: 18/24/8 (44%) and20/24/6 (46%); total38/48/14 (45%).
All200 completed, errors0. Record/summary/outcome checks and all1334
dedicated moves matched book positions/moves. Input hashes match preparation.
Trial B was reached7 times (3/3/1); v2 reached2 (0/1/1).
All7 continued with silver83/rook62. Direct Sente replies: silver66 four,
pawn56/silver56/bishop77 one each. No consistent immediate opening gain.
Baseline r1/game49 transposes into the same position after ply20; baseline
r2/game47 already searched pawn25 and shares the first24 moves with trial
r2/game45, despite opposite outcomes. The non-B cohort also scored higher
in the trial runs, so the overall4-point gap cannot be attributed to the new
entry. Apply the pre-agreed ambiguous-result fallback: retain v2.

Full results, 7-game review, provenance, checksums and closure:
docs/experiments/2026-10-03-v2-bounded-white-improvement-cycle.md.
Books/status/GUI settings: books/README.md.
tools/review_v2_white_cycle.py reproduces White cohorts by board/hands/turn,
now accepts completed50-game outputs via requested_games. Replay is not full
independent legality or perpetual-check adjudication.

## Immediate Next Steps: Black Book

See docs/experiments/2026-10-03-black-book-start-plan.md.
Entry statistics from six existing paired runs (Black50 each) are inspected:
300 games,108/138/54, descriptive45%. All reply 3c3d to fixed5i4h.
After 7g7f, normal7a6b occurs162 times and8b4b occurs82.
White v1/v2 books supplied no dedicated moves to Black. Standard book was used
for just5 Shin moves in one old ON game; do not infer a book benefit.
Keep per-run settings/history: these paired games are not a new fixed-Black
benchmark, and old runtime binaries lack automatically stored start hashes.

Black book work then began. Audit and initial screen are
complete, source HEAD0ea194a. See
docs/experiments/2026-10-03-black-300-game-branch-review.md.
tools/review_black_runs.py audits all600 saved paired records/results/summary,
replays the selected Black300, and outputs run-specific branches, book exits,
king positions, representative games and diagnostic shallow score changes.
Its5 synthetic tests pass. Ownership replay is not full legality/adjudication.
Normal first search is ply6 in269 games, ply8 in24, ply10 in6, ply20 in1;
some later return to book. Four position occurrences appear in36 games,
all saved draws. At ply24,101/300 Black kings are already on files5-9;
do not force the right-side placement or infer causality from king cohorts.

Three unrestricted Black-ON depth24/MultiPV5/threads1/hash512/fresh/book-free
searches completed, errors0/no stops/no bounds; all10 input moves legal-probed:
- 5i4h 3c3d: pawn76/pawn26 tie-121, silver38 -129.
- 5i4h 3c3d 7g7f 7a6b: pawn26 first-27, pawn16 -54, silver38 -60.
- 5i4h 3c3d 7g7f 8b4b: pawn96/pawn86 tie-96, king59 -98,
  pawn26 -102, pawn75 -103. Top PV after pawn96 returns king to59/68/78.
Root PV replies include pawn44 and rook52, unlike the common standard-book
replies. Do not choose a unique root or a finished Black skeleton yet.
Raw result: results/black-entry-2026-10-03-shin-depth24.json, SHA256
f783f65a3b0ccd8dcd140e27d84499742de19d21f89ac95a78957173b385a1bb.

The subsequent continuation completed5 more searches:
2 normal-OFF depth24 direct roots,2 Black-ON depth24 preparations,1 Black-ON
depth28 rook42-parent recheck; same unrestricted/fresh/thread1/hash512/book-free
conditions. All5 completed with5 candidates each, errors0/no stops/no bounds;
all18 input moves legal-probed. Results are appended to the same Black report.
- After pawn76, normal pawn44 +96, rook32 +87, pawn64 +58, bishop33 +42,
  silver62 +39. The new pawn44/rook32 replies never occurred at ply4 in the
  244 old pawn76 games (all book silver62/rook42).
- After pawn26, normal bishop33/silver42 tie+105, silver32/pawn44 +104,
  rook32 +93; root Black-ON PV's rook52 was outside this direct OFF top5.
- Black after pawn76/pawn44: pawn26 -109 first, pawn56 -123, pawn96 -124,
  gold58 -128, silver38 -130. Top PV returns king via57/68/78.
- Black after pawn26/bishop33: silver38 -110, gold58/pawn76 -113.
  Top PV silver38/silver32/pawn76/pawn44/king39 connects to silver27/rook48,
  preserving a right-side king plan without extra positional restrictions.
- After pawn76/rook42 at depth28: gold58 -64, king58 -65, king59 -66,
  pawn26 -96, pawn66 -113. Depth24 pawn96/pawn86 leaders are now outside top5;
  do not force them or subtract scores across depths. Leading PVs move king left.
Prefer pawn26-first as the next Black-trial investigation, not an adopted
best root or strength claim. Keep pawn76/silver62 as an alternative; do not
forbid king retreats. No Black book or extra games have been created.

Checkpoint e310529 committed the audit,8 searches and right-side-king
preference; not pushed. Continuation completed4 more unrestricted fresh
depth24/MultiPV5 searches (Black ON2, normal OFF2), same settings, errors0/
stops0/bounds0,5 candidates each,18 input moves legal-probed. Results are
appended to the same report; cumulative12 searches (ON8/OFF4).
- After pawn26/silver42: gold58 -99, pawn76 -124, silver38 -134,
  pawn25/pawn36 -145. Gold58 PV returns king59/68; pawn76 and silver38
  connect to right-side plans, but are not equivalent to the leader.
- After pawn26/gold32: pawn76 -32, silver38 -94, pawn25 -108,
  gold78 -113, king38 -158. Top PV keeps king48 and exchanges rook pawns.
- Normal OFF after silver42/pawn76: bishop33 +128, pawn44 +96,
  silver33 +13, bishop88+ +8, bishop44 -26. Leader PV silver38/king39;
  pawn44 PV instead returns king59. Right-side placement is not guaranteed.
- Normal OFF after gold32/pawn76: silver72 +55, pawn64 +54,
  pawn84/silver62 +47, king42 +32. Top4 PVs choose Black pawn25, but OFF
  PVs do not directly establish future Black ON responses.
- Historical pawn26/bishop33 already chose silver38 in19/21 games;
  pawn26/gold32 chose pawn76 in all22. Do not present registration itself
  as a newly discovered winning move or proven strength gain.

The continuation completed the3 queued Black ON depth24 checks,
same unrestricted/fresh settings; all15 candidates complete/no errors/stops/
bounds,18 input moves legal-probed. Cumulative15 searches (ON11/OFF4).
- Gold32/pawn76/silver62: pawn25 -36, gold78/silver38 -41. Leading PV
  retains king48 initially but returns king59 at overall ply25.
- Gold32/pawn76/pawn84: pawn25 +17, gold78 -10, pawn66 -45,
  silver38 -101. Leading ON PV exchanges bishops, unlike earlier OFF PV.
- Silver42/pawn76/bishop33: gold58 -94, pawn25 -98, silver38 -110.
  Choose pawn25 (4cp deficit/right-side PV), replacing tentative silver38.

Created books/shin-yonenaga-black-pawn26-experiment.json and
books/shin-yonenaga-black-book-pawn26-experiment.txt:7 experimental positions,
plies3-7 only. SHA2566218cbbcd7768ecd3c0e90aec650ec080e8a02dfcf14555e76edd23775ed00b1.
Root pawn26; bishop33->silver38; gold32/silver42->pawn76; gold32 followed
by silver62/pawn84->pawn25; silver42/bishop33->pawn25. Keep the25cp deficit
for silver42/pawn76 explicit. Unknown replies/deeper moves leave book for
search, not standard fallback. No king retreats prohibited/guarantee given.
This is a trial, NOT operational adoption or demonstrated strength gain.

Both loader/probe and builder were White-only. src/shin_book.cc now accepts
either side using existing exact position/turn equality and legality checks.
No evaluation/default/first-move changes. build_shin_book.py defaults White;
Black requires --side black --source ... --experimental --output ... and
cannot overwrite existing White books. Separate ShinBookFile selection is
still necessary; no automatic White/Black file switching.
make release -j2 succeeded;29 regression tests passed (Black8/White5/
seventh8/analysis3/audit5). All7 entry evidence matched raw results, and39
book/input moves were legal-probed. White v2 hash unchanged.

Preparation was committed/pushed as433f8d0. All four
external fixed-Black50 runs baseline/trial/trial/baseline, depth15/thread1/
hash512/normal book ON/BookMaxPly20/max256/PonderOFF completed. All200/errors0;
records/outcomes/summaries/settings and215 dedicated moves checked.
Baseline:18/16/16 (52%),17/24/9 (43%); total35/40/25 (47.5%).
Trial:15/25/10 (40%),14/27/9 (37%); total29/52/19 (38.5%).
Do not attribute the9-point difference as an exact causal book effect.
At ply24 right-side kings: baseline65/trial85; returned by12:17/0.
Draws25/19; four board/hands/turn occurrences17/9, all saved draws.
No independent perpetual-check adjudication. Trial gold32 cohort44 games
scores53.4%, bishop33 cohort37 scores25.7%; bishop33/silver38/silver32
23 games score26.1%. Root forces pawn26 in100 instead of baseline19.

Deeper diagnosis completed6 focused searches (ON5/OFF1),
cumulative21, current unchanged binary;105 inputs and2 restricted candidates
legal-probed, errors/stops/bounds0. Appended results to the same Black report:
- Frequent after bishop33/silver32/pawn76/pawn44: depth24 silver27 -131,
  pawn96 -138, king39 -149. Do not reject the actual right-side preparation
  merely from low cohort outcomes.
- After king39/silver43/silver27/rook22: depth24 pawn46 -87, silver68/
  pawn56/rook48 -167. Main practical move is supported, not immediate failure.
- Trial-r2 game31 before29: unrestricted depth24 pawn66 -75 vs knight77
  -235; depth26 pawn66 -165 vs knight77 -204. Restricted depth24 pawn66
  -221 vs actual pawn86 -395. Do not subtract across depths/restrictions;
  absolute cp unstable, but pawn66 remains a preferred defense.
- Normal OFF after actual pawn86: depth24 pawn45 +352, pawn14 +274,
  pawn64 +258; PV pawn45/knight45/bishop88+/silver88/bishop64 drop.
  Pawn66 blocks the bishop diagonal while retaining the right-side king.
  Exact parent occurred once only; not the sole cause of37 poor games.

The next comparison removes only the root pawn26-forcing
entry, retain6 conditional entries to separate root selection from
preparations. Baseline100 statically reaches those
entries39 times in31 games (17 different recorded moves); transpositions
included, not a counterfactual coverage/strength prediction. Do not extend
BookMaxPly/register game31's29th move from one case. Recommend holding
the7-entry trial's operational adoption, not rejecting all right-king ideas.
Diagnostic checkpoint c2c064c was committed/pushed. Then created separate
books/shin-yonenaga-black-conditional-experiment.json and
books/shin-yonenaga-black-book-conditional-experiment.txt. Only removed
black_pawn26_entry;6 remaining entries (including evidence) fully identical.
New txt SHA256e08bb43bfd6c557ff402e8407b68f72443925228080d4774c60d0e2a4f72a0f7.
Fixed first king48 unchanged; root source=search; transposed conditional
positions still hit dedicated book. No standard fallback for uncovered root.
Added4 tests, all33 passed. Old7-entry book/White v2/binary hashes unchanged;
no rebuild required. Preparation and completed results are included in the
current conditional-book checkpoint; see git log for its commit ID.

Both external6-entry trial50-game runs completed, same depth15/thread1/
hash512/normal book ON/BookMaxPly20/max256/PonderOFF/timeout300. Outputs:
results/shin-black-conditional-r1-depth15-50games.json and same r2.
All100/errors0; records/summaries/outcomes/settings and18 dedicated moves
matched. r1:13/24/13 (39%); r2:24/17/9 (57%); total37/41/22 (48%).
Existing baseline100 scores47.5%, root-forced100 scores38.5%; separate runs,
not concurrent controls. The18-point within-condition spread forbids a
causal improvement claim. Root is search throughout: pawn76 in93/pawn26 in7.
Book used in17 games,5/9/3 (38.2%); unused83 score50%, not causal cohorts.
Right-side kings at24:63/100; returned by12:26. Four position occurrences
in11 games, all saved draws; no formal repetition/perpetual-check adjudication.
Conditional book remains experimental/unadopted; no clear benefit established.
Full counts, game references and raw hashes appended to the same Black report.

Early silver38/silver68 root screen completed, cumulative23 searches.
Input: docs/experiments/positions/book/black-silver-entry-2026-10-04-shin.json.
Root5i4h3c3d; restricted four candidates pawn76/pawn26/silver38/silver68,
Black ON/book OFF/fresh/thread1/hash512/MultiPV4; depths24 and28 both complete.
Depth24 ranks pawn76 -117,pawn26 -118,silver38 -164,silver68 -219;
depth28 same ranks -110/-123/-149/-204. Within-depth gaps only; do not
subtract against old unrestricted scores or across depths. errors/stops/bounds0,
bestmove/PV/depth/count verified; input2+candidate4 and246 input/PV moves
legal-probed. Analysis lifecycle3 tests passed. Raw results under results/:
black-silver-entry-2026-10-04-shin-depth24.json and same depth28.
Hashes/PVs appended to the Black report. No book/evaluation/search changes.
Silver38 PVs both reply pawn84, but not direct normal-OFF evidence.
Depth28 silver38 keeps king48 with gold78/silver77/silver47/rook29;
depth24 instead king28/rook68. Neither PV exchanges bishops.
Depth28 silver68 permits bishop exchange taken with gold88/king48 retained,
but has94cp deficit; lower priority, not a proven safe bishop-exchange setup.
Silver38 direct replies and2 preparations completed, cumulative26 searches.
Inputs: black-silver38-2026-10-04-opponent.json and preparations-shin.json
under docs/experiments/positions/book/. Fresh unrestricted depth24/MultiPV5,
thread1/hash512/book OFF/Ponder OFF. errors/stops/bounds0; all15 candidates
complete, bestmoves verified;445 input/PV moves legal-probed, plus11 input
moves and6 standard-book candidates. Analysis lifecycle3 tests passed.
OFF after5i4h3c3d3i3h: pawn84 +170,silver32 +115,silver42 +114,
silver62 +96,bishop33 +94 (White side-to-move).
ON after pawn84: pawn76 -166,pawn26 -170,gold78 -175,pawn96 -186,
king39 -210. Top3 depth24 PVs return king left; old restricted root depth28
silver38 PV instead kept king48. Right-side static-rook setup remains unstable.
ON after rook42: pawn26 -75,silver68 -77,pawn56/king39 -88,pawn76 -90;
top5 PVs keep king right with silver27/rook48-type plans, not proven strength.
Normal standard book has6 selectable replies to the silver38 root:
pawn54/silver62/rook32/pawn84/silver32/rook42. Ten one-position depth1
probes all source=book: rook42 6,pawn84 2,silver62 2; not games/probabilities.
Book info depth32/cp0 is stored book display, not completed search/equality.
Raw result hashes and evidence appended to the same Black report.
Pawn84 unrestricted ON depth28 recheck and one PV bishop-exchange diagnosis
completed, cumulative28 searches. Fresh/thread1/hash512/book OFF/MultiPV5;
errors/stops/bounds0, count/depth/bestmoves matched;476 input/PV moves plus
input4+32 legally verified. Lifecycle3 tests passed. New input files under
docs/experiments/positions/book/: black-silver38-2026-10-04-
pawn84-recheck-shin.json and bishop-exchange-shin.json. Raw result hashes/PVs
are in the Black report; no book/engine/evaluation changes or new games.
After pawn84 depth28: pawn26 -102,pawn76 -112,gold78 -130,pawn16 -146,
pawn96 -157. Top4 PVs keep king48; pawn96 returns king59. Do not subtract
depth24 scores. Pawn26 PV exchanges8-file pawns, gold78/pawn87 drop, then
2-file pawns/rook26; left silver79 remains unprepared. At32 both hold bishops.
That hypothetical PV endpoint ON depth24: pawn74 -290,silver88 -543,
rook25 -657,bishop55 drop -681,rook29 -748. Within-run top gap253;
do not subtract from the root28 -102. Pawn74 PV trades bishops55/44 before
silver88; other lines suffer bishop44 drop or silver87 pressure.
King48 stays right but this does not prove safe bishop exchange. Hold long
pawn26/rook26/exchange registration, not all silver38/king-right concepts.
Pawn76 branch direct OFF reply and one ON preparation completed, cumulative30.
Fresh unrestricted depth24/MultiPV5/thread1/hash512/book OFF; errors/stops/
bounds0, all10 candidates complete and bestmoves match;336 input/PV moves
legal-probed. Inputs black-silver38-2026-10-04-pawn76-opponent.json and
pawn85-preparation-shin.json; raw hashes/PVs in the same Black report.
OFF after5i4h3c3d3i3h8c8d7g7f: pawn85 +121,gold32 +36,silver62 +34,
gold52right +31,pawn44 +26. Book-ON depth1 probe searches, not a book hit;
its bishop88+ reply is shallow only, not the depth24 conclusion.
ON after pawn85: pawn26 -105,gold78 -133,bishop77 -169,king39 -184,
bishop22+ -259. Top4 PVs keep king right; bishop22+ later returns left.
Pawn26 PV still has later bishop77+/bishop44 drop with rook26; safety unresolved.
Gold78 PV has silver88/87,king28, rook exchange then opponent rook69 drop.
Bishop77 PV permits bishop77+ taken with knight77 then silver88/king48;
64cp deficit in this depth24 run. Silver68 outside top5; early-left-silver
bestness/safety hypothesis unconfirmed, not a proven gain.
Same six-move ON parent depth28 recheck completed, cumulative31 searches.
Fresh unrestricted/MultiPV5/thread1/hash512/book OFF, errors/stops/bounds0;
all5 complete, bestmove/PV matched;191 input/PV moves and input6 legal-probed;
lifecycle3 tests passed. Raw pawn85-preparation-shin-depth28.json hash in report.
Pawn26 -140,gold78 -145,bishop77 -196,king39 -215,pawn96 -225.
Top3 order unchanged from24, pawn26/gold78 gap5 within28; no cross-depth math.
All top5 PVs keep king right. Pawn26 now develops silver77/silver47/rook29/
gold58right/king48 without bishop exchange inPV; gold78 chooses rook48/king39
with opponent switching rook42. Bishop77 accepts exchange/knight77, but56cp
below leader. Safe exchange/strength not proved; do not force that entry.
Close the entry-search cycle here. October5: separate4-entry short
silver38 trial created (NOT operationally adopted): root3 silver38 (39cp deficit in
restricted root28), after pawn84 pawn76 (10cp deficit in unrestricted28),
after pawn84/pawn76/pawn85 pawn26 (unrestricted28 leader), after rook42
pawn26 (unrestricted24 leader). Unknown replies search, no standard fallback,
BookMaxPly20 unchanged; no long PV/king return registration. Compare externally
with50 games x2 runs; existing books/White v2 remain unchanged.
Source: books/shin-yonenaga-black-silver38-experiment.json.
Book: books/shin-yonenaga-black-book-silver38-experiment.txt;
SHA256 6cbb021417a755d193eeb66de3cfd26575bfbaf711cb1f89382e80ed712bf0c0.
37 regression tests passed; all4 evidence references match local raw data.
External games pending: results/shin-black-silver38-r1-depth15-50games.json,
then r2 with identical settings. Give one command at a time, caffeinate -i.
Check replies/book coverage/king placement/left-silver development/exchange
failures; historical47.5%/48%/38.5% are descriptive, not causal benchmarks.
Root screen ends at2 searches; no book/engine/default changes or adoption.
Compare standard-book replies separately from normal-OFF book-free search;
do not assume an opponent static-rook opening or safety from being Black.
Potential White reuse needs a separate tempo/safety check; White v2 stays frozen.
No additional games or engine/evaluation changes in the silver-entry investigation.
Do not expand searches indefinitely or require winning strength for closure.

The White decision, cleanup and Black starting plan were pushed as0ea194a.
The initial checkpoint commit is e310529; trial preparation433f8d0 was
pushed to origin/main. October4's200-game/deeper diagnosis was pushed as
c2c064c. The6-entry comparison100 has completed, but is not operationally adopted.
No long games are authorized inside Codex.
Engine defaults and GUI settings remain unchanged;
v2 requires explicit ShinBookFile selection.

## Deferred White Research and Evidence Map

- Four fixed-White100 runs: v1 30%, v2 42%, no-book26.5%, standard39.5%.
  Shin had0 standard-book moves in the last run; not proof of a book benefit.
  docs/experiments/2026-10-02-fixed-white-four-books-depth15.md.
- Astra independent review and benchmark-first addendum:
  docs/experiments/2026-10-03-astra-white-book-independent-review.md.
- Main historical 5c5d/silver42-53 development:
  docs/experiments/2026-09-27-historical-line-analysis.md.
  Do not force early6c6d or historical king83.
- V2's frequent silver67/gold58 parent: depth28/30 rankings differ;
  high observed silver83 cohort score is not a causal move comparison.
  docs/experiments/2026-09-29-shin-dedicated-white-book-v2-two-run-branch-review.md.
- Edge waiting / contextual pawn74: not a fixed general skeleton.
  docs/experiments/2026-10-02-edge-wait-seventh-file-analysis.md and
  docs/experiments/2026-10-02-early-silver72-and-seventh-trial.md.
- Seventh-edge trial100:20/61/19 (29.5%), dedicated pawn74 in7 games,
  dedicated silver73 in0. Not operationally adopted; do not reject the whole
  concept from a low-coverage experiment. Followup rook32 candidate remains
  deferred, not the immediate task.
  docs/experiments/2026-10-02-seventh-edge-white-only-depth15.md.
- Common White ply22: depth28 pawn14/rook32 tied-174, pawn94 -176,
  pawn25 -200. Needs intentional BookMaxPly change; not added.
- First-book integration tests: test/test_shin_book.py. Existing seventh-edge
  tests and analysis fresh-process tests remain useful regression coverage.

## Data, Tools and Safety

- tools/paired_selfplay.py fixes color with --shin-side black|white --games N;
  default paired mode swaps colors. Normal side always uses standard book.
  --shin-book on plus --shin-book-file sets the dedicated book only for Shin.
  JSON saves every game; --resume supports paired/fixed runs. docs/selfplay.md.
- Runner handles resign, entering-king declaration, max256 draw; strict
  repetition/perpetual-check adjudication remains unimplemented.
- Raw JSON stays in ignored results/. Historical third-party KIF stays in
  ignored local/kifu/. Keep large raw data and complete third-party games
  out of Git. Commit reports/input positions/tools and raw-file SHA-256.
- Public files must use repository-relative paths or neutral placeholders,
  never personal home-directory paths. Run commands from the repository root;
  GUI file selection resolves each user's own absolute path locally.
  Current tracked documentation was sanitized; older commits are left intact.
- Write public experiment reports as development records: describe decisions,
  methods and results directly, without request/approval dialogue. Preserve
  analysis provenance (including Astra reviews), evidence and uncertainty.
- Reports: docs/experiments/; named inputs: docs/experiments/positions/.
  No files were moved/deleted in the October3 cleanup. Old paths stay valid.
- Important raw data should be compressed/backed up to
  Rakuyou-results/YYYY-MM-DD/ on Google Drive; never delete originals before
  verified backup. No external backup was performed in this cleanup.
- One hundred games may show large differences, not small reliable gains.
  GUI engines may need restart to reload files/binaries.
- Prefer small observable changes. Preserve user changes; no destructive
  resets/deletions. Use gyoku in king-related branch names.
- C++ helpers follow existing anonymous-namespace style; opening helper
  GetOpeningMove/log Shin-Yonenaga-Gyoku. Keep detailed build/tool usage in docs.
