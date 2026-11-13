# Liquidation continuation — 2026-11-14

User corrected the piece: 4g4f is P4f, not G4f. Native starting board confirms a Black pawn at4g. Generated board state/move captions already showed a pawn, but prose and line labels incorrectly said gold. Corrected tracked reports, labels and resume map; original frozen search logs unchanged. User tentatively prefers P*6b, withholding judgment without the continuation.

Exactly two fresh 10-second searches (depth15 cap), after49 P*6b versus P4f, both unchanged trial binary with correction0, support10/D10, ShinON, bookOFF, thread1/hash64. Both reported depth15. All30 reported PVs and best moves passed native legality replay; frozen bindings unchanged. No tuning, repeats or installation.

| Black choice at49 | White reply | White-view score | Black-view equivalent |
|---|---|---:|---:|
| P*6b | G6a7a | +248 | −248 |
| P4f | S*5e | +403 | −403 |

P*6b line: G7a, +P5c6c, P*5e, +P6c7b (takes silver), Gx7b, R5f9f, P*6h, G6i5i, R3b6b ... .
P4f line: S*5e, P*6b, G7a, +P5c4c, R3b6b, R5f5i ... . This differs from the earlier ancestor-root prediction P*5e/R5i/S*5g. Re-search is not a forced-line confirmation.

The bounded continuation gives P*6b a better evaluation than P4f, consistent with the user's tentative preference, but both scores favor White and do not establish winning play or absolute superiority. Separate fresh roots and finite depth remain limitations. This is a positional diagnostic with correction disabled, not evidence to adopt or retune the experimental correction.

[Continuation viewer](continuation-review.html): left P*6b, right P4f, both lower-side Black/Shin, starts at50. All39 displayed states exactly match original native probe replay. Original root histories and PVs in `continuation-review-data.json`; full searches in local ignored `results/teatsui-liquidation-continuation-2026-11-14/`. No further search scheduled; next user review of the concrete continuations.
