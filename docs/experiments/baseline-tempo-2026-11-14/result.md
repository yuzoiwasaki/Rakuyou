# Baseline central-counterplay timing diagnostic

User judges the initial counterplay natural, with attack speed reversing later. Preserve that assessment separately from engine scores. Adopted support10/D10 remains unchanged.

## Conditions and validation

Game3 of baseline-review4: actual histories after45 and55. Fresh engine for each search, ShinON/support10/D10, Hash64, Threads1, OwnBook/Ponder OFF, all RAKUYOU environment variables removed. Two initial10s/depth15cap MultiPV2 searches: after45 unrestricted; after55 restricted to L*5g and S6ex5d. Timed after45 output ends with a mate−2 second line at reported depth12; this is not evidence of a forced mate. Timed after55 depth13 repeats depth12 lines near cutoff. Therefore run exactly two separate fixed-depth11 checks to complete both candidates. No silent retries, tuning or long games.

Four searches total,94 emitted PVs legally replayed by native referee. Fixed checks completed in5.3s and7.8s. Original240 match input bindings intact; diagnostic hashes/options/commands checked. Viewer53 states match native replay. Raw local plans/transcripts are in results/teatsui-baseline-tempo[-fixed11]-2026-11-14. Runner imports parsing/replay helpers from an older local experiment; local artifacts are required to reproduce, not a standalone distribution.

## Completed depth11 result (White perspective)

| Root | Candidate | cp |
|---|---|---:|
| after45, all legal moves |46 S6e (played)|−239|
| after45, all legal moves |46 S4c|−765|
| after55, two restricted candidates |56 L*5g (played)|−477|
| after55, two restricted candidates |56 S6ex5d|−336|

At46 the engine still prefers the played S6e. This supports keeping central counterplay as a viable plan to investigate, not proving equality or a favorable position. Its PV follows P*5d with S7f, whereas the game chose48 P9d. That earlier branch is a candidate for the next direct comparison; its superiority is not established here.

At56 immediate Sx5d scores141cp higher. PV begins S6ex5d/S5ex5d/S6cx5d/P*9c/L*5e: silver exchange first, then use the lance. Played L*5g meets L*5h, followed by silver exchanges. The difference supports investigating move order and where the lance is used, but neither line restores equality in this search. These shallow diagnostics do not establish a unique losing move or a coefficient defect. Timed depth12/13 shows only64cp separation, indicating uncertainty in the size of the difference.

[Candidate viewer](../../../results/teatsui-baseline-tempo-fixed11-2026-11-14/review.html): both WHITE/TOP. Default56, LEFT played L*5g, RIGHT S6ex5d. Predicted lines, not actual games or forced sequences. Dropdown46 shows unrestricted top two moves. Next useful bounded check, after user review: actual after47, P9d versus S7f; keep evaluation unchanged.
