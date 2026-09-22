# Rakuyou Development Notes

This repository is a personal experimental fork of Gikou 2.

## Current State

- The codebase is mostly the cloned Gikou 2 source.
- `README.md` has been changed to describe Rakuyou as a personal experiment.
- `Makefile` has been adjusted for Apple Silicon Mac by building the SSE 4.2 engine as x86_64 via Rosetta.
- The USI engine name has been changed from `Gikou 2 (v2.0.2)` to `Rakuyou` in `src/usi.cc`.
- The Rakuyou USI author string in `src/usi.cc` has been changed to `Yuzo Iwasaki, based on Gikou by Yosuke Demura`.
- `AGENTS.md` has been added for durable Codex working rules; this file remains the resume map.
- A short Apple Silicon build note, adapted from upstream PR #10’s README addition, is in `docs/development.md`, referenced by `AGENTS.md`. The README intentionally omits the development link.
- The Apple Silicon OpenMP setup and release build have succeeded on this machine. The previous missing `omp.h` issue is resolved locally.
- `bin/params.bin`, `bin/progress.bin`, `bin/book.bin`, and `bin/probability.bin` are present locally. The probability file came from the upstream release archive; a fresh `bin/release` USI startup reported no missing-file warning. Restart an already running GUI engine to load it.
- 新米長玉 from `experiment/shin-yonenaga-gyoku` is now integrated into `main` in `src/thinking.cc`: Black opens with `5i4h` (▲4八玉), White with `5a6b` (△6二玉), then uses the existing book/search behavior. No option is required.
- Opening selection requires the standard initial position or one move from it in the supplied history. Standalone intermediate SFEN positions do not trigger White’s opening. Legal root moves and USI restrictions are respected; infinite/ponder wait for stop/ponderhit.
- Initial verification passed 13 USI checks. The smoke-test script was removed at the user’s request; use manual USI or GUI checks for now. Ignored build artifacts survive branch switches, so rebuild after switching.
- Merge verification: release build succeeded; manual USI checks confirmed ▲4八玉, △6二玉 after either ▲7六歩 or ▲2六歩, and subsequent normal search.
- `experiment/gyoku-right-preference` now contains a 25 cp opening penalty when Black's king is outside files 1–4 or White's is outside files 6–9. The penalty fades to zero by the middle-game progress point. It is a separate `EvalDetail` term, updated in both full and incremental evaluation; no move is forbidden.
- Release and development builds passed. A temporary local probe checked both colors, retreat and unmake, and zero preference from middle-game progress onward. Development search to depth 3 passed its full-versus-incremental evaluation assertions. Playing behavior and strength have not yet been compared under controlled conditions.

## Direction

Work in small steps. Prefer low-risk, observable changes before large strength improvements.

- Keep the README minimal and shared build instructions concise in `docs/development.md`; keep branch-specific handoff notes in `MEMORY.md`.
- Develop the 新米長玉 concept further. A brief README description may be added later; leave the current overview unchanged for now.
- Use `gyoku` in branch names for 玉. Omit experiment labels from code comments; the branch name already conveys that context.
- Follow existing C++ conventions: file-local helper functions use anonymous namespaces (as in `usi.cc` and `notations.cc`). The opening helper is `GetOpeningMove`; its log label is `Shin-Yonenaga-Gyoku`.

## Next Experiment: Keep the Gyoku on the Right

Intent: accept a modest evaluation tradeoff to continue the opening's right-side plan, while allowing retreat under pressure and free king movement in the endgame. The first evaluation version is implemented on `experiment/gyoku-right-preference`; its effect in play remains to be reviewed.

1. Establish a baseline with `OwnBook=false` using the existing option; retain the book feature. Runtime data are now present; restart the GUI engine after the probability-file copy. Save games/positions where the king returns toward the center, noting side, depth/time, and principal variation.
2. Keep `main` as the fixed-opening baseline until comparison is satisfactory. The experiment branch is `experiment/gyoku-right-preference`.
3. The first version applies a flat 25 cp opening penalty outside files 1–4 for Black or 6–9 for White, including file 5. Existing progress interpolation fades it to zero by the middle-game point. Revisit the amount and fade after behavior review.
4. With books off and identical data/search settings, compare baseline and modified builds on saved positions at several depths. Check both sides, opening continuity, necessary retreats under attack, endgame freedom, and evaluation consistency when making/unmaking moves. Use focused manual checks first; do not reintroduce a general test framework.
5. Play comparison games and review losses as well as whether the intended style persists. Adjust the penalty/fade and merge only after review; playing strength alone is not the objective.
6. Later, collect promising continuations for a dedicated 新米長玉 book. Verify position matching, legal moves, both sides, and fallback to search; compare book-on/off games for tactical weaknesses and plan continuity before adoption. The book remains a future experiment, not yet selected or implemented.

Startup-message and data-path improvements remain secondary to this experiment.

## Notes For Future Codex Sessions

Conversation history is not reliable persistent memory. Follow `AGENTS.md`, then read this file, `README.md`, `Makefile`, and `git status` first when resuming work.
