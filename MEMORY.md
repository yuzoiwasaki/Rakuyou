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
- Swap colors within each pair and keep depth, threads, hash, and book settings
  equal between comparison runs.
- Judge the experiment using playing strength and whether the intended king
  placement persists. Review losses and necessary retreats, not only wins.
- Prefer small, observable experiments before larger evaluation or architecture
  changes. A dedicated 新米長玉 book remains a future step.

## Self-Play Tool

- `tools/paired_selfplay.py` runs two Rakuyou processes without Shogidokoro:
  新米長玉 versus normal Rakuyou, with colors swapped once per pair.
- The normal side always uses the standard book. `--shin-book off|on` controls
  book use only for the 新米長玉 side. Ponder is disabled.
- The runner saves JSON after every completed game. It records results, moves,
  move sources, scores, principal variations, aggregate statistics, errors, and
  timing. `--resume` continues a partial run.
- See `docs/selfplay.md` for complete usage.

## Current Experiment

The first strength baseline is 50 pairs (100 games) at depth 15:

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --depth 15 \
  --threads 1 \
  --hash 512 \
  --shin-book off \
  --pairs 50 \
  --output results/shin-book-off-vs-normal-depth15-100games.json
```

Conditions:

- Normal side: `ShinYonenagaGyoku=false`, standard book enabled.
- 新米長玉 side: `ShinYonenagaGyoku=true`, standard book disabled.
- Each engine uses one thread and 512 MB hash.
- A local depth-15 timing sample suggested about 3 hours 20 minutes for 50
  pairs, but actual duration depends on the games and concurrent Mac usage.

Do not mark this experiment complete until the result JSON has been inspected.
Resume an interrupted run with:

```sh
caffeinate -i python3 tools/paired_selfplay.py \
  --resume results/shin-book-off-vs-normal-depth15-100games.json
```

## Immediate Next Steps

1. Analyze the first 100-game result: W/L/D, score rate, color split, average
   plies, termination reasons, and errors.
2. Inspect representative wins and losses for king movement, fixed-opening use,
   standard-book use, evaluation changes, and principal variations.
3. Repeat the same 100-game conditions with `--shin-book on` and a separate
   output file.
4. Compare the two runs before changing the 25 cp preference.
5. Use promising continuations as input to a later dedicated 新米長玉 book
   experiment.

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

Build the future 新米長玉 book by concentrating expensive analysis on important
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

Moderate-depth games are useful for finding where to analyze and for measuring
behavior. Treat deeper focused analysis as the main source of book move quality.

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
