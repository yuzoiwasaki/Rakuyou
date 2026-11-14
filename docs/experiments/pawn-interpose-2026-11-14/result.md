# P*5d interposition after48 R5b — 2026-11-14

User proposes49 P*5d; if S6e5d, the rook's fifth-file ray is blocked and Black can take N3c with the dragon. Native replay confirms P*5d/Sx5d/Rx3c legal. It is a pawn DROP from hand. This is the selected G7h/S5g PV position, not an actual game continuation. After Sx5d, White Bishop2b still attacks3c: direct Rx3c can be met by Bx3c/Bx3c+, giving White a rook. No claim that blocking the rook makes3c unopposed.

## Bounded searches

Same unchanged binary, rank0/support10/D10/ShinON/bookOFF/thread1/hash64. Fixed depth12, MultiPV2, no USI time limit,90s watchdog. Three planned diagnostics plus one targeted comparison because direct Rx3c did not appear among unrestricted top2 after Sx5d. No repeats/tuning or installation. All four finished normally (~5–8s each);96 reported PVs and best moves native legal; frozen bindings unchanged.

1. After48, restricted RxR5b versus P*5d: Black−98 /−173. P*5d line begins P*5d/P*5f/S6h/Sx5d/Bx3c+/Bx3c/Rx3c. The75cp gap is a bounded estimate, not rejection of the plan or an approved tolerance.
2. After49 P*5d, unrestricted White replies: P*5f +265, Sx5d +234 (White view). The opponent can first attack S5g with P*5f before taking the dropped pawn. These scores are from a different search root; do not subtract them from case1 to claim a change in move quality.
3. After50 Sx5d, unrestricted Black: Bx3c+−174, RxR5b−392. Direct Rx3c not top2, so its quality was not yet measured.
4. Same after50 root, restricted direct Rx3c versus Bx3c+: Black−333 /−47. B-first line Bx3c+/Bx3c/Rx3c exchanges bishops while retaining the dragon; direct Rx3c/Bx3c/Bx3c+ gives up the dragon for bishop and knight. The bishop-first continuation still includes enemy B*5e, so it is not a forced win or safe-material proof. Different restricted/unrestricted scores illustrate search dependence; use only within-search comparisons.

The interposition idea is meaningful: it changes the fifth-file geometry after Sx5d. The concrete sequence benefits from considering a bishop-first capture, and the opponent's P*5f before capturing prevents treating the user's sequence as forced. No evaluation change follows.

[Viewer](../../../results/teatsui-pawn-interpose-2026-11-14/review.html) contains three comparisons: move49 choices, captures after Sx5d, and White's replies to the drop.94 displayed states exactly match native replay. Side-to-move score labeling switches for White's reply comparison. `summary.json` retains all four searches' final rows/history; full local plans/logs under ignored results. User review pending.
