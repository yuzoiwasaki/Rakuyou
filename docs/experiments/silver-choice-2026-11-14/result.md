# Silver choices after P4e — 2026-11-14

User prefers the G7h line and suggests withdrawing/advancing a silver rather than capturing P4e. This diagnostic continues the selected G7h PV through46 P4e: a hypothetical continuation, not an actual played position or forced line. Black has silvers3f/4f. Native replay verifies all8 legal moves across these two silvers; 3f4g and4f3g are illegal because own pawns occupy the destination squares. No omitted legal promotion variant applies here.

## Completed comparison

Same binary, rank0/support10/D10/ShinON, thread1/hash64/bookOFF. All8 candidates together, MultiPV8.

| Candidate | Source | Depth11 Black score |
|---|---|---:|
| S5g | 4f | −246 |
| S5e | 4f | −437 |
| Sx4e | 3f | −509 |
| Sx4e | 4f | −509 |
| S3e | 4f | −1139 |
| S2g | 3f | −1164 |
| S3e | 3f | −1164 |
| S2e | 3f | −1838 |

S5g line starts S5g/R5b/Rx5b/Gx5b/R*2a/B1c/S6h/R*5h. A retreat can be combined with rook-exchange counterplay; it is not passive abandonment. S5e is the second-ranked alternative. Both captures meet Nx4e in the saved PV. This is one bounded search, not proof that S5g is best overall, that all opponent replies are covered, or that the earlier G7h choice is superior. All listed scores favor White; keep the user's positional preference separate from an absolute winning claim.

## Interrupted MultiPV issue and follow-up

The first fresh10s/depth15cap search stopped during depth11. The engine emits a full MultiPV set even when `limit_reached` interrupts the candidate loop (`search.cc` IterativeDeepening), so matching depth labels alone do not guarantee all candidates completed that depth. Two lower candidates were printed as `mate -2`, alongside older PVs; they must not be treated as proven mates or as cp−2. The interrupted output is preserved in `results/teatsui-silver-choice-2026-11-14/`; its summary is explicitly diagnostic-only, not the comparison table.

One justified additional fresh search used fixed depth11 with no USI time limit (90s external watchdog), otherwise identical settings. It completed in11.3s, with eight ordinary cp rows and no interruption, selecting S5g. The table/viewer use only this run. No coefficient, candidate or root changes; no repeated tuning. Future equal-depth MultiPV reports must distinguish completed iterations from time-limit output; previous timed estimates remain bounded observations, not proof of completed candidate coverage.

Both searches'88 reported PVs each and best moves passed native replay (176 total); even a legal PV does not validate an interrupted score/mate claim. Frozen bindings unchanged. No engine changes or installation.

[Viewer](../../../results/teatsui-silver-choice-fixed-2026-11-14/review.html): left prior Sx4e from3f, right selectable alternative; both Black/bottom. Default right S5g from4f, second option S5e from4f. All201 displayed states matched to native replay. `summary.json` preserves all completed rows and root history. User review pending; no further searches scheduled.
