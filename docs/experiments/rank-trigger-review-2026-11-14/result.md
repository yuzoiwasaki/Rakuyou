# Where the rank predicate triggers — 2026-11-14

Final user static-rook verdict: LEFT/rank0 somewhat more natural, although imperfect. RIGHT/rank10 has awkward major-piece excursions and S*7e. Across four pairs: White/third favors rank10; Black/central and White/fourth roughly equal with issues on both sides; Black/static favors rank0 slightly. Trial remains unadopted. User authorized comparing the trigger patterns before considering narrower conditions.

## Scope and verification

No engine searches, coefficient changes or operational updates. Original native probe evaluates1247 actual saved states across all8 games with rank0/10. This is a counterfactual static diagnostic at support10/D10/ShinON, not re-evaluation using each normal opponent's actual options. Predicate geometry itself is color-symmetric and independent of that setting. Rank0 game flags mean where the predicate WOULD trigger, not an actual penalty applied in those games.

For the good White/third pair07/08 and problematic Black/static pair03/04, inspect all136 saved candidate-side PVs from moves13–80 and their1756 distinct prefix positions. Every full PV is native-legal. Opponent PVs, deeper unreported branches and later game phases are outside this saved-PV comparison. A separate annotation-only native probe reports the first triggering pawn, participants and counts. Its ordinary output exactly matches the original probe on all29 distinct active positions from both scans. A first witness is not an enumeration of all eligible pawns in a position. Match input bindings remain unchanged.

## Actual game positions

| Game | Setting / candidate | Trigger plies | Flagged side |
|---|---|---|---|
| 01 | rank0 / Black central | none | — |
| 02 | rank10 / Black central |55,56| Black |
| 03 | rank10 / Black static |none| — |
| 04 | rank0 / Black static |none| — |
| 05 | rank0 / White fourth |118–121| White (counterfactual) |
| 06 | rank10 / White fourth |none| — |
| 07 | rank10 / White third |42| White |
| 08 | rank0 / White third |68,69| Black opponent (counterfactual) |

No observed static penalty explains the awkward S*7e or rook movements in03. This does NOT prove the term was irrelevant: scores in unreported alternatives can affect move ordering, pruning and transpositions, and finite-time runs differ.

## Good versus awkward examples

Good07 after42 P6d6e: White pawn6e, defender Silver5d (1), enemy Rook6h and Silver7f (2). This triggers a6cp White static penalty after taper/rounding. Actual continuation43 S7f6e 44 S5d6e 45 R6h6e 46 S*7f is the active counterplay the user liked. A temporary attacking/exchange position satisfies exactly the predicate advertised as unsustainable rank support. The same witness appears in saved PVs from roots31/33; root41's first PV move also reaches the actual position.

Awkward03: no actual-position hits. In34 saved candidate PVs only one prefix triggers,14 added plies after root62 (so later than the played55 S*7e). It flags WHITE pawn4e supported by Silver3d (1), attacked by Black Rook4i/Knight3g (2). The direct static effect favors Black; it is not a direct penalty on Black's silver drop or a reward for the drop. Root62 timing does not exclude earlier unreported branches, but this observed PV provides no causal explanation for55 S*7e.

Thus the observed examples share the same simple geometry (rook plus small piece versus one silver). They cannot be separated using these counts alone. Good07's measured penalty also shows the predicate is not specific to a passive attempt to maintain territory: it catches transient attacking positions. This is a specificity concern, not proof that removing that hit would improve the engine.

Other saved PV counts:03 has1 active prefix occurrence,04 has0,07 has3,08 has21. These counts are not causal importance, affected-node percentages or strength evidence.

## Decision

Do not narrow coefficients, add move-specific bonuses, or claim a validated improvement. There is no evidence-based threshold separating the liked and disliked games in this record. Keep the prototype unadopted and the support10/D10 operational baseline unchanged.

A possible design question for future work is whether the local exchange leaves an enduring defensive burden, versus a temporary imbalance during viable counterplay. That would require a separate definition and contrasting fixtures including07's exchange sequence, the original forced-support example and the user's central attack timing cases. It is not implemented or established by this static scan. Further off-PV causal tracing could examine specific early decisions, but is also not performed here; don't reopen previously closed tactical branches automatically.

Reproduction/evidence: `summary.json`, `witnesses.json`, `input-hashes.json`, and scripts here. Full scans/build artifacts remain local under `results/teatsui-rank-trigger-review-2026-11-14/`. Probe source is archived with diagnostic fields only; it uses the unchanged trial header/source snapshot for compilation. The installed engine is untouched.
