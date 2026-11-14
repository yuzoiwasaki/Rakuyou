# Exchange-burden diagnostic prototype — 2026-11-14

User authorized trying an exchange-aware direction. Implemented a small native diagnostic, not an evaluation hook: start from the original rank-count predicate's first witness; enumerate legal enemy captures of that pawn and legal immediate same-square recaptures; use the existing Swap::Evaluate (SEE) to estimate the recapture's material result. If any capture has no recapture with SEE>=0, mark a possible local burden. Both nonpromotion/promotion forms are checked when applicable.

The enemy-to-move hypothetical position is reconstructed from SFEN so turn-dependent legality caches are correct. Skip if either king is already in check; do not model a forced tempo switch under check. Immediate moves are legal, but subsequent SEE exchanges are an approximation and do not prove a legal forced sequence. It ignores other-square counters, drops, king safety, initiative, recapture placement and attack speed. Only the first original triggering pawn is diagnosed; production use would require considering every eligible pawn. No coefficient or threshold fitted to search results.

A nonlosing recapture does NOT mean the whole transaction is free: the original rank pawn can still be lost. A zero-valued silver recapture can simply exchange silvers while giving up that pawn. SEE numbers below are material exchange units, not searched position evaluations.

## Tests and result

63 positions: original29 static fixtures/histories,29 observed active witnesses, and5 new checks (knight imbalance, its mirror/rotation, pinned attacking knight, in-check skip). All original native output fields match the unchanged reference probe exactly after removing diagnostic fields. Existing full/incremental/unmake/rotation checks remain active. New checks verify a negative recapture can be detected, color/mirror handling, illegal pinned captures excluded, and check positions skipped. Frozen match inputs unchanged. No engine searches or games.

| Case | Opponent's silver capture of rank pawn | Best recapture SEE | Local burden |
|---|---|---:|---|
| Original criticized S8d support, after S7f | S7f8e | S8d8e:0 | no |
| Liked central counterplay, game07 after42 | S7f6e | S5d6e:0 | no |
| Synthetic knight capture (N7g8e) | knight rather than silver | S8d8e:−310 | yes |

In BOTH real examples, enemy silver capture has SEE+198; immediate silver recapture has SEE0. Enemy rook capture has SEE−378, with silver recapture SEE+576. The entire local material patterns are identical despite different user judgments. The liked example is spared, but so is the original unsupported-rank example this feature was intended to address. A nonzero threshold cannot separate these equal local values.

## Decision

Do not integrate this gate or run matches: its required contrast already fails at the static diagnostic stage. Keep it as a tested diagnostic artifact, without a production hook or tuned coefficient. This does not reject exchange-aware reasoning in general; it shows same-square material exchange alone is insufficient for the desired positional distinction.

Likely additional context is the resulting piece placement, tempo and available counterplay, but that is an inference and has not been implemented or proven here. A future feature needs an explicit way to measure that context and contrasting fixtures before searching; don't silently equate no material loss with sustainable defense or force remembered moves.

The adopted support10/D10 runtime and old rank10 prototype are unchanged. No further searches scheduled and previously closed tactical branches remain closed.

## Artifacts

`exchange_probe.h` implements the diagnostic; `checks-summary.json` records each input and capture/recapture result; `input-hashes.json` identifies local tested artifacts. Full outputs/source copy are under ignored `results/teatsui-exchange-burden-2026-11-14/`.

`build.py --output NEW_DIRECTORY` rebuilds the diagnostic in a new directory using the existing isolated rank-trial source snapshot and local compiler/data prerequisites. It does not build/install a playing engine. `check.py` reproduces the saved local validation using the original diagnostic output directory; it is not a match runner. No large binaries or parameter files are tracked.
