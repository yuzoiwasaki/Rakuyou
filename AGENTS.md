# AGENTS.md

Rakuyou is a personal experimental fork of Gikou 2.

- Read `MEMORY.md`, `README.md`, `Makefile`, and `git status` before work.
- Before implementation, explain the change and ask the user whether to commit directly to `main` or use a task branch and PR. Minor changes may go directly to `main` with the user's approval.
- New features and evaluation changes normally use task branches (`feature/`, `fix/`, `experiment/`, or `chore/`) and PRs. Develop alongside stable `main`; merge only after validation, review, discussion and explicit user approval. Do not merge automatically after implementation.
- Keep `main` limited to adopted code, maintained tools/tests and concise documentation. Leave rejected experiments on their branches.
- Keep generated games, binaries and logs in ignored directories. Do not add dated experiment reports or one-off runners to `main`.
- Preserve upstream copyright headers. Use repository-relative paths in tracked files.
- Keep README short and human-facing. Put configuration and build details in `docs/development.md`.
- Update the short resume map in `MEMORY.md` after meaningful work; detailed experimental history belongs on experiment branches.
- Prefer small changes with relevant verification. Review concrete style defects, not every loss; skip ambiguous cases.

See `docs/development.md` for builds, tests and branch workflow.
