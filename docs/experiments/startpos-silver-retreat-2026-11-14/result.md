# Start-position game2: capture or retreat at move36

User concern: White king is thin; do not take P7e and allow obvious knight loss, prefer silver retreat. Compared actual35 P*7e position, White S7dx7e (played) and S7d6c (suggested). No evaluation change or long games.

One fresh restricted MultiPV2 search, completed fixed depth13, adopted ShinON/support10/D10, book/ponderOFF,1thread/Hash64, all RAKUYOU environment removed. Native referee validated both roots,26 emitted PVs and37 displayed states. Search7.083s wall/7.080s engine. Original240 match bindings and all diagnostic inputs unchanged; options and one go command checked. No retries or stop. Local runner reuses parsing/native replay helpers from an earlier local experiment; those ignored artifacts are prerequisites.

| Candidate | White-view cp, completed depth13 |
|---|---:|
| S7dx7e (played) | −48 |
| S7d6c (retreat) | −61 |

Only13cp apart. The engine still narrowly selects capture; this is not evidence that retreat is tactically refuted or significantly inferior. Limited-depth result, not equality proof or a statistical confidence bound. Earlier suggestion that pawn capture is over-rewarded is unproven; material/initiative and king safety cannot be causally isolated from this two-move search.

Retreat PV begins S6c/G7h/R8a/N3g/G5b/K4h/P1d/R2i/S5d/S7f/N3c/P9f/P4e. White retains the knight and king on6b through the displayed line, can develop the gold instead of immediately exposing the king. This does not show a completed castle or establish long-term safety.

Capture PV begins Sx7e/P*7d/P8f/P7c+/Kx7c/Px8f/Sx8f/B6h/S7e/G7i/P*8h. Black's bishop retreats in this new PV, unlike the actual game where it was exchanged; do not label this as actual continuation or guaranteed bishop compensation. This line still trades the knight and king exposure for active play on the8-file.

[Candidate viewer](../../../results/teatsui-startpos-silver-retreat-2026-11-14/review.html): both WHITE/TOP; LEFT played capture, RIGHT suggested retreat. All predicted continuations from the same35-ply root, not actual paired games. User preference for retreat can reasonably remain a style target given near-equal scores, but no ad-hoc retreat bonus or evaluation patch follows yet. Await user's view of the retreat continuation; avoid further exhaustive diagnosis unless a concrete concern emerges.
