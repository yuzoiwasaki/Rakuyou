# Normal-side book ON: completed screening — 2026-11-15

Two completed losses for adopted ShinON/support10/D10 (Black and White), versus fixed normal Rakuyou with bookON. No errors, unresolved or unrun games. Do not pool earlier runs, infer strength from two games, or attribute a change to book use alone.

## Read-only audit

240 frozen bindings unchanged. All211 go commands verified against recorded positions/options/bestmoves:204 timed searches,5 normal book moves,2 adopted native opening moves. Both histories replay legally; both games end by resignation with ongoing native board states. Max wall9912ms / engine9908ms. Game1:98 actual board moves, resignation99; game2:111 board moves, resignation112. Native-matched211 displayed states. No new searches or evaluation changes.

Book usage: game1 normal White at2 P3d and4 S6b only; first search6. Game2 normal Black at1 P7f,3 R6h,5 K4h only; first search7. Both leave book well before the20-ply limit. Book scores are database metadata, not search scores. This trial exercised only brief opening-book prefixes, not sustained book-guided opposition.

## One visual candidate: game1 king-route change

Adopted Black begins1 K4h but later33 K5i,35 K6h,39 K7i,43 K8h. Native-verified settings remain ShinON/support10/D10 throughout. This is a coherent switch to a left-side king rather than a simple back-and-forth or proof of an option failure. The engine no longer chooses the intended Shin-Yonenaga king shape. User subsequently accepted this flexibility after the pieces have developed; no forced king-route change or evaluation patch follows.

Saved own search values before33/35/39/43 are+43/−6/+8/+12cp, and before53 Rx2d +255cp. Thus no evidence here that the king switch immediately lost the game. Do not deepen losing-move diagnosis merely because it ultimately lost. Initial screening of game2 (versus fourth rook, White later swings rook to2b and attacks2/1 files) establishes no clear correction target.

[Actual-game viewer](../../../results/teatsui-startpos-normal-book-2026-11-14/review.html): default game1, BOTH BLACK/BOTTOM, same-game left31/right43. Advance33/39/43 to inspect the king route, optional53 for subsequent play. Dropdown game2 changes BOTH to WHITE/TOP, left30/right46. Actual saved histories, not predicted lines or parameter comparisons.

Disposition (2026-11-15): user finds this recastling natural after the setup has developed. They would want correction if the engine switched back in the early opening. Preserve this distinction as a style requirement, not a blanket penalty for moving the king back or a hard ply threshold (none agreed). Close this case; keep support10/D10 unchanged. No further searches or evaluation edits.
