# Rakuyou Development Notes

This file is the resume map for future work. Keep it focused on the current
implementation, durable decisions, active experiments, and immediate next steps.
Use Git history for completed work and chronology.

## Project Snapshot

- Rakuyou is a personal experimental fork of Gikou 2.
- `main` contains the current 新米長玉 implementation and its comparison tool.
- Apple Silicon builds the SSE 4.2 engine as x86_64 through Rosetta. See
  `docs/development.md` for setup and build commands.
- The local runtime data needed by the engine are present in `bin/`:
  `params.bin`, `progress.bin`, `book.bin`, and `probability.bin`.
- The engine identifies itself as `Rakuyou`; its author string credits Gikou and
  Yosuke Demura.

## Current Shin-Yonenaga-Gyoku Behavior

- `ShinYonenagaGyoku`, a USI check option enabled by default, controls the whole
  experiment for one engine process.
- When enabled, Black opens with `5i4h` (▲4八玉) and White with `5a6b` (△6二玉).
  The fixed move applies only to the standard initial position or the matching
  one-move history, and respects legal root-move restrictions.
- It also applies a 25 cp opening preference for keeping Black's king on files
  1–4 and White's king on files 6–9. The preference fades to zero by the
  middle-game progress point; it does not forbid a retreat.
- When disabled, both the fixed opening and the 25 cp preference are disabled.
  This lets the same binary act as the normal comparison engine.

## Durable Decisions

- Keep the fixed first move and the 25 cp preference under one toggle.
- Treat 25 cp as an experimental value to revisit after controlled games.
- Compare against normal Rakuyou with its standard book enabled.
- Test the 新米長玉 side with its standard book both disabled and enabled.
- Use color-swapped pairs for broad comparisons, and fixed-color games when
  measuring a book that only applies to one side. Keep depth, threads, hash,
  and book settings equal between comparison runs.
- Judge the experiment using playing strength and whether the intended king
  placement persists. Review losses and necessary retreats, not only wins.
- Prefer small, observable experiments before larger evaluation or architecture
  changes. The first dedicated White book is implemented from the reviewed
  candidate set. Its initial strength validation is complete, but a book
  benefit remains unconfirmed.

## Self-Play Tool

- `tools/paired_selfplay.py` runs two Rakuyou processes without Shogidokoro:
  新米長玉 versus normal Rakuyou. It swaps colors once per pair by default;
  `--shin-side black|white --games N` fixes Shin's color for targeted tests.
- The normal side always uses the standard book. `--shin-book off|on` controls
  book use only for the 新米長玉 side. `--shin-book-file` selects its dedicated
  position book independently of the normal side. Ponder is disabled.
- The runner saves JSON after every completed game. It records results, moves,
  move sources, scores, principal variations, aggregate statistics, errors, and
  timing. `--resume` continues both paired and fixed-color runs, including
  pre-existing paired JSON without a `shin_side` setting.
- See `docs/selfplay.md` for complete usage.

## Current Experiment

The four fixed-White runs completed 100 games each without errors on
September 30–October 1. Their full review is
`docs/experiments/2026-10-02-fixed-white-four-books-depth15.md`:
v1 scored 24/64/12 (30.0%), v2 36/52/12 (42.0%), no-book 21/68/11
(26.5%), and standard-book 29/50/21 (39.5%). Shin used no standard-book
moves in the last run, so its 13-point difference from no-book is not
evidence of a book benefit. V2 used the added `2c2d` in 70 games.
V2 is the recommended existing candidate for the next validation baseline,
not a confirmed official book; no book or engine changes were made.
The combined previous and current White data are v1 55/123/22 over 200 games
(33.0%) and v2 66/105/29 over 200 games (40.25%), with important run-to-run
variation. `tools/review_white_runs.py` audits records and reproduces the
four-run statistics, branches, and descriptive uncertainty intervals.
The engine retains its processes and some search state between games;
`StartNewGame()` does nothing, while per-search resets clear only some state.
Do not assume independent games or attribute the observed score gaps to this
mechanism without further checks.
The two search-only datasets produced immediate `1c1d` in 127/200 games.
Eight games reached `7c7d` by ply 20 and `7b7c` by ply 24 (3/3/2);
seven had Sente's `8h7g` before the pawn push, and one answered `6f6e`.
These are focused-analysis seeds, not new book entries.

The October 2 high-stage review is appended to the same report. It retains
v2 as the leading existing validation candidate, but emphasizes that every
game followed `7g7f 5a6b 2h6h`: this is a fourth-file-rook benchmark, not a
general White opening-strength test. Immediate `1c1d` was already within
3 cp of the leaders in the older depth-24 MultiPV-12 analysis.
The most interesting new combination is edge waiting (`1c1d` / `1d1e`),
deferring the rook-pawn push, then contextual `7c7d` after `8h7g`, with
flexible ordering of `6b7a` and `7b7c`. A second seed is no-book game 38:
earlier `7a7b` in the `5c5d` skeleton, answering `6f6e` with `7c7d`.
Verify parent feasibility and strong opponent replies before adopting either.
`docs/experiments/positions/book/high-review-2026-10-02-opponent.json` has
three opponent positions (Shin off); the matching `-shin.json` has six White
positions (Shin on). Their 74 input moves were checked with engine legalmoves.
No new deep searches or games were run. `tools/audit_white_positions.py`
reconstructs placement and hands and detects four identical position
occurrences. It found 5/5/5/8 such games across v1/v2/no-book/standard;
all 23 were saved draws. All 400 final positions plus the 23 repetition
positions matched the engine's board/turn/hands output. This is not full
independent legality or perpetual-check adjudication. Startup Zobrist keys
are randomized, another possible source of search variation alongside
retained shared state and opponent-book randomness, not a measured cause.

Phase 1 edge-wait analysis is complete; see
`docs/experiments/2026-10-02-edge-wait-seventh-file-analysis.md`.
Fifteen distinct positions produced 19 completed searches: 15 at depth24,
four at depth28, all one-thread/512MB/book-free and fresh process per position.
At depth28, contextual `7c7d` was first in standard games81/43 and second,
1 cp below `2d2e`, in game63. Keep it as a conditional branch, not a fixed
main book. Before game81's `7a7b`, depth28 tied `3d3e`/`6b5a` at -167;
`7a7b` was third at -207. Normal-side leaders include early `1g1f`, `6i5h`,
and `3h2h` instead of the assumed bishop77. After that last reply, `7c7d`
was outside the top5. After contextual `7c7d`, direct replies supported
flexible silver/king/pawn ordering; game63's actual `6f6e` favored `7b7c`.
All saved candidates reached the requested depth without timed stops or
bound scores. The resumed initial screen retains one Broken-pipe error record,
alongside a validated completed result for that ID; other six files have no
errors. Do not call the entire execution error-free. Engine/books unchanged;
analysis tooling adds optional `--fresh-engine` with three lifecycle tests.

Phase 2 and a separate seventh-file trial book are complete; see
`docs/experiments/2026-10-02-early-silver72-and-seventh-trial.md`.
At the `5c5d` skeleton's early parent, depth28 ranked `7a7b` first at -205,
with existing `4b5c` second at -207. But against actual `6f6e`, `7c7d` stayed
outside unrestricted top5 at depth24/28; a separate restricted depth28
comparison ranked `8c8d` -184, `6b7a` -195, and `7c7d` -239. The 55 cp
gap applies only within that restricted comparison. Normal-side `6i5h` after
the experimental pawn74 favored king71 before silver73, unlike the saved
game's `7i7h`. Do not force the phase2 pawn74 response into an official book.
The user nevertheless wants a concept trial, so the new standalone book uses
phase1 edge waiting with earlier silver72, not the inferior game81 parent.
Six additional depth24 entry/preparation checks support the selected sequence;
two chosen preparation moves trail by13/21 cp, explicitly recorded as concept
choices. Total new analysis: 14 positions/17 completed searches, no errors.
`books/shin-yonenaga-white-seventh-edge-experiment.json` contains 13 experimental
entries; generate `books/shin-yonenaga-white-book-seventh-edge-experiment.txt`
with `tools/build_shin_book.py --experimental --source ... --output ...`.
Unknown replies fall back to search; bishop77 is not forced. The builder
requires an explicit output and protects v1/v2. All 13 moves, transposition,
fallback and normal book behavior passed eight new tests; existing five book
tests and three analysis tests also passed. Engine/v1/v2 hashes unchanged.
Trial usage and exact external White-only100 command are in the report.

Both initial strength comparisons finished with 50 pairs (100 games) at depth
15 and no errors. With its book disabled, 新米長玉 scored 25 wins, 56 losses,
and 19 draws (34.5%). With the standard book enabled, it scored 32 wins, 56
losses, and 12 draws (38.0%). The observed difference was 3.5 percentage points,
but 新米長玉 used the standard book in only one game for five moves, so the
difference is not evidence of a book benefit.

The book-enabled score rate was 46.0% as Black and 30.0% as White. The color
gap remains a priority for analysis. See the two reports in `docs/experiments/`
for settings, integrity checks, uncertainty, conclusions, and raw-data
checksums.

`tools/analyze_selfplay.py` combines result files into opening-prefix tables,
same-engine two-ply evaluation-drop candidates, and a small representative-game
list. Its first 200-game report is
`docs/experiments/2026-09-26-selfplay-opening-analysis.md`. The combined score
was 44.5% as Black and 28.0% as White. Prioritize the White 新米長玉 branch
starting `7g7f 5a6b 2h6h`; several frequent continuations scored poorly, but
they require deeper position analysis before any move is rejected.

`tools/analyze_positions.py` runs book-free MultiPV analysis for named move
sequences and can disable the experiment evaluation when selecting normal-side
opponent replies. The first five anti-fourth-file-rook positions were analyzed at
depths 20 and 24; see
`docs/experiments/2026-09-26-anti-fourth-file-rook-focused-analysis.md`.
The clearest original candidate was `7c7d` followed by `7b7c`; the historical
`4b5c` silver development was also supported. The common `7b8c` move was only
slightly behind alternatives, while `8b6b` was best after reaching its tested
position, so do not blame either move in isolation.
At the base position immediately after `7g7f 5a6b 2h6h`, expanded depth-24
MultiPV placed `8c8d`, `5c5d`, and `3a4b` equal at -190 and `7a7b` at -192.
An immediate forced `7c7d` scored -291, so prepare the seventh-file plan with
the silver before pushing that pawn.
Keep focused depth-based analysis at one thread. A depth-24 MultiPV-12 benchmark
of the base position took 73.2 seconds and 111 million nodes with one thread,
versus 78.1 seconds and 226 million nodes with two; parallel search changed the
tree and candidate order without reducing wall time.

The first historical-line analysis is in
`docs/experiments/2026-09-27-historical-line-analysis.md`. Both source games
transpose after `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c`. Their immediate
`6c6d` after `4h3i` scored about 96 cp below `7a7b` and `8c8d`, although the
historical replies after committing to it were supported. The modernized
historical skeleton delays `6c6d` and continues with `4h3i 7a7b 6g6f`, followed
by `6b7a` or `8c8d`. Normal-side analysis chose an early `6f6e` first against
both waiting moves, confirming that left-side activity must be a main branch.
The replies converge: after `6b7a 6f6e`, `8c8d` was clearly best; after
`8c8d 6f6e`, `8b8c` and `6b7a` were nearly equal. The `6b7a` route later used
`7a8b` in its PV. Direct checks of four quieter opponent moves usually converged
on the same `6b7a`, `8c8d`, and `7b8c` structure, though the exact move order
depends on Sente's reply. With the king on 82 and silver on 83, the engine kept
the king on 82 and preferred a rook shift to 42 after `5h4g`; treat this as a
modernized king-and-silver arrangement rather than forcing the historical king
to 83. Earlier, after `5c5d 6g6f`, the historical `3a4b` was best, so the
core silver development also survives when Sente delays castling.

The first original seventh-file analysis is in
`docs/experiments/2026-09-27-original-seventh-file-analysis.md`. Do not play
`7c7d` mechanically after `7a7b`; against most immediate Sente replies it was
outside the top candidates. After Sente commits `8h7g`, `7c7d` can lead to a
sound `7b7c` structure, but Sente has little reason to play `8h7g` before White
advances the rook pawn. Preparing with `8c8d` made `8h7g` natural, but then
`7b8c` was preferred and `7c7d` ranked seventh, eighth, or outside the top eight.
Preparing with `6b7a` and allowing a second natural Sente development move also
left `7c7d` outside the top eight in all five tested branches. Keep the
seventh-file structure only as an opportunistic branch; it is not currently a
practical main-book line. If reached, it remained sound against an early
`6g6f` / `6f6e` attack. Do not play `8b7b` immediately after completing the
structure: forced tests were 132–166 cp below the best move in four normal
branches and lost 634 cp with a bishop on 86. In the successful self-play
position, however, `8b7b` immediately after Sente's `7f7e` was the clear best
move at -136, 24 cp above the next candidate. Treat the rook shift as a timed
counterattack against `7f7e`, not as an automatic part of the setup.

The standard-book reachability recheck is in
`docs/experiments/2026-09-28-original-seventh-standard-book-recheck.md`.
After `7g7f 5a6b 2h6h 7a7b`, the normal side chose `5i4h` from `book.bin`
in all 12 earlier self-play occurrences and all 10 direct probes. If White
then forces `7c7d`, the normal side leaves its book. At the `5i4h` position,
unrestricted depth-28 MultiPV-16 ranked `7c7d` eighth, 48 cp behind `3a4b`.
Normal-side depth-24 search after `7c7d` put `3i3h` and `4h3h` within 2 cp.
White-side depth-28 search ranked `7b7c` first after `4h3h`, but second and
29 cp behind `6b5b` after `3i3h`. Earlier 2W/1L games with the early seventh-
file structure used different move orders. Keep it as a situational side
branch, not a new main entry or a claimed strength gain; the dedicated book
remains unchanged.

The first dedicated White book candidate is the historical `5c5d` line in
`books/shin-yonenaga-white-candidates.json`, documented in
`docs/experiments/2026-09-27-first-white-book-candidates.md`. Its reviewed
mainline is `7g7f 5a6b 2h6h 5c5d 3i3h 3a4b 5i4h 4b5c 4h3i 7a7b 6g6f
6b7a 7i7h 8c8d`. The final `8c8d` was first at -201 in a direct depth-28
MultiPV-5 run, 11 cp ahead of `2c2d`; its raw JSON and checksum are in the
report. Early `5c5d 5i4h` and `5c5d 6g6f` responses are reviewed side
branches. The `6b7a 6i5h` response remains unstable. The initial `8c8d`
branch and its descendants are outside the first dedicated book. The candidate
JSON remains a review artifact. `tools/build_shin_book.py` generates the
engine-readable `books/shin-yonenaga-white-book.txt` with six mainline and
three reviewed side-branch positions; unstable candidates are excluded.
`ShinBookFile` makes the enabled 新米長玉 side use this file, while the normal
side keeps `book.bin`. Uncovered positions fall back to search, not the
standard book. The paired runner records these moves as `dedicated_book`.
The integration check is `python3 test/test_shin_book.py`; a depth-1,
two-game smoke run used the dedicated book five times as White, but is not a
strength result. Keep raw analysis and self-play in ignored `results/`.

The first dedicated-book validation completed 50 pairs / 100 games at depth 15;
see `docs/experiments/2026-09-28-shin-dedicated-white-book-v1-vs-normal-depth15.md`.
As White, Shin scored 13 wins, 30 losses, and 7 draws (33.0%), versus 30.0%
in the previous standard-book baseline. The 3-point difference is too small
to attribute to the book across separate runs. All 50 White games used the
dedicated book; 41 reached `7i7h 8c8d`. The next frequent Sente moves were
`7h6g` in 23 games and `6i5h` in 17. As Black, Shin scored 23 wins, 23 losses,
and 4 draws (50.0%) without using the dedicated book. No game errors occurred.

The post-exit review is in
`docs/experiments/2026-09-28-first-white-book-post-exit-analysis.md`.
Normal-side depth-24 MultiPV put `7h6g` and `6i5h` within 2 cp after the
mainline's `8c8d`, matching their high self-play frequency. White-side depth-28
MultiPV preferred `1c1d` after either move, but depth-24 leaders differed, so
neither reply has been added to the book. In 21 games the two move orders
transposed after `3c3d`; White searched `7b8c` in 20. At that position,
depth-24 MultiPV-12 ranked `7b8c` fourth, 27 cp below `2c2d`; a restricted
depth-28 comparison placed it 38 cp below `4a5b`. Normal-side depth-24 analysis
chose `7f7e` against `7b8c`, an answer absent from depth-15 self-play. Treat
this as a concrete branch to recheck, not proof of a move-level cause for losses.

An unrestricted depth-28 MultiPV-5 recheck of that transposition is in
`docs/experiments/2026-09-28-first-white-book-post-exit-depth28-30.md`.
It ranked `1c1d` first at -201 and `2c2d` second at -207, with the frequent
`7b8c` fourth at -283. The earlier three-move restricted search had ranked
`4a5b` first among those three, but unrestricted search put it third and 70 cp
behind `1c1d`. Normal-side direct replies after `1c1d` chose `9g9f` first;
after `2c2d`, `3i2h` and `8h7g` were within 1 cp. White-side depth-28 checks
then preferred `2c2d` after `1c1d 9g9f`, `2d2e` after `2c2d 3i2h`, and
`1c1d` after `2c2d 8h7g`. Keep both `1c1d` and `2c2d` as candidates, and do
not extend the dedicated book yet. An earlier 900-second time-boxed depth-40
request emitted provisional depth-30 values after `stop`; do not use those
values as a completed depth-30 result. `tools/analyze_positions.py` now
snapshots the last MultiPV depth present before sending `stop`, and the
time-bounded output records `stopped_early`. The `candidate_bestmove` field
comes from the saved rank-one PV; `bestmove` is the engine's later USI reply
and may differ after a timed stop. Prefer searches that finish their
requested depth when candidate scores are close.

The same post-exit report now also covers the two frequent book exits. In
completed unrestricted depth-30 MultiPV-5 runs, `2c2d` ranked first after
both `7h6g` and `6i5h`, whereas depth 28 had ranked `1c1d` first at both.
The normal side directly chose `7f7e` first after `7h6g 2c2d` and `8h7g`
first after `6i5h 2c2d`. White-side depth-28 checks preferred `2d2e` after
the former and tied `1c1d` / `7b8c` after the latter. Treat two `2c2d`
entries as a small experimental second-book variant, not a proven best move.
The experimental v2 book is generated by overlaying
`books/shin-yonenaga-white-v2-experiment.json` on the unchanged v1 candidates,
producing `books/shin-yonenaga-white-book-v2-experiment.txt` with 11 positions.
Direct engine checks confirm that both new exits return `2c2d` as
`dedicated_book`, while v1 still searches there. Its 50-pair / 100-game
validation finished without errors; see
`docs/experiments/2026-09-28-shin-dedicated-white-book-v2-vs-normal-depth15.md`.
As White, Shin scored 18 wins, 22 losses, and 10 draws (46.0%), versus v1's
13/30/7 (33.0%). All 34 reached v2 exits used `2c2d` from the dedicated
book: 21 after `7h6g` and 13 after `6i5h`. This was an encouraging separate-run
result, not a causal proof. The normal side's frequent search replies after
`2c2d` were `6i5h` and `4g4f`; neither direct depth-28 leader `7f7e` nor
`8h7g` appeared in these depth-15 games. The time-boxed depth-32 output for these
exits is provisional and excluded because the old tool saved post-stop values.

An unchanged v2 repeat finished 50 pairs / 100 games without errors; see
`docs/experiments/2026-09-29-shin-dedicated-white-book-v2-repeat-vs-normal-depth15.md`.
As White, Shin scored 12 wins, 31 losses, and 7 draws (31.0%); as Black,
14/20/16 (44.0%). The added `2c2d` was used in 41 White games, but the first
run's 46.0% White score did not reproduce. The frequent transposition after
`7h6g` and `6i5h` scored 6/16/1 in 23 games; normal-side replies after `3c3d`
included more `6g5f` and `8h7g`. Do not attribute the score change to one book
move or to the Mac's clamshell sleep. Treat v2 strength as unconfirmed.

The two v2 runs were combined for a focused White-side branch review in
`docs/experiments/2026-09-29-shin-dedicated-white-book-v2-two-run-branch-review.md`.
Across 100 White games, Shin scored 30/53/17 (38.5%). The frequent
post-`2c2d` transposition appeared 41 times. Completed depth-30 MultiPV
rechecks of its two parent positions both ranked searched `3c3d` first.
After `3c3d 4g4f`, completed depth-28 ranked the frequent `7b8c` first.
After `3c3d 6g5f`, depth 28 ranked `3d3e` first but depth 30 reversed to
`4c4d`; after `3c3d 8h7g`, depth 28 ranked `1c1d` first but depth 30
reversed to `7c7d`. These are unstable rankings, not proven new book moves.
Keep v2 unchanged and raw analysis JSON ignored under `results/`.

An unchanged v1 repeat also finished 50 pairs / 100 games without errors; see
`docs/experiments/2026-09-29-shin-dedicated-white-book-v1-repeat-vs-normal-depth15.md`.
As White, Shin scored 18/29/3 (39.0%), versus the first v1 run's 13/30/7
(33.0%); as Black, it scored 13/26/11 (37.0%). All 50 White games used the
dedicated book. Across both runs, v1 White scored 31/59/10 (36.0%), while v2
scored 30/53/17 (38.5%). The 2.5-point difference does not establish a better
book. In the main v1 branch, searched `7h6g` scored about 30% in both runs,
while searched `6i5h` varied from 29.4% to 64.7% with 17 games each time.
Keep both book versions unchanged pending a deliberate comparison decision.

## Immediate Next Steps

The four fixed-White runs, medium analysis, and high review are complete.
The user runs long self-play commands outside Codex; provide commands rather
than starting further runs here. The user approved the following sequence:
checkpoint this review and plan with a commit/push, then start step 1 below.
The earlier review checkpoint was pushed as `1ba5461`; step 1 is now complete.
Its report, input queues, and analysis-tool test/update are checkpointed in a
separate commit (`07defdd`). Steps 1 and 2 are complete; the user requested
committing the phase2/trial artifacts and pushing both checkpoints together.
The user explicitly wants to try a small `7c7d`-structure book based on step 1
or 2 even if it is not the engine's best choice. Record any forced move's
evaluation cost and limited reachability honestly; do not call it an official
book or a strength gain. Prepare a separate experimental book and commands,
without starting long self-play inside Codex or changing v1/v2.
The standalone phase1-based trial and phase2 report are checkpointed in Git.
Next is the user's external depth15/threads1/hash512 White-only100
run using `books/shin-yonenaga-white-book-seventh-edge-experiment.txt` and
`results/shin-seventh-edge-white-only-depth15-100games.json`. Measure actual
dedicated-book pawn74 usage and simultaneous pawn74/silver73 placement, not
just overall score. If coverage is negligible, do not reject the concept from
that run. No long run has been started here.
Use the prepared opponent/White queues for bounded focused engine analysis.
The official White book is not restricted to v1/v2:
explore from the fixed `6b` opening, including immediate `1c1d` and contextual
seventh-file structures, then validate ideas with deep engine searches and
games. No expensive searches or new games were started during the high review;
the later phase1/2 focused searches are documented separately above.
Do not spend another review pass on the same data before obtaining new engine
evidence. An independent concept review can be reconsidered after the tests.

1. Completed: analyze edge waiting (`1c1d` / `1d1e`) with `8c8d` deferred, then contextual
   `7c7d` / `7b7c`. Start with strong normal-side replies to the early edge
   moves, and compare winning and losing source positions. Do not force Sente
   to play `8h7g`, or require `6b7a` before every `7c7d`. Check parent move
   feasibility as well as the attractive final setup. Use completed one-thread
   depth-based searches; compare scores only within a consistent perspective.
2. Completed: check the `5c5d` skeleton with earlier `7a7b`, especially meeting actual
   `6f6e` with `7c7d`, including its parent position and strongest replies.
3. The requested concept trial is built separately without changing v1/v2.
   Validate against the existing v2 benchmark, and repeat v2 if a small gain
   needs confirmation. Keep the same engine and normal-side settings, record
   binary hashes, run variation and target-structure reachability.

The later alternatives include a Black-side version and a gold-and-silver
advancement setup; prioritize the White tests above before these.

Additional constraints and maintenance:

1. Keep v1 and v2 unchanged pending review. V2 is the leading existing
   candidate, but its superiority is unconfirmed. Check strong opponent
   replies at its two `2c2d` exits, including `7f7e`, `8h7g`, and the frequent
   `6f6e` attack. The focused depth-24/28/30 analyses did not establish a
   stable v3 entry. Treat later-position
   `7c7d` after `3c3d 8h7g` as an unconfirmed candidate, not a revival of the
   earlier `7a7b 5i4h 7c7d` route. Keep the older common-transposition `7b8c`
   out of the book unless new evidence supports it.
2. If a small strength gain needs confirmation, compare dedicated-book on/off
   with the same current engine build and normal side's standard book enabled.
   Keep the initial `8c8d` branch outside this book.
3. Revisit Black-side book coverage and the 25 cp preference only after a
   concrete comparison plan.
4. Add formal repetition and perpetual-check adjudication while retaining the
   WCSC-compatible 256-ply draw limit.

## Experiment Data Management

- Keep raw self-play JSON under the ignored local `results/` directory. Raw
  files contain every move, score, and principal variation and should not be
  committed to Git as they grow quickly across repeated experiments.
- Commit a Markdown report for each completed experiment under
  `docs/experiments/`. Record the source commit, complete engine settings,
  comparison conditions, game count, W/L/D and score rate, color split, average
  plies, termination reasons, errors, representative games, conclusions, and
  the raw file's SHA-256 checksum.
- Commit reusable analysis scripts so summaries and later comparisons can be
  reproduced from the raw JSON.
- Keep raw files locally at first. Back up important completed datasets to a
  `Rakuyou-results/YYYY-MM-DD/` folder on Google Drive when the collection grows
  or when losing the local copy would matter.
- Prefer a gzip copy for backup while retaining the local JSON when it is still
  being analyzed:

```sh
gzip -k results/EXPERIMENT.json
```

- Put compressed datasets on Google Drive rather than in Git history. Use names
  that include the comparison, depth, game count, and date, and use the checksum
  in the committed report to identify the exact source data.

## Dedicated Book Development Plan

Build the 新米長玉 book by concentrating expensive analysis on important
opening branches rather than running every full game at a very high depth.

1. Use moderate-depth self-play to collect a broad set of opening positions.
   Identify frequent branches, early exits from the normal book, evaluation
   drops, recurring losses, and successful 新米長玉 continuations.
2. Select a smaller set of important opening positions. Favor positions that
   occur often, distinguish candidate moves, or appear to decide whether the
   initial king move can be recovered.
3. Reanalyze those positions at greater depth or with a longer time limit. Use
   MultiPV so the data retain several candidate moves and their evaluation gaps,
   rather than only the engine's first choice.
4. Use strong external games, including relevant Floodgate records, as supporting
   evidence for transpositions, related right-king structures, and the opponent's
   strongest attacking plans. Do not assume external games directly cover the
   unusual fixed opening.
5. Add only reviewed continuations to a dedicated 新米長玉 book, then compare it
   against the same book-enabled normal baseline with colors swapped.
6. Repeat collection, focused analysis, book updates, and paired validation.
   Keep the source position, analysis settings, candidate evaluations, and
   validation result traceable for every adopted line.

The near-term goal is for the fixed `6二玉` opening to win more games than it
loses against normal Gikou 2. Use this local baseline to decide whether later
book and evaluation changes are actually improving the opening.

Moderate-depth games are useful for finding where to analyze and for measuring
behavior. Treat deeper focused analysis as the main source of book move quality.

Historical source games are kept locally under the ignored `local/kifu/`
directory. Keep complete third-party KIF files out of Git; commit source
metadata and derived Rakuyou analysis or reviewed book candidates when needed.
Treat those two games as candidate seeds rather than a required target. The
first book uses the reviewed historical `5c5d` skeleton; compare later
extensions with original branches using focused analysis and paired validation.

## Known Limits and Checks

- The runner recognizes engine resignation, entering-king declaration, and the
  maximum-ply draw. It does not yet implement strict repetition and every
  official adjudication rule.
- One hundred games can reveal a large difference and useful behavior patterns,
  but may not establish a small strength difference with confidence.
- Rebuild after switching to a commit with different engine code; ignored build
  artifacts can survive branch switches.
- If GUI behavior differs from a fresh command-line run, restart the GUI engine
  so it reloads the binary and runtime data.

## Working Conventions

- Preserve upstream copyright headers.
- Use `gyoku` in branch names for 玉.
- Keep experiment labels out of code comments when the branch or option already
  supplies the context.
- Follow existing C++ style: file-local helpers use anonymous namespaces. The
  opening helper is `GetOpeningMove`; its log label is `Shin-Yonenaga-Gyoku`.
- Keep detailed build instructions in `docs/development.md` and tool usage in
  `docs/selfplay.md`. Update this file by replacing stale state rather than
  appending a chronological changelog.
