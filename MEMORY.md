# Rakuyou resume map

Updated 2026-11-17.

- PR2 merged at main960a2bc. Active branch experiment/white-king62 studies White vs fourth rook: retain S72, prefer P64/S63 then G72/P74/N73/R81 with king62. Initial PV reaches requested setup; early P65 needs separate defense and may lead to K71. No engine/book change yet. See docs/experiments/white-king62.md; local board results/white-king62/review.html awaits user review.
- Operational book: `books/shin-yonenaga-book-v1.txt`, generated from `books/shin-yonenaga-book.json` by `tools/books/build_operational_shin_book.py`.26 reviewed positions (Black15/White11); identical position/move rows to the tested candidate. Black starts with S68 and includes exact-position P46/S38-to47 and developed bogin gold/king plans. White entries unchanged.
- BookMaxPly default32 enables the later entries. Existing GUI settings may retain20 or an old trial file path; see books/README.md. No GUI configuration was changed automatically.
- Adopted engine remains ShinON/support10/D10. Release hides fixed style options; stale style setoption values are ignored. OwnBook/ShinBookFile remain editable.
- `make release`: optimized fixed style. `make match`: optimized configurable comparison engine. `make development`: debug checks, much slower; do not use for long batches. Evaluation and search are unchanged by PR2.
- Maintained book tests are consolidated into test/books/test_operational_shin_book.py. Experiment runners, duplicate books/sources and historical-only tests were removed from this PR's final tree.
- Final validation: release/match rebuilt; all17 maintained Python tests pass with no skips.26 book rows match the tested candidate exactly, reproduction check passes, and bin/ book matches the committed book.
- Full pre-integration opening history is saved at `archive/early-silver68-before-integration-2026-11-17` (`99e4859`). Ignored results/ remain local; replay old runners from the archived revision with their original inputs.
- Search experiment PR3 was closed without adoption. Its branch `experiment/root-candidate-recheck` is preserved; do not mix that search patch into PR2.
- Before new implementation, consult the user about direct main versus branch/PR. Minor changes can go directly to main only with approval. User reviews and explicitly approves merges. Keep main limited to adopted code, necessary tools/tests and concise docs.
- User runs long matches. Short bounded diagnostics are fine. Review clear style defects; skip ambiguous losses and do not tune to every lost game.
- Aim: thick, coherent shogi; support sustainable territory, permit counterplay and turn thickness into attack. No blanket requirement to preserve territory or avoid king recastling.
- README keeps2–3 major dated milestones. Omit minor items or move history to a separate file if needed.
- Public README text should stand alone for new readers, without references to the current review or trial. Remove Draft when submitting a finished PR for review; the user performs the merge.
- Earlier repository cleanup is archived at `archive/pre-adoption-cleanup-2026-11-15` (`f488a64`). See docs/development.md for builds, checks and recovery.
