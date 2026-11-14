# Four adopted-baseline games: completed review

All four games completed: support10/D10 2 wins, 2 losses. Black versus fourth/third rook won; White versus central/static rook lost. These are different fixed development starts, not a color-effect estimate, paired ablation, unseen validation or strength proof. No pooling with earlier runs.

Read-only audit passed: all 240 input bindings, four complete legal histories and terminal results, 492 timed searches, role options, removed experimental environment, commands and recorded clocks. Maximum observed external search time 9917ms; USI time 9912ms. All games ended by resignation; the native board was still ongoing, as expected. Seven preparation tests were already passed. No new searches or games.

[Local viewer](../../../results/teatsui-baseline-review4-2026-11-14/review.html): all 548 displayed states match native replay SFEN. The two panels show different times of ONE game, not different coefficients. Defaults game3, White/top is adopted baseline, left38/right46. Right timeline advances independently; button pins a new left reference. All four games selectable.

## Initial review focus, pending user judgment

Game3, White versus central rook: inspect38/46/54/60. Black39 P9e, White40 Px9e, Black41 Lx9e, White42 P*9c. White44 P*5g draws Rx5g, then46 S6e. Black attacks the edge while White seeks central activity. White's own saved pre-move search scores are −276cp at38, −255 at46, −472 at54, −596 at60 (depth14/15/13/14). This is a window for reviewing defense versus counterattack timing, not proof that any selected move is a blunder or that an evaluation coefficient causes it. First White search16 already scores −238cp.

Game4, White versus static rook: the fixed opening permits immediate15 P2d/Px2d/Rx2d, followed by18 G3b/19 B9g/20 P6d/21 Rx2b+/22 Gx2b. The initial Black search15 reports +575cp and White16 −541cp; White20 −711cp and30 −732cp. This opening imbalance predates most observed middlegame choices. White later recovers part of the score gap (62 −245cp), so avoid presenting early disadvantage as an inevitable loss. Review opening conditions separately before designing any correction from this game.

Keep operational support10/D10 unchanged. Rank and exchange-burden prototypes remain rejected. Next: user's positional judgment on game3; only then select a bounded candidate-move diagnostic if useful. No new tuning or long-match request.
