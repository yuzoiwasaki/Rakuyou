# Root-branch tracing of rank commitment — 2026-11-13

Isolated instrumentation only; evaluation coefficient and predicate unchanged. Copied trial source, added root-move/depth scope to search and logging at RankCommitmentScore. OFF also computes the predicate for observation but still returns zero. Trace records qualifying evaluation calls, including evaluations used in incremental parent/child differences, not unique visited nodes or backed-up root-score contributions. Root context persists through recursive and quiescence calls; no complete move path or null-move marker is recorded. Position legality checks below do not prove legal reachability of a search path.

Exactly two searches: same restricted S4d/S3f, MultiPV2, fixed depth13 as prior diagnosis. No time limit;90s watchdog. Instrumented and original binaries match EVERY reported info field except timing/NPS/raw text, including scores, PVs, depths, nodes and hashfull; same best move. All52 reported PVs/best moves passed legal replay. Both finish about8.5s. The 20,000-event limit was never reached. Original source/runtime and frozen inputs unchanged.

## Qualifying calls by root branch

| Correction | Root candidate | Black flagged | White flagged | Unique positions in group |
|---|---|---:|---:|---:|
| 0 (observation only) | S4d | 0 | 4494 | 1706 |
| 0 (observation only) | S3f | 9 | 226 | 3 Black +84 White |
| 10 | S4d | 0 | 5268 | 1978 |
| 10 | S3f | 9 | 238 | 3 Black +90 White |

All2425 distinct qualifying SFENs across both runs were checked with the ORIGINAL native probe; flags match exactly and probe invariants pass. Group/event counts are not causal importance or total penalty sums.

In the S4d branch every qualifying static position penalizes WHITE, favoring Black directly. No direct penalty against Black's S4d attacking plan was observed in this bounded search. One early example has a White pawn5e supported by Gold5d and attacked by Black Rook5f/Silver4d. This is an opponent support-deficit pattern, not punishment for Black abandoning territory. In the S3f branch three distinct Black-flagged positions also occur; these are not a penalty on S4d.

The root outcome remains exactly as the prior diagnostic: S3f−117 both; S4d−335 OFF/−243 ON with different PVs. This does not imply a causal92cp improvement: move ordering, pruning and transpositions propagate small score changes nonlinearly.

## Conclusion and scope

The proposed explanation “the trial directly penalizes S4d liquidation and therefore preserves thickness unnecessarily” is unsupported by the observed branches. No evidence-based predicate narrowing is justified yet. The user's preference for S4d remains an important attack-timing example; it is not overwritten by this engine result.

This traces the restricted fixed-depth diagnostic, NOT the earlier unrestricted 10-second search. Historical root-choice divergence is still not fully attributed, and no branch-level ablation or backed-up-score causal analysis was performed. Do not claim that the correction has no indirect influence or is safe to adopt. Keep the trial unadopted and avoid tuning it to force one root move.

If continuing positional diagnosis, inspect the engine's concrete defenses after S4d/Gx4d/P5c+ (R3b then P*5e/S*5g in the saved diagnostic), alongside the user-approved counterplay example, before deciding whether a general evaluation change is needed. Saved traces, plan, build, parity and native checks accompany this report; no long matches or operational installation.
