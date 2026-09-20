# Rakuyou Development Notes

This repository is a personal experimental fork of Gikou 2.

## Current State

- The codebase is mostly the cloned Gikou 2 source.
- `README.md` has been changed to describe Rakuyou as a personal experiment.
- `Makefile` has been adjusted for Apple Silicon Mac by building the SSE 4.2 engine as x86_64 via Rosetta.
- The USI engine name has been changed from `Gikou 2 (v2.0.2)` to `Rakuyou` in `src/usi.cc`.
- The Rakuyou USI author string in `src/usi.cc` has been changed to `Yuzo Iwasaki, based on Gikou by Yosuke Demura`.
- `AGENTS.md` has been added for durable Codex working rules; this file remains the resume map.
- A short Apple Silicon build note, adapted from upstream PR #10’s README addition, is in `docs/development.md`, linked from the minimal README. Keep this document limited to that concise scope.
- The Apple Silicon OpenMP setup and release build have succeeded on this machine. The previous missing `omp.h` issue is resolved locally.
- `bin/params.bin`, `bin/progress.bin`, and `bin/book.bin` are now present; `probability.bin` was still missing at the last startup check.
- The opening experiment lives on `experiment/shin-yonenaga-gyoku`. Its implementation and smoke test are not on `main`. Ignored build artifacts survive branch switches; the existing `bin/release` was built on that experiment branch.

## Direction

Work in small steps. Prefer low-risk, observable changes before large strength improvements.

- Keep the README minimal and shared build instructions concise in `docs/development.md`; keep branch-specific handoff notes in `MEMORY.md`.
- Use `gyoku` in branch names for 玉, and `experiment` rather than 「実験」 as a code-comment label.

Near-term ideas:

1. Finish runtime setup and confirm GUI registration.
   - Check the existing Gikou 2 installation for `probability.bin`.
   - Register `bin/release` through Shogidokoro Mac's engine management dialog.
2. Improve user-facing startup behavior.
   - Make missing `params.bin`, `progress.bin`, and `book.bin` messages clearer.
   - Consider USI options for evaluation/progress/book file paths.
3. Add lightweight verification tools.
   - USI smoke test.
   - Fixed-position search benchmark.
   - Legal move / perft-style checks.

## Notes For Future Codex Sessions

Conversation history is not reliable persistent memory. Follow `AGENTS.md`, then read this file, `README.md`, `Makefile`, and `git status` first when resuming work.
