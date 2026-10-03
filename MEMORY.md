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
  a1a5e25ada0d7be1375b45168586f00f7feaa29f1a87074a85b0e4b09c571f1b.
  Ignored binaries can survive branch switches; rebuild for changed engine code.

## Engine Behavior and Durable Decisions

- ShinYonenagaGyoku (default ON) controls both the fixed first move and an
  experimental 25cp opening king-location preference.
- Black opens 5i4h (king48); White opens 5a6b (king62), only from the initial
  position/matching one-move history, respecting legal root restrictions.
- Preference favors Black king files1-4 and White files6-9, fading to zero in
  middlegame; retreats are legal. OFF disables both features.
- Keep the toggle and 25cp value unchanged for the current book work.
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

The user approved ending the bounded White improvement cycle and proceeding
to Black book work, even without proving a winning score against standard
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

User-run comparison completed on October3, preparation commit da37690:
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

1. Audit and reanalyze those existing Black games, main branches, book exits,
   king paths and representative wins/losses before choosing entries.
2. First focused search parents (not yet run), Black ON, unrestricted
   depth24/MultiPV5, threads1/hash512, OwnBook OFF, fresh process:
   5i4h 3c3d;
   5i4h 3c3d 7g7f 7a6b;
   5i4h 3c3d 7g7f 8b4b.
   Check normal-OFF direct replies; deepen only promising close choices.
3. Build a separate small Black trial. Current builder is White-only; add
   explicit Black support and regression tests when implementing. Do not
   rotate/copy the White skeleton blindly or overwrite its operational book.
4. Provide external fixed-Black baseline/trial commands with the same current
   engine, normal book and settings. User runs long games outside Codex.
   Do not start long self-play here.

The user approved committing/pushing the White decision, completed comparison,
non-destructive documentation cleanup and Black starting plan. Engine defaults
and GUI settings were not changed; v2 requires explicit ShinBookFile selection.

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
