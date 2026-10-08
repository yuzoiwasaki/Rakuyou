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
External games completed: results/shin-black-silver38-r1-depth15-50games.json
and r2. All100/errors0, same settings, records/summary/outcomes/book169 checked.
r1 19/24/7 (45%), r2 12/30/8 (32%), total31/54/15 (38.5%).
Right king at24 in97, left return by12 in1; no strength gain proven/adoption.
Rook42 cohort37:10/21/6 (35.1%); pawn84 cohort16:7/8/1 (46.9%).
October5 loss diagnosis:5 fresh Black ON/book OFF depth24 searches complete,
cumulative36, no errors/stops/bounds;1043 input/PV moves legal;37 tests passed.
Inputs black-silver38-loss-review/followup-2026-10-05-shin.json under
docs/experiments/positions/book/; raw hashes and results in the same Black report.
Common rook42/king62 parent37: silver68 -71 vs actual king39/pawn96 -75,
pawn56 -76; no immediate root failure, only small within-search gaps.
r1/game7 before31 actual silver56 -73 first; before33 actual silver65 -93
first. Do NOT label these errors from saved depth15 score changes.
r1/game43 before17 singleton: unrestricted pawn66 -163 first, actual
bishop33+ outside5. Restricted same-parent pawn66 -210 vs bishop33+ -336,
126cp within-run gap; delay exchange and develop left defense as hypothesis.
Same exchange-vs-pawn66 parent rechecked at depth26, two-candidate restricted,
fresh ON/book OFF/thread1/hash512/MultiPV5 (two actual candidates).
Pawn66 -199 vs bishop33+ -407,208cp within-run gap, rank unchanged from24;
do not compute cross-depth improvement.33.323s complete/errors/stops/bounds0,
89 input/PV moves legally verified; lifecycle3 tests passed; cumulative37.
Pawn66 PV gold58left/silver68-67-56/bishop77/silver27/rook48/gold38right/
king28, then later bishop exchange/drop77. Both PVs keep king right.
Input black-silver38-exchange-recheck-2026-10-05-shin.json; raw hash in report.
Maintain conditional preparation-before-exchange guidance; singleton parent
does not justify claiming global gain or registering a long PV.
Stop this depth-expansion cycle. No book edits/adoption/new games.
Silver32 cohort18 (4/11/3) reviewed: normal fourth reply all source=book,
Shin fifth all search, no later dedicated hit. Fifth pawn76 in10 (4/5/1),
pawn46 in4 (0/4/0), king39 in4 (0/2/2). Normal first search ply6 in14,
ply8 in1, ply10 in3; do not label every sixth move as standard-book.
Two fresh unrestricted ON depth24/MultiPV5 searches completed,cumulative39.
After silver32: king39 -92,pawn76 -110,pawn26 -122,pawn96 -127,pawn46 -128.
After silver32/pawn46/rook42: king39 -130,pawn96 -131,silver47 -132,
pawn86 -133,pawn76 -148. Actual pawn96/silver47 within1/2cp, not proven errors.
Top5 both parents keep king right. Pawn76 PV develops left silver68 then
bishop exchange/silver77/rook88/king28; king39 leader instead follows
pawn26/silver27/rook48; opponent not committed to static rook.
32.089s/13.407s complete/errors/stops/bounds0,308 input/PV moves legal,
analysis/audit8 tests passed. Input black-silver38-silver32-2026-10-05-shin.json;
raw SHA256 and full evidence in Black report. No book edits/games/adoption.
King39 after silver32 is a conditional candidate, not a proven gain.
Silver32 four-move parent rechecked fresh unrestricted ON depth26/MultiPV5,
same book-free/thread1/hash512 settings,63.270s complete,cumulative40.
King39 -98,pawn76 -115,pawn96 -133,pawn46 -139,pawn26 -140.
First/second order stable vs24; within26 king39/pawn76 gap17,not a proven gain.
Leader PV now normal static rook pawn84/85/rook86-56-54-74, not prior rook42;
Black silver68-57/gold78/silver46/silver47/rook48/gold38right,king39 throughout.
All5 PVs keep king right; long PVs are not stable enough to register.
Errors/stops/bounds0;158 input/PV moves legal;37 tests passed;hashes unchanged.
Input black-silver38-silver32-recheck-2026-10-05-shin.json; raw hash in report.
Keep only king39 as one-move conditional registration candidate, not yet added.
Close silver32 depth expansion here. Rook32 cohort8 (2/5/1) reviewed:
all fourth reply source=book; fifth search pawn46 in4 (1/3/0),pawn96 in3
(1/1/1),king39 in1 (0/1/0). Dedicated root only in all8; normal first search
ply6/8/10 in4/3/1. Sixth king62 in7, pawn35 in1; sixth book4/search4.
King24 right in7; r2/game31 king78/four same positions by32/max256 draw.
One fresh unrestricted ON depth24 root screen complete27.228s,cumulative41:
pawn76 -58,king39 -68,pawn46 -74,pawn96 -91,pawn26 -99. All5 PVs right king;
leader pawn46/silver47/king39/pawn86-85/pawn75/rook78/gold38right/gold58left.
Tiny10/16cp leader gaps; hold rook32 registration, no extra depth expansion.
145 input/PV moves legal;errors/stops/bounds0;analysis/audit8 tests passed.
Input black-silver38-rook32-2026-10-05-shin.json; raw hash in report.
Prepared separate5-entry trial retaining original4 entries
unchanged, adding ONLY silver32 parent -> king39. NOT operationally adopted.
Source books/shin-yonenaga-black-silver38-silver32-experiment.json;
book books/shin-yonenaga-black-book-silver38-silver32-experiment.txt;
SHA25642622adc1fb4cc479bd70af352e296b4b5fa413f91ccad9ea4fc161866ea5a17.
41 regression tests pass; added evidence matches raw; original/runtime unchanged.
Rare pawn66/exchange guard and rook32/pawn76 remain evidence-backed deferred
candidates, not simultaneous changes. Evaluate a bounded external comparison
with same-condition original-book reruns, not only historical38.5%.
External plan50x4: baseline-r1/trial-r1/trial-r2/baseline-r2, sequential fresh
processes, total200, original/trial100each. Outputs under results/
shin-black-silver38-silver32-<label>-depth15-50games.json; all completed October6.
All200/errors0; settings/records/outcomes/summaries/replay/book375 verified;
runtime/books current hashes match preparation. Original44%/47%, total38/47/15
(45.5%); trial32%/46%, total34/56/10 (39%). No causal overall gain established.
Silver32 cohort original19:5/9/5 (39.5%), trial23:13/8/2 (60.9%);
original fifth king39 only2 (both draws), trial23 all dedicated king39.
Non-target cohorts46.9%/32.5%; do not attribute overall drop to added move,
or call target-cohort rise a proven gain. Hold operational adoption;
close this one-change game comparison, retain both books/research candidate.
King24 right93/97; left return by12 zero in both. No king restrictions added.
October6 existing-data review: rook42 total72,18/43/11; left silver57 in62,
both golds still49/69 in48 at24. Early bishop captures6:3wins/3losses;
do not ban exchange or infer a causal failure from placement alone.
October6 focused followup complete:2 unrestricted24/MultiPV5 searches,
plus game31 same-parent limited24/MultiPV4, fresh ON/book OFF/thread1/hash512.
All3 complete/errors/stops/bounds0,592 input/PV moves legal,8 tests pass;
cumulative44 searches. Inputs black-silver38-rook42-preparation[-limited]-
2026-10-06-shin.json under docs/experiments/positions/book/; raw hashes/PVs
in the Black report. No book/engine changes or new games.
Common17 parent8: pawn76 +7,silver27 -41,pawn86 -51,gold58left/pawn36 -121.
Gold38right originally proposed is ILLEGAL: silver occupies38; corrected to
gold58right as comparison (outside top5, not separately scored).
Do not infer a universal gold-first rule. All5 PVs keep king right.
Game31 before17 actual rook48 unrestricted -136 first; limited rook48 -159,
pawn66 -418,gold78 -449,silver68 -3793. Compare only within each scope.
Silver68 removes silver79 recapture on88 and blocks rook28's horizontal
recapture; do not generalize earlier singleton pawn66-before-exchange finding.
All9 PVs here keep king right; actual exchange acceptance not proven error.
Common17 unrestricted26/MultiPV5 recheck complete100.289s,cumulative45.
Pawn76 -46,pawn86 -55,gold58left -86,silver27 -95,pawn66 -101.
Pawn76 first at24/26, but9cp gap to pawn86 at26; no unique best/gain claim.
All5 PVs right king; top2 keep king39/silver38/rook28, gold58left later
at33/31. Do not hard-code long PV or infer a universal pawn/gold timing rule.
Errors/stops/bounds0;216 input/PV moves legal;8 tests pass;book/runtime unchanged.
Input black-silver38-rook42-common17-recheck-2026-10-06-shin.json;raw hash in report.
Close parent depth expansion here, no28/30. Hold registration/new games.
Actual pawn76 fourgames (1win/3losses) ALL reply gold52 at18; top24/26 PV
instead silver43. Actual pawn76/gold52 parent19 ON/book OFF/fresh24/MultiPV5
now complete30.315s,cumulative46. Pawn86 -35,silver27 -56,bishop77 -63,
pawn75 -114,pawn66 -117; gold58left outside5, gold38right still illegal.
Exact parent reached6 incl trial-r1/games1,12 transpositions:1win/5losses;
silver27 fourlosses,pawn86 1win/1loss, not causal move comparisons.
All5 PVs right king; top2 use rook88 with silver27/gold38right after bishop
development. Left rook use is not king retreat; do not hard-code rook48.
Input black-silver38-rook42-pawn76-gold52-2026-10-06-shin.json;225 input/PV
moves legal,errors/stops/bounds0,8 tests pass;raw hash in Black report.
Close this small search cycle. Separate6-entry trial now prepared:
books/shin-yonenaga-black-silver38-silver32-pawn76-experiment.json and
books/shin-yonenaga-black-book-silver38-silver32-pawn76-experiment.txt.
Retains existing5 exactly +ONLY common17 pawn76 (leader24/26).
Leave19/deeper PV to search (pawn86/silver27 gap21 at one depth only).
New txt SHA284850ec7495a4d1889c79d393fe75e775cc56dc3cfe7b7ec7af2b0df1b9c299.
45 tests pass (4 new);6 evidence references/raw match;59 entry/transposed
moves legal;old/runtime hashes unchanged. No rebuild/eval/default changes.
Experimental NOT adopted. Target8 includes4 already pawn76;low expected impact.
External plan50x4: existing5 baseline-r1/new6 trial-r1/new6 trial-r2/existing5
baseline-r2, sequential fresh processes,each100,total200. Same fixedBlack
depth15/thread1/hash512/bookMax20/max256/timeout300/PonderOFF/normalbookON.
Outputs results/shin-black-silver38-pawn76-<label>-depth15-50games.json;
all200 completed October7/errors0;settings/records/summary/outcomes/replay/
book378 checked. Five-entry44%/49%,total40/47/13 (46.5%);six39%/45%,
total35/51/14 (42%). Current runtime/book hashes unchanged.
Target five1 (baseline-r2/game25):searched pawn76,win; six3 dedicated
(trial-r1/game2 draw,trial-r2/game23 loss,game50 win). Too few for effect;
non-target46.0%/41.8%,no causal attribution of4.5-point overall difference.
King24 right96each;left return by12 five0/six1;four-occurrences9each.
Hold six-entry operational adoption;close this single-branch comparison,
retain both experimental books/evidence. No automatic extra100 or deeper
common17 searches. Five-entry also unadopted;Whitev2/eval/default unchanged.
October7 pawn84 review34games complete:6/27/1. All use same11 moves through
gold78 after8-file exchange;normal searches from6 in all34,last book4.
Early bishop captures only1 loss;not a general explanation. At24 kingright32,
left silver68 in15/still79 in11;rook48 in25. Winning/losing cp25 medians
-180.5/-182,not evidence of universal opening collapse or move loss.
Two fresh ON/book OFF unrestricted24/MultiPV5 searches complete,cumulative48:
common13 (33games) pawn25 -125,silver68 -127,pawn16 -133,pawn46/gold58right
-162;actual silver27/king39 outside5. All5 PVs king48,early left-silver/rook29.
Common19 (15games) actual gold38right -157 first,pawn16 -161,king28 -165,
silver68 -168,actual pawn46 -172. All5 PVs kingright;no proven immediate failure.
Input black-silver38-pawn84-transition-2026-10-07-shin.json;raw hash/full refs
in Black report. 401 input/PV moves legal,errors/stops/bounds0,8tests pass.
Reuse old pawn84/pawn85 depth28 evidence;no root rerun/book changes/newgames.
Common13 four-candidate limited26/MultiPV4 complete37.695s,cumulative49:
pawn25 -119,silver68 -141,silver27/king39 -189. Within-run gaps22/70/70;
not unrestricted26 leader or causal winning gain;do not subtract24/26 scores.
Top2 PVs keep king48,develop left silver77/right silver47/rook29;actual2 PVs
transpose after16 and king39/28/rook48. All4 PVs right king.
Input black-silver38-pawn84-common13-limited-2026-10-07-shin.json;161 input/PV
moves legal,errors/stops/bounds0,8tests pass;raw hash in Black report.
Close parent depth expansion here;no automatic19/28/30/singleton/100games.
New separate6-entry pawn25 trial prepared:existing5 unchanged +ONLY common13
pawn25 entry;NOT prior common17 pawn76 extension. Leave15/deeper moves search.
Source books/shin-yonenaga-black-silver38-silver32-pawn25-experiment.json;
txt books/shin-yonenaga-black-book-silver38-silver32-pawn25-experiment.txt.
SHA52123e92c55e0dc33f1f77849daf481879f00dffb6e68c4831e93534a9a531c7.
Evidence explicitly restricted26 (not unrestricted26);all6 refs/raw match.
50 tests pass,51 input/book/transposed moves legal;old/runtime hashes unchanged.
Parent33/200,actual pawn25 zero at13;future frequency/gain not guaranteed.
External plan50x4:existing5 baseline-r1/pawn25 trial-r1/pawn25 trial-r2/
existing5 baseline-r2,each100,total200,sequential fresh. FixedBlackdepth15,
thread1/hash512/normalbookON/PonderOFF/BookMax20/max256/timeout300.
Outputs results/shin-black-silver38-pawn25-<label>-depth15-50games.json,
all200 complete October8/errors0;settings/records/summary/outcomes/replay/
book382 checked,current runtime/book hashes match. Five45%/35%,29/49/22;
trial39%/41%,32/52/16,both40% total. Targetfive15:5/10/0 (33.3%),trial13:
6/6/1 (50%);non-target41.2%/38.5%,no causal-gain claim. King24 right94/98.
Trialall13 reply bishop33;move15 pawn46 seven(4/3/0),rook26 five(2/2/1),
silver68 one(loss). Leftsilver79 at24 in12/13;target king48 eleven/king59 two.
Hold pawn25 operational adoption;close one-entry game comparison,no new100.
Trial/evidence are recorded in the current checkpoint;no mixed common17 changes.
October8 same15 parent limited26/MultiPV3 complete63.545s,cumulative51:
silver68 -132,pawn46 -151,rook26 -156. Gaps19/24 only,not a decisive error
diagnosis/unrestricted-best claim. Silver68 PV silver77/47/rook29,king48->38;
pawn46 PV returns59;rook26 keeps48 and prepares silvers/rook29 later.
Input black-silver38-pawn25-bishop33-followup-2026-10-08-shin.json;123 input/PV
moves legal,errors/stops/bounds0,8tests pass;raw hash in report.
Same15 unrestricted24/MultiPV5 now complete76.805s,cumulative52:
silver68 -101,rook26 -118,pawn46 -134,pawn16 -159,pawn96 -191.
Silver68 first in both restricted26/unrestricted24;other actual2 swap order,
scope/depth scores not subtracted. All5 PVs right king,leader king48->38,
silver77/47/rook29. Actual pawn46 king48 here vs59 in restricted26.
203 input/PV moves legal,errors/stops/bounds0,8tests pass;raw hash in report.
Input black-silver38-pawn25-bishop33-unrestricted-2026-10-08-shin.json.
Nearest actual gap17cp small;hold15 fixed registration and close this prep
comparison,no auto26/28/30/new100. Existing pawn25 six remains unadopted.
Concept-only silver68 one-entry extension is a future choice,not created;
separate concept achievement from strength claims,don't register long PV.
Prep/200/root reference/two15 searches are consolidated in the current
checkpoint. Next consider bounded Black operational choice;no automatic book/eval changes.
Separate first-king48 reference query completed October7:direct ['5i4h']
White-to-move normal OFF/book OFF/fresh unrestricted26/MultiPV5/thread1/hash512.
Pawn34 +113,pawn44 +97,pawn84 +61,pawn64 +60,silver62 +50 (WHITE cp).
Leading score converts to Black -113,NOT measured loss from startpos.
Normal OFF disables25cp preference for both colors;not mixed ON/OFF selfplay.
Top2 PVs return Black king59/68/78;do not read -113 as right-king-only value.
One search105.548s,cumulative50,errors/stops/bounds0;150 input/PV moves legal,
analysis3 tests pass;runtime/book unchanged. Input black-king48-direct-root-
2026-10-07-normal.json;raw hash/full PVs in Black report. No automatic root
deepening/new reply branches/book changes. Main pawn25 comparison is complete;
reference query/report/input are included in the current checkpoint.
Keep right-king priority/no retreat bans;bookMax20/eval unchanged.
Old pawn66-vs-exchange parent reached0 in these200; deprioritize registration.
Baseline-r1/game37 before23 is a deferred central-pressure counterexample,
outside BookMaxPly20; do not automatically add a third search/raise book limit.
The200-game audit was read-only; subsequent5 searches are separately recorded.
Give one caffeinate command at a time only when another external trial is ready.
Depth15/thread1/hash512/normalbookON/max256/timeout300/BookMaxPly20.
No local games; no rebuild needed; do not edit during external runs.
Inspect overall/run spread/reached cohort/book hits/control same king39 choices/
king placements/transition; no causal claims from cohorts/small differences.
If ambiguous hold adoption, close this single-change cycle, no indefinite games.
Preparation b174535, previous2282e88 and review d8ce83c were pushed to origin/main.
October6 focused searches/trial preparation and October7 completed comparison
were committed/pushed as8fb593a. The subsequent pawn84 review and three searches
were committed as c1a0508. The current checkpoint contains subsequent pawn25
trial preparation/tests, completed200 results, reference root and two15 searches;
see git log for its ID. Both checkpoints are included in the publication update.
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
