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
- 新米長玉 from `experiment/shin-yonenaga-gyoku` is integrated into `main` in `src/thinking.cc`: Black opens with `5i4h` (▲4八玉), White with `5a6b` (△6二玉), then uses the existing book/search behavior. It is enabled by default and can be disabled with the `ShinYonenagaGyoku` option on the current tool branch.
- Opening selection requires the standard initial position or one move from it in the supplied history. Standalone intermediate SFEN positions do not trigger White’s opening. Legal root moves and USI restrictions are respected; infinite/ponder wait for stop/ponderhit.
- Initial verification passed 13 USI checks. The smoke-test script was removed at the user’s request; use manual USI or GUI checks for now. Ignored build artifacts survive branch switches, so rebuild after switching.
- Merge verification: release build succeeded; manual USI checks confirmed ▲4八玉, △6二玉 after either ▲7六歩 or ▲2六歩, and subsequent normal search.
- The right-side king preference from `experiment/gyoku-right-preference` is integrated into `main`. It applies a 25 cp opening penalty when Black's king is outside files 1–4 or White's is outside files 6–9, fading to zero by the middle-game progress point. It is a separate `EvalDetail` term in both full and incremental evaluation; no move is forbidden.
- Release and development builds passed. A temporary local probe checked both colors, retreat and unmake, and zero preference from middle-game progress onward. Development search to depth 3 passed its full-versus-incremental evaluation assertions. Playing behavior and strength have not yet been compared under controlled conditions.
- `tool/paired-selfplay` contains the first small paired-match runner in `tools/paired_selfplay.py`. It runs 新米長玉 against normal Rakuyou twice with colors swapped, disables ponder, and records settings, result, USI moves, move source, score, and PV as JSON. Normal Rakuyou always uses its book; 新米長玉 book use is the tested variable (`--shin-book off|on`). Its initial rule handling recognizes engine resignation/declaration and a maximum-ply draw; strict repetition and other adjudication remain future work.
- Depth-1 smoke runs completed both color-swapped games with books off and on. Only the 新米長玉 player used the forced opening; with books enabled, the output also identified actual book moves. The recorded move-source field supports longer runs and future dedicated-book tests.
- The same branch adds a `ShinYonenagaGyoku` USI check option, enabled by default. Turning it off disables both the forced opening move and the 25 cp right-side king preference for that engine process, allowing the current binary to act as the normal opponent in paired games. Release build passed; direct USI checks produced `5i4h` when enabled and a searched move when disabled, and an evaluation probe confirmed a 24 cp rounded difference in an early retreat position.
- The runner now accepts `--pairs`, saves atomically after every completed game, aggregates W/L/D, score rate, color splits, average plies, result reasons, and move sources, and displays elapsed time plus ETA. `--resume` continues from the saved settings/results and can increase the requested pair count. A 2-pair run followed by resume to 3 pairs verified ordering, aggregation, and checkpoint replacement.
- Local timing with one thread and 128 MB hash per engine: one pair took about 1.3 s at depth 5, 5.8 s at depth 10, and 236 s at depth 15 (roughly 3 h 20 min for 50 depth-15 pairs on this Mac). These were timing samples only; each two-game sample split 1-1 and says nothing about strength.

## Direction

Work in small steps. Prefer low-risk, observable changes before large strength improvements.

- Keep the README minimal and shared build instructions concise in `docs/development.md`; keep branch-specific handoff notes in `MEMORY.md`.
- Develop the 新米長玉 concept further. A brief README description may be added later; leave the current overview unchanged for now.
- Use `gyoku` in branch names for 玉. Omit experiment labels from code comments; the branch name already conveys that context.
- Follow existing C++ conventions: file-local helper functions use anonymous namespaces (as in `usi.cc` and `notations.cc`). The opening helper is `GetOpeningMove`; its log label is `Shin-Yonenaga-Gyoku`.

## Next Checks: Right-Side King Preference

Intent: accept a modest evaluation tradeoff to continue the opening's right-side plan, while allowing retreat under pressure and free king movement in the endgame. A brief GUI trial suggested the king no longer returned left in the previously observed line; strength and wider behavior remain unmeasured.

1. Retain `OwnBook=false` as an option; runtime data are now present locally. Save games/positions where the king returns toward the center, noting side, depth/time, and principal variation.
2. With books off and identical data/search settings, compare `d9f5710` (fixed-opening baseline) and current `main` on saved positions at several depths. Check both sides, opening continuity, necessary retreats under attack, and endgame freedom. Revisit the 25 cp amount and fade if behavior warrants it.
3. Use the paired self-play tool for 新米長玉 versus book-enabled normal Rakuyou, swapping colors while keeping other conditions equal. Run 新米長玉 with its book off and on as separate comparison conditions, and review losses as well as whether the intended style persists. Playing strength alone is not the objective.
4. Eventually, collect promising continuations for a dedicated 新米長玉 book. Verify position matching, legal moves, both sides, and fallback to search before adoption. The book remains a future experiment, not yet selected or implemented.

Startup-message and data-path improvements remain secondary to this experiment.

## Notes For Future Codex Sessions

Conversation history is not reliable persistent memory. Follow `AGENTS.md`, then read this file, `README.md`, `Makefile`, and `git status` first when resuming work.
