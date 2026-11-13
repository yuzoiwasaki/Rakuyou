# Diagnosis of the rejected S3f choice — 2026-11-13

User prefers S4d liquidation over S3f in the accepted central-rank position. Thickness and rank should be converted into attack at the right moment, not preserved unconditionally. This is a durable style judgment, not an assumed tactical best-move label. Trial stays unadopted.

## Saved evidence

`inspect_saved.py` replays every prefix of every reported PV from both supported-root searches: 233 prefix occurrences, 97 distinct positions. Native full/incremental/unmake checks pass. Both correction flags are zero everywhere; static scores are identical with correction0/10. Thus no directly penalized position was found in the reported lines, including the S4d line. Unreported search branches remain unobserved. The predicate only concerns pawns on rank5; the main Black pawn here is already5d, so this is not a direct bonus for preserving that pawn.

## Bounded diagnostic searches

Exactly two fresh searches, same unchanged binary/support10/D10, correction0/10, restricted to S5e4d and S2g3f, MultiPV2, fixed depth13, no USI time limit,90s watchdog. Both finish in about8.3s. All52 reported PVs and best moves pass native legality replay. Bound inputs unchanged. No retries or tuning.

| Correction | S3f | S4d | Ranking |
|---|---|---|---|
| 0 | −117 | −335 | S3f first |
| 10 | −117 | −243 | S3f first |

Scores are Black-view cp at depth13. S3f has identical final PV in both settings. S4d final lines differ after S4d/Gx4d/P5c+/R3b/G4f/P*5e/R5i/S*5g: OFF P*6b, ON P*6h. This does not show direct improvement by92cp; changed search paths and evaluation functions prevent that inference.

The previous unrestricted time-limited result (OFF S4d vs ON S3f) is not reproduced as a ranking reversal under these diagnostic conditions. Both select S3f; S4d is not worse with the correction in this diagnostic. Restricted MultiPV changes search behavior, so this is not a disproof that the correction influenced the earlier run, nor an adjudication of the user's preferred S4d.

## Conclusion

No observed direct penalty explains rejection of S4d. Earlier claims that the correction discourages conversion of thickness were premature. Causal attribution to off-PV pruning/transpositions/branch changes is unresolved, not established. Do not add an attack bonus, force S4d, or narrow the geometric rule on this evidence. Preserve both user judgments (good counterplay, preferred central liquidation), unchanged coefficients and installed baseline. If deeper diagnosis is pursued, use an isolated instrumented search to identify affected off-PV nodes and their root candidates, retaining this untouched binary as reference; that instrumentation has not been done here.
