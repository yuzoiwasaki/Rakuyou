# Rakuyou Development Notes

This repository is a personal experimental fork of Gikou 2.

## Current State

- The codebase is mostly the cloned Gikou 2 source.
- `README.md` has been changed to describe Rakuyou as a personal experiment.
- `Makefile` has been adjusted for Apple Silicon Mac by building the SSE 4.2 engine as x86_64 via Rosetta.
- The USI engine name has been changed from `Gikou 2 (v2.0.2)` to `Rakuyou` in `src/usi.cc`.
- The Rakuyou USI author string in `src/usi.cc` has been changed to `Yuzo Iwasaki, based on Gikou by Yosuke Demura`.

## Direction

Work in small steps. Prefer low-risk, observable changes before large strength improvements.

Near-term ideas:

1. Finish and document the Apple Silicon build flow.
   - Expected flow: `make libomp-x86_64`, then `make release`.
   - Current build attempt failed because `omp.h` was not available under `lib/libomp-x86_64/include`.
2. Improve user-facing startup behavior.
   - Make missing `params.bin`, `progress.bin`, and `book.bin` messages clearer.
   - Consider USI options for evaluation/progress/book file paths.
3. Add lightweight verification tools.
   - USI smoke test.
   - Fixed-position search benchmark.
   - Legal move / perft-style checks.

## Notes For Future Codex Sessions

Conversation history is not reliable persistent memory. Read this file, `README.md`, `Makefile`, and `git status` first when resuming work.
