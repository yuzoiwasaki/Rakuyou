# Rakuyou resume map

Updated 2026-11-18.

- PR #4 (https://github.com/yuzoiwasaki/Rakuyou/pull/4), branch `experiment/white-king62`, integrates the approved White fourth-rook book update. User reviews and merges; do not merge automatically.
- Operational book: `books/shin-yonenaga-book-v1.txt`, generated from `books/shin-yonenaga-book.json` by `tools/books/build_operational_shin_book.py`.42 positions (Black15 unchanged, White27). White advances P84/P85 before P64 and uses reviewed S63/G72/N73/R81 and Px65 lines. Unregistered positions return to search.
- Fixed G32 adoption was rejected. White's 4a gold destination and P94 are not prescribed. King location and formation are not forced against arbitrary replies. Evaluation/search C++ is unchanged.
- BookMaxPly remains32; use OwnBook ON and the operational filename. Builds copy the book to bin/. Existing GUI settings may need manual adjustment; see books/README.md.
- Engine remains ShinON/support10/D10. Release hides fixed style options; stale style setoption values are ignored. OwnBook/ShinBookFile remain editable.
- `make release`: optimized fixed style. `make match`: optimized configurable comparison engine. `make development`: debug checks, much slower; do not use for long batches.
- Validation: release/match builds and all17 maintained Python tests pass with no skips; generator check passes and bin/ book matches the committed source.
- Book verification is consolidated in test/books/test_operational_shin_book.py. Experiment sources/books/tests/runners/reports were removed from the final PR tree.
- White trial history is preserved at `archive/white-king62-before-integration-2026-11-18` (`25ee593`). Ignored results/ remain local; use that revision and its frozen book copies to reproduce experiment runners.
- Earlier archives: `archive/early-silver68-before-integration-2026-11-17` (`99e4859`), `archive/pre-adoption-cleanup-2026-11-15` (`f488a64`). PR3 root-recheck experiment was closed without adoption; its branch remains preserved.
- User runs long matches. Short bounded diagnostics are fine. Review clear style defects and skip ambiguous losses; known/repeated starts and capped games do not prove strength improvement.
- Aim: thick, coherent shogi; support sustainable territory, permit counterplay and turn thickness into attack. No blanket requirement to preserve territory or avoid king recastling.
- Consult user about main versus branch/PR before new implementation. Minor changes may go directly to main with approval. Keep main limited to adopted code, maintained tools/tests and concise docs.
- Public README should stand alone and retain only2–3 major milestones. Remove Draft when presenting a finished PR; user reviews and merges.
