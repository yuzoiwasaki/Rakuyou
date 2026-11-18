# Rakuyou resume map

Updated 2026-11-18.

- PR2 merged at main960a2bc. Active experiment/white-king62 now trials early P84/P85 before P64, inducing B77 before Black N77. User approved shape and requests no fixed P94. Trial book updated to47 rows (22 overlay entries), native tests9 pass; production book/C++ untouched. Short depth12 preflight maintains K62/R81 but S63 is not guaranteed (one G63). Updated trial White10 completed4W4L2caps, no errors. All ten achieved P85/B77 then S63/N73/R81 and K62 through32; cap6 repeats positions, cap10 White+4772 (not a win). Next review actual game1/game3 at results/white-king62/p85-batch-review.html; no further edits yet. See docs/experiments/white-king62.md and results/white-king62/early-p85-review.html. No PR/adoption yet.
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

- User prefers game3 shape and proposes G32+G72. Depth24 with P94 deferred: White28 G32 -157/G52 -164; after G32/S67/S63/K28, White32 G72 -224 vs G52 -164. Candidate reaches requested shape but PV later K52. See results/white-king62/gold32-review.html (right G32+G72, White top). No trial-book changes pending review.

- Latest: user wants N33/B13 instead of P24 from G32/G72 shape. P33 still blocks knight: must prepare P34. Depth24 legal comparison B13 first -186/P24 -254/P34 -272. B13 PV then P44/P34/N33 retains K62 and both golds; P34 first allows bishop exchange. Normal-side reply includes S47 and edge attack, so not forced. Board results/white-king62/knight33-review.html, right B13-first. No book edits.

- Latest steering: B13-first edge attack is not simply safe (prepared P15 leads bishop-for-lance compensation); immediate N65 allows B95 check. User now proposes P44 first to block bishop exchange, then P34/N33. Common depth23: P44 -192/P24 -212/P34 -265. Black replies P55; White PV captures and advances G43, postponing knight. Board results/white-king62/pawn44-review.html, right P44-first. Attack vision G43/P35/Bx35/G34/R41 retained as conditional plan; do not ignore Black P75. No book edits during these diagnostics.

- Latest local question: pawn44 PV49 Sx53+ recapture. Limited common depth21 (24 target/20s): Gx53 -119 vs Kx53 -436; Kx53 allows P*66/P65 and PV later K42. Both full PVs native legal. Results silver53-recapture-analysis.json. No code/book changes.
