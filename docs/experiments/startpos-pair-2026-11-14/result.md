# Initial-position pair: completed screening

User completed two games. Adopted ShinON/support10/D10 lost as Black and White versus fixed normal Rakuyou ShinOFF/support0/D0. Both books OFF; native first-move rule retained. Two games do not establish strength, color effects, or the cause of losses. Preserve the adopted evaluation and skip ambiguous failures.

Read-only audit passed:240 frozen bindings,337 go commands comprising335 timed searches and2 native opening moves, both full legal histories and results, options/environment/position/bestmove correspondence. Maximum search wall time9929ms and reported time9925ms. Game1 ends after160 board moves with Black resigning on161; game2 after175 board moves with White resigning on176. Native terminal positions remain ongoing, as expected for engine resignation. No errors or unrun games. No new searches.

## Lightweight opening screen

Game1 (adopted Black): angle exchange10 Bx7g+, then later19 B*3f/Bx3f/Sx3f. Black23 R8h,25 S6f,27 K2h,31 G3h builds a coherent setup before later maneuvering and attack. Own saved pre-move search scores25 and29 are0cp;43 −127,49 −203,59 −381. No obvious opening defect established; do not turn gradual score drift into exhaustive losing-move analysis.

Game2 (adopted White):2 K6b allows immediate pawn exchange3 P2e/4 P3d/5 P2d/Px2d/Rx2d, followed by G3b and later P*2c. White score4 −360cp later reaches32 −4cp. Thus do not attribute the eventual loss to the early pawn exchange alone. These are saved searches with different positions/depths, not proof of equality or a causal reversal.

One visual candidate: after35 P*7e, White36 Sx7e/37 P*7d/38 P8f/39 Px8f/40 Sx8f/41 P7c+/42 Kx7c. The knight is lost and the king leaves its starting route before castling. However43 P*8e/44 Sx7g+/45 Nx7g trades the silver for a bishop, and46 B*8h/47 G7h/48 Bx9i+ obtains the lance. This is an active material/king-safety tradeoff, not an established blunder. Own saved score42 −71cp then44 −445cp reflects changing searches; no single-move causal claim. Ask whether the early commitment is stylistically acceptable; skip if ambiguous. No new candidate searches or tuning authorized by this screen.

[Actual-game viewer](../../../results/teatsui-startpos-pair-2026-11-14/review.html): all337 displayed states native-matched. Default game2, both WHITE/TOP, same game left35/right42; advance48/58 for compensation. Dropdown game1 switches BOTH to BLACK/BOTTOM, left30/right43. These are actual moves at different times, not evaluation ablations or predicted lines.
