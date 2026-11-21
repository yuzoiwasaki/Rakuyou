# Rakuyou resume map

Updated 2026-11-21.

- Floating-rook integration prepared on experiment/bogin-bishop-transfer; do not merge automatically. User favors hineri formation and accepts modest evaluation disadvantage. Formal source/txt now67 positions (Black40/White27); book rules equal final tested candidate. Canonical source move orders repaired without changing SFEN/hand/turn/book moves; native uniqueness/legal/path consistency verified. BookMaxPly default44 includes late43B97; GUI saved20/32 needs44.
- Added conditional floating-rook entries, N77/P96/B97 and19S38 at S42/S72/B33. AfterS38 all replies return to search; no hard-coded floating/rightking classifier, kinglock, eval or search changes. Promotion when available retained; alternate defended23 floats. Existing bogin gold regrouping survives via transpositions; original White rules unchanged.
- Latest20: Black4W5L1cap,White0W9L1cap. S38 hit5Black/alllost but shared111plies; rightking K38/S47/N37/R29 achieved. No strength claim or pooling; no lateN77/B97 hits in startpos batches. Prior known-start shape review separate. User approves shape. Later111R49 vsS*52 (-673/-187 atd21) recorded as futuresearch issue; no fix included. Logs/diagrams results/s38-startpos20-review/.
- Full experiment sources preserved on archive/floating-rook-before-integration-2026-11-21 at3f6314b. Trial scripts/notes removed from integration tree; generated results/ remain local. Per-search shared-history halving rejected; no experimental C++ carried over. Reproduction needs archived sources and original frozen binaries/books/data; current bin/match rebuilt for default44.
- Validation: release/development/match builds pass; all18 maintained Python tests pass without skips; generator check and bin/ book copy match. Next push integration/archive and create ready PR; user reviews and merges. Long games are user-run.

- PR #4 (https://github.com/yuzoiwasaki/Rakuyou/pull/4), branch `experiment/white-king62`, was merged as main2bdf140 and integrates the approved White fourth-rook book update. User reviews and merges; do not merge automatically.
- Fixed G32 adoption was rejected. White's 4a gold destination and P94 are not prescribed. King location and formation are not forced against arbitrary replies. Evaluation/search C++ is unchanged.
- Engine remains ShinON/support10/D10. Release hides fixed style options; stale style setoption values are ignored. OwnBook/ShinBookFile remain editable.
- `make release`: optimized fixed style. `make match`: optimized configurable comparison engine. `make development`: debug checks, much slower; do not use for long batches.
- Book verification is consolidated in test/books/test_operational_shin_book.py. Experiment sources/books/tests/runners/reports were removed from the final PR tree.
- White trial history is preserved at `archive/white-king62-before-integration-2026-11-18` (`25ee593`). Ignored results/ remain local; use that revision and its frozen book copies to reproduce experiment runners.
- Earlier archives: `archive/early-silver68-before-integration-2026-11-17` (`99e4859`), `archive/pre-adoption-cleanup-2026-11-15` (`f488a64`). PR3 root-recheck experiment was closed without adoption; its branch remains preserved.
- User runs long matches. Short bounded diagnostics are fine. Review clear style defects and skip ambiguous losses; known/repeated starts and capped games do not prove strength improvement.
- Aim: thick, coherent shogi; support sustainable territory, permit counterplay and turn thickness into attack. No blanket requirement to preserve territory or avoid king recastling.
- Consult user about main versus branch/PR before new implementation. Minor changes may go directly to main with approval. Keep main limited to adopted code, maintained tools/tests and concise docs.
- Public README should stand alone and retain only2–3 major milestones. Remove Draft when presenting a finished PR; user reviews and merges.
