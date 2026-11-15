# Rakuyou resume map

Updated 2026-11-15.

- Active search trial: `experiment/root-candidate-recheck`, based on origin/main851dc0f, independent of opening PR2. Root likely near-fail-low alternative gets one wider-window PV verification per root invocation. Separate `bin/match-root-recheck`; baseline bin/match unchanged. Gx8g found at depth15 and within250k/300k reported nodes; other cases cost more.6-case diagnostics and8 shallow golden checks pass; not adopted. See docs/experiments/root-candidate-recheck.md. Opening work remains on experiment/early-silver68 (local f341b5d); do not merge either automatically.

- Adopted baseline: `src/` includes support10 and king-contact deficit D10; normal `make release` builds it. No separate adoption patch required.
- Release fixes ShinON/support10/D10: the3 style options are hidden and stale GUI setoption commands ignored. OwnBook/ShinBookFile remain editable. USI name Rakuyou; register `tools/run-engine.sh` for the current build. Dated snapshots are unchanged.
- `make development` builds `bin/development` with `RAKUYOU_DEVELOPMENT_OPTIONS` and a separate object directory; exposes3 style options under name Rakuyou (development). `make match` builds optimized `bin/match` (-O3 -DNDEBUG) with the same comparison options and separate obj/match; comparison tool defaults to match to avoid expensive debug checks. Position analysis defaults to release; OFF can use match. Release remains fixed ON/10/10.
- Fixed-style change validated:21 Python tests pass, including release ignoring stale settings before/after isready, unchanged default search values, development4-setting search parity, standard/dedicated book handling. Keep README short.
- Fast comparison build validated:23 Python tests pass;8 golden search cases across4 support/D settings and normal-side parity pass. Two bounded node searches match release/development results; match runs at release speed. Two24-ply paired preflight games pass. Long100-game run must start a new output with bin/match, not resume the old development run.
- Before implementation, consult the user about direct main commits versus a task branch and PR. Minor changes may go directly to main with approval; new features and evaluation changes normally use branches and PRs, with merging only after validation, review, discussion and explicit user approval. Only adopted code, maintained tools/tests and short docs belong on main; no dated trial reports or one-off runners.
- Before cleanup: `archive/pre-adoption-cleanup-2026-11-15` (`f488a64`). Old reports, scripts and decisions are recoverable there. Ignored `results/` and previous runtime snapshots remain local; old experiment hash checks require the old tree.
- Rank-commitment and exchange-burden prototypes were rejected. No new evaluation terms or training adopted.
- Style: thick, coherent shogi; sustain viable territory, allow bait/counterplay when support is unsustainable, and convert thickness into attack when appropriate.
- Review obvious actionable defects regardless of game result. Skip losses without a clear issue; small score differences alone do not justify tuning.
- User runs long matches from prepared commands. Short bounded diagnostics are fine. Never infer strength from the small development batches.
- Recent initial-position pairs: adopted side lost both games in bookOFF and normal-bookON batches. Not pooled strength evidence. Normal book was used only2/3 moves in the latter pair.
- Silver retreat at move36 of the bookOFF White game is acceptable: Sx7e−48 vs S6c−61 at depth13; user prefers natural retreat with a thin king. No correction adopted.
- Recastling after development is acceptable (bookON Black33 K5i through43 K8h). Early abandonment of the intended king setup would be a correction candidate; no blanket penalty or hard ply cutoff agreed.
- `docs/development.md`: operational settings, tests, recovery and branch workflow. `books/README.md`: current book reproduction.
- Cleanup validated:18 Python tests passed;132 native positions×4 settings and8 fixed-depth search cases match the adopted reference. Book17 positions reproducible; recapture18 cases and terminal move-picker checks pass.
- Repository reduced from758 tracked files to148;615 obsolete files removed and5 maintained test/launcher files added. Cleanup branch: `chore/adopt-support10-d10-cleanup`. Old `bin/release` backed up at ignored `results/adoption-cleanup-2026-11-15/previous-release`.
