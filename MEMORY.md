# Rakuyou Development Notes

This file is the resume map: current state, durable decisions, constraints, and
links to evidence. Detailed experiment history belongs in `docs/experiments/`.

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
- No experiment is currently active. The next research objective has not been
  selected.
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
  Treat test splits as untouched; draw outcomes and max-ply draws have their
  recorded masking/adjudication limits. Existing `results/` attempt markers
  prevent reruns; never remove or bypass them.
- The 47-run self-play corpus has 2,740 games and 475,347 moves. Historical
  parameter/progress/probability identities are unknown. Existing train,
  validation, and test splits and their run-level separation are documented in
  [learning feasibility](docs/experiments/learning/framework/2026-10-11-learning-feasibility-plan.md).
  Gikou's normal `--learn` resets parameters/material; experiments used a frozen
  baseline plus deltas instead. Do not treat self-generated teachers as an
  independent stronger teacher.

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
- Book source JSON is grouped under `books/sources/`, held candidates under
  `books/experiments/`, and retired reproducible sources under `books/archive/`.
  Active book text paths and contents were preserved during cleanup.
- Tools and tests were moved into category packages; imports and CLI entry
  points were updated. The last full verification after that move passed 196
  tests. No engine/evaluation code changed in the organization work.
- `docs/development.md` now covers build, tests, and durable data safeguards;
  dated learning-stage instructions belong in experiment reports.
- Current branch was last committed and pushed at `505b1c3` (`origin/main`).
  The development-guide cleanup is in progress; recheck `git status` and recent
  history on resume.
