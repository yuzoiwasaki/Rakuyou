# Rakuyou Development Notes

This repository is a personal experimental fork of Gikou 2.

## Current State

- The codebase is mostly the cloned Gikou 2 source.
- `README.md` has been changed to describe Rakuyou as a personal experiment.
- `Makefile` has been adjusted for Apple Silicon Mac by building the SSE 4.2 engine as x86_64 via Rosetta.
- The USI engine name has been changed from `Gikou 2 (v2.0.2)` to `Rakuyou` in `src/usi.cc`.
- The Rakuyou USI author string in `src/usi.cc` has been changed to `Yuzo Iwasaki, based on Gikou by Yosuke Demura`.
- `AGENTS.md` has been added for durable Codex working rules; this file remains the resume map.

## Direction

Work in small steps. Prefer low-risk, observable changes before large strength improvements.

- Use `gyoku`, not `king`, in branch names for 玉. Omit experiment labels from code comments; the branch name already conveys that context.
- Keep branch-specific experiment notes in AI handoff files such as this one; do not add them to `README.md`.

## Active Experiment

- Branch: `experiment/shin-yonenaga-gyoku`, created from `main` for the requested 新米長玉 experiment.
- Implemented in `src/thinking.cc`: Black opens with `5i4h` (▲4八玉); White responds to any first move with `5a6b` (△6二玉). Later turns retain the existing book/search behavior. Always enabled on this branch, with no new USI option.
- Applies only to the standard initial position or one move from it, checked using position history. A standalone SFEN of an intermediate position does not trigger White's forced opening. Legal root moves and USI move restrictions are respected; infinite/ponder still wait for stop/ponderhit.
- Built x86_64 OpenMP via `make libomp-x86_64`; `make release -j4` now succeeds on this machine. Existing compiler warnings remain.
- Initial verification passed 13 USI checks. The smoke-test script was subsequently removed at the user's request to keep this experiment minimal; use manual USI or GUI checks for now.
- Evaluation/book data (`params.bin`, `progress.bin`, `book.bin`) are absent: verification covers behavior, not playing strength. Place these in the engine's working directory for actual games (`book.bin` is needed when using the book).
- Next: supply evaluation data and observe actual games. Further formation/search modifications are deferred per the user's request.

Near-term ideas:

1. Observe games using the experimental opening after supplying evaluation data.
   - Apple Silicon build flow is verified: `make libomp-x86_64`, then `make release`.
2. Improve user-facing startup behavior.
   - Make missing `params.bin`, `progress.bin`, and `book.bin` messages clearer.
   - Consider USI options for evaluation/progress/book file paths.

## Notes For Future Codex Sessions

Conversation history is not reliable persistent memory. Follow `AGENTS.md`, then read this file, `README.md`, `Makefile`, and `git status` first when resuming work.
