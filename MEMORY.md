# Rakuyou resume map

Updated 2026-11-15.

- Adopted baseline: `src/` includes support10 and king-contact deficit D10; normal `make release` builds it. No separate adoption patch required.
- USI name remains Rakuyou. Keep the root README a short project introduction.
- Work on task branches. Only adopted code, maintained tools/tests and short docs belong on main; no dated trial reports or one-off runners.
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
