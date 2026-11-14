# Counterplay timing candidates — 2026-11-14

User considers the central-rook pair roughly equal. Right shows counterplay intent but the enemy attack arrives first; early N3g should restrain it. Left is interesting but should defend against S7f with G7h. The principle is to restrain/slow the enemy enough for counterplay to arrive, not always preserve territory or always attack.

## Fixed bounded comparison

Three roots chosen before search, each with exactly two legal candidates: actual played move and user suggestion. Same trial binary and original per-game correction (left0, right10); support10/D10/ShinON/bookOFF, thread1/hash64, MultiPV2, depth15 cap/10-second byoyomi. No repeated searches, tuning or installation. Before all searches, native replay verified every root and each proposed move. Left checks immediately after36 S7f. Right checks after40 (39 P3f has just cleared3g) and after44 (before the actual rook retreat).

| Position / move number | Played candidate | Suggested candidate | Common reported depth |
|---|---|---|---|
| Game01 after36 /37 | P5e −77 | G7h −120 | 14 |
| Game02 after40 /41 | P9e −187 | N3g −435 | 14 |
| Game02 after44 /45 | R5i −356 | N3g −491 | 14 |

All scores are Black-view cp. Each comparison uses the two rows at the same reported depth from one search, not two differently deep final rows. All3 selected the actual played candidate. Restricting candidates and using MultiPV changes search behavior, so this does not fully reconstruct the historical choice or prove the user's suggestions inferior.

G7h PV begins G7h/P*5c/P5e/N3c/P5d/Px5d/Rx5d/S6e/R5c+. It prevents the immediate promoted-silver incursion in this predicted line while retaining a central attack. The43cp gap is one bounded estimate, not an approved tolerance or a forced tactical refutation. No evidence warrants forcing G7h with an arbitrary bonus.

N3g at41 meets P*2e/Px2e/Nx2e/P*2f/Nx3g+/Kx3g, bringing the king forward in this PV. N3g at45 meets P*2e/Px2e/Nx2e/Nx2e/Rx2e/P*2f/R2a. The opponent uses the knight contact/2-file to make exchanges rather than being restrained. These are candidate tactical explanations to inspect, not unique forced defenses. A plan preparing P3f/N3g at earlier plies is NOT tested here and is not refuted by these two roots.

## Verification and review

All84 reported PVs/best moves passed native legality replay. Existing frozen bindings, including completed match inputs, unchanged. [Candidate viewer](../../../results/teatsui-counter-timing-2026-11-14/review.html) shows115 states matched to original native replay. Both panels compare lower-side Black; LEFT means the played candidate's new PV, RIGHT the proposed candidate's PV. This differs from the previous page's rank0/rank10 meaning. Dropdown chooses the three timings; opening view is37 G7h.

`summary.json` preserves roots, candidates and equal-depth PVs; full local run/plan/logs are under ignored `results/teatsui-counter-timing-2026-11-14/`. User review pending. No more searches scheduled; retain both the G7h counterplay line and the knight-exchange timing issue before considering any general feature change. Operational baseline and unadopted trial remain unchanged.
