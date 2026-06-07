# AGENTS.md

## Project Context

Rakuyou is a personal experimental fork of Gikou 2.

## Working Rules

- Read `MEMORY.md`, `README.md`, `Makefile`, and `git status` before resuming work.
- Prefer small, low-risk, observable changes before larger strength or architecture changes.
- Preserve upstream copyright headers unless there is a clear reason to change them.
- Keep `MEMORY.md` updated with current state and next steps after meaningful work.
- Treat `MEMORY.md` as the resume map, not as a detailed changelog.

## Build Notes

- On Apple Silicon, the intended flow is `make libomp-x86_64`, then `make release`.
- Gikou depends on SSE 4.2, so Apple Silicon builds target x86_64 via Rosetta.
- Current known issue: `make release` needs `omp.h` under `lib/libomp-x86_64/include`.
