# Rakuyou Development Notes

This file is the resume map: current state, durable decisions, constraints, and
links to evidence. Detailed experiment history belongs in `docs/experiments/`.

## Project and runtime

- Rakuyou is a personal experimental fork of Gikou 2. Preserve upstream
  copyright headers and existing C++ conventions.
- On Apple Silicon, build the SSE4.2 engine as x86_64/Rosetta. Read
  [development instructions](docs/development.md) before build or learning-data
  work. Run Python tests from the repository root with
  `python3 -m unittest discover -s test -t .`.
- Current runtime data in `bin/` is user state. Do not overwrite it during
  experiments. Last verified identities:
  - `bin/release`: `6f7891c4957e1bf37b1e80c37ad0c9cf83f34ca974e87be05fb05dd5c1f4c2ac`
  - `bin/params.bin`: `6bbc573306839fe019634dd94b06af7c22834a641e8bc060e23889ae9b3b2195`
  - `bin/progress.bin`: `ddf60a3180f768d9756b83cd4fe50a18b9e93855d1ad7281566934fb7c53a042`
  - `bin/probability.bin`: `dc2b18f1eaa7551822901eab7b68c6f279cc449ef527462b611b5d9510cb6c1a`
  - `bin/book.bin`: `cd42c35f48db3148a2c2f312887313b43135074dd3c0fa6bcd2fb04e66ac28c8`

## Current engine and book decisions

- `ShinYonenagaGyoku` defaults ON. At the initial position it selects Black
  `5i4h` or White `5a6b`, subject to legal root restrictions. The 25cp opening
  king-location preference is retained; retreats remain legal. Do not change
  these settings implicitly.
- The common 17-position book is
  `books/shin-yonenaga-book-v1.txt`, SHA-256
  `d080bc78583695da22641509ca93682653baa4761cb633f4f144ec1aef7c7e07`.
  Black's six-position book is
  `books/shin-yonenaga-black-book-pawn76-right-side-experiment.txt`, SHA-256
  `cb8d7e3e3a4ed2817752ea93d4890837fa43c91db752b5ce3a1dc534f38bb7eb`.
  White's 11-position v2 is
  `books/shin-yonenaga-white-book-v2-experiment.txt`, SHA-256
  `28e59ec12cb86ada7280687d130e29bdb28eb0d550840d634c73e003aa2ffc62`.
- Use the combined file explicitly with `ShinYonenagaGyoku` ON, `OwnBook` ON,
  and `BookMaxPly` 20. GUI settings do not switch automatically. Uncovered
  positions go to search; there is no standard-book fallback. Regeneration and
  source locations are in [books/README.md](books/README.md).
- The books are bounded operational choices, not proof of playing strength.
  White v2 is frozen. Black's pawn76/right-side six is the current operational
  choice; the pawn36 addition and other candidates remain unadopted.

## Learning work: closed, no candidate adopted

- The tempo-three-coefficient, four-feature king-safety, and one-feature
  gold-silver-pair experiments are closed. Current evaluation and runtime files
  remain the baseline. Do not resume learning, tune coefficients, expand data,
  run more searches/games, or adopt a candidate automatically. Wait for the
  user's direction before starting another experiment.
- Supported central fifth-rank pawns: authorized single20-update run is closed;
  selected0,baseline retained,no candidate adopted.
- The final pair-feature check selected only the five-update candidate for
  review. Validation re-quiescence search showed no PV or leaf changes; six
  normal-search roots had unchanged best moves and mixed PV/score changes.
  Adoption remains on hold. See the [final pair review](docs/experiments/learning/gold-silver/2026-10-12-pair-final-search-review.md).
- The expanded pair run used 143 training and 35 validation positions. Its
  validation improvement was small and layer results mixed; it is a mechanics
  observation, not evidence of playing-strength gain. See the [expanded
  result](docs/experiments/learning/gold-silver/2026-10-12-expanded-pair-learning-result.md)
  and [teacher/leaf audit](docs/experiments/learning/data/2026-10-12-pair-expanded-teachers-and-leaves.md).
- Earlier tempo and king-safety results, data preparation, and implementation
  notes are indexed in [learning reports](docs/experiments/learning/README.md).
  Preserve test splits and do not use them for tuning. Prior input diagnostics
  and qualitative game reviews exposed some test data; do not call the whole
  split unseen. Draw outcomes and max-ply draws have their recorded
  masking/adjudication limits. Existing `results/` attempt markers
  prevent reruns; never remove or bypass them.
- The 47-run self-play corpus has 2,740 games and 475,347 moves. Historical
  parameter/progress/probability identities are unknown. Existing train,
  validation, and test splits and their run-level separation are documented in
  [learning feasibility](docs/experiments/learning/framework/2026-10-11-learning-feasibility-plan.md).
  Gikou's normal `--learn` resets parameters/material; experiments used a frozen
  baseline plus deltas instead. Do not treat self-generated teachers as an
  independent stronger teacher.

## Next research direction: thickness and territorial control

- The user wants to explore thickness as a defining Shin-Yonenaga-Gyoku style;
  a stylistic feature may be worth adopting even without measured strength gain.
  Keep style effects and strength evidence separate in any future decision.
- Web consultation suggests thickness is useful, sustained control of an area
  for both attack and defense, not a universal numeric pattern. A high pawn
  foothold supported by gold/silver can both enable progress and deny the
  opponent a foothold. See [厚みを作るときに意識すべきこと](https://sakurai-shogi.com/araki-20240216/)
  and [厚い: 将棋用語](https://xn--pet04dr1n5x9a.com/%E5%B0%86%E6%A3%8B%E7%94%A8%E8%AA%9E/%E5%8E%9A%E3%81%84.html).
- Keep candidate aspects distinct: supported pawn territory, gold/silver
  advancement, safe king placement, and local influence around a meaningful
  front. Raw whole-board attack counts can reward irrelevant control; local
  attack balance is better treated first as a diagnostic. Traditional
  Hashi-gyoku Ginkanmuri descriptions are references, not direct definitions
  of this engine's Shin-Yonenaga-Gyoku.
- Three train-run games/four windows have now been reviewed. User agreed to
  investigate usefulness using current-evaluation teachers, with ONE feature:
  count unpromoted fifth-rank pawns on files3-7 directly defended by an own gold
  or unpromoted silver, once per pawn. No control-surplus gate, advance-distance
  bonus, or king feature. Signed coefficients;single20-update trial now closed.
  Evidence and limitations: [supported-pawn review](docs/experiments/learning/gold-silver/2026-10-12-supported-pawn-thickness-review.md).
- Existing143/35 frozen leaves checked statically: presence49/10; Black-owned
  pawns27/5,White-owned22/5;nonzero net49/10,max2per side. Draw presence15/47
  train,4/12validation;validationBlack-loss stratum0/6. No automatic refill.
- Update0 preparation/audit complete with new supported-pawn-probe and
  tools/learning/gold_silver/supported_pawn_preparation.py (no --run entry).
  Frozen teacher/leaf hashes preserved;native178 baselines and356 root/leaf
  independent counts match;zero candidate matches old178 cp baselines.
  L2 fixed1e-6:train gradients[-3.4664e-6,-5.9175e-6],cap regularization
  ~14.4%/8.45% of initialsignal. Coeffcap.5cp,20updates/batch128/seed20261011.
  Four static perturbations includingcaps give max1cp whole-position difference.
  New4+existing3 focusedtests pass;local independentbackup190files verified.
  Report: [preparation audit](docs/experiments/learning/gold-silver/2026-10-12-supported-pawn-preparation-and-scale-audit.md).
  Saved results/learning-pilot/2026-10-12-supported-pawn-preparation-v1/;
  reportSHA060bb14fdcda10282ccead3055a4888c0df19d8a41bcf563b667096bef90e2f4.
- Preparation committed16b4c49 before actuallearning. One20-update run complete
  with same143/35/L2/settings,selected0(no improved validationcandidate).
  Saved20avg[+.240306,+.241382]cp per pawn,raw[15748,15819];current20delta
  [+.380489,+.376393],capsnotreached. Trainintegerloss~.006466%improves;
  validation~.024816%worsens:White~.053319%worse,Black/drawunchanged.
  Validationonly1leaf changes1cp;Black-supported6e/7e withS7f getsbonus,
  Whitebase272->271 while savedteacher646. Whole root/leaf max1cp;
  smoothmax~.482cp. No strength/style benefit demonstrated.
  New4guardtests pass;20step RNG/gradient/trajectory and4checkpoints replay
  exactly;old190+new10backupfiles verified. All runtime/books/oldcandidates kept.
  Report: [learning result](docs/experiments/learning/gold-silver/2026-10-12-supported-pawn-learning-result.md).
  results/learning-pilot/2026-10-12-supported-pawn-run-v1/report.json SHA
  39dd3c5a4817e8c9ee99adca77dff55773df874e07300e31d2efd9e981019650.
  Prepdir learning-attempt-v1.json locksrun;neverbypass. Allcandidates saved.
- Supported-pawn result implementation/report committedc345e5f. User wants
  to finish thickness investigation before considering theme-free learning.
- Closed Gold experiment: supported gold advancement, reviewed in3train games.
  Score own unpromoted gold defended by another gold/unpromoted silver:
  ownrank1-2=0,3=1,4=2,5or further=3. Allfiles,once per gold,no king bonus
  or control-surplus gate. One-hop support still counts some fragile chains.
  [Gold advancement proposal](docs/experiments/learning/gold-silver/2026-10-12-supported-gold-advance-proposal.md).
  Saved reviewSHA13867a499ce997900e947c1add9e0f890d51c64ae28ebc08952db3ef8da49f07.
- Existing143/35 leaves: presence41/15,nonzero net36/12,maxscore2.
  Qualifying gold occurrences at ownrank3:44train/17val;rank4:2/2;rank5+:0/0.
  Main limitation:24-80ply sampling misses deep rising formations. Train-only
  initialgrad[-2.8616e-6,-3.8098e-6];L2_1e-6 capratio~17.5%/13.1%.
  These were pre-supplement measurements;later preparation/result below.
- User authorized the small supplement. Selected16train/8fresh-validation
  roots from savedgames:8side/height/support buckets each2/1,Shin own foremost
  gold only,one root/game,seed20261011,window24-120,run caps4/2,no outcome/cp
  quality selection. Exclude239previously used games andcross-split/test keys.
  All24 native histories legal/SFEN-Huffman exact,no exclusions/refill. Roots
  train87-116ply/12runs,val82-116ply/6runs. Supplemental draw3train/0val;
  if allaccepted combined159/43 hasdraw50/12. Some attacking golds included.
  Selectionstage:5tests pass;oldbackup+19newfiles verified,teacher/QS/updates0.
  [Supplement preparation](docs/experiments/learning/data/2026-10-12-gold-advance-supplement-preparation.md).
  results/learning-pilot/2026-10-12-gold-supplement-preparation-v1/manifest.json
  SHA06d59cc954ccae8e464b05b26f3c3fe4eb3008b23d6a538aa08267ae90dc1938.
- Authorized Gold teacher/leaf preparation is complete: additional16/8 all
  accepted;combined159/43,draw50/12. No exclusions/retries/refill,updates0.
  Old178 teachers/leaves reused byte-identically;new24 depth15 teachers and
  new24 qsearch calls only. Runtime/books/25cp unchanged;no adoption.
  [Teacher/leaf and zero audit](docs/experiments/learning/data/2026-10-12-gold-advance-teachers-and-leaves.md).
  Goldprep report results/learning-pilot/2026-10-12-gold-advance-preparation-v1/report.json
  SHA99c40167875f063baaea07052c5a6c161f5a272edd8f1910498b6aa9852002fc.
  Goldteacher report SHA7688a8e3df760a389f327a55a67632798ad6f41c510b48f53807b37622896951.
- Goldleaf presence52/19,nonzero net46/16;values2 gold7/4,values3 gold5/3.
  Supported4th-rank-or-higher goldpositions10/6 (newsubset8/4 allownside).
  Initialtraingrad[-2.121850831e-6,-3.800665585e-6];L2_1e-6 atcap.5
  ratios23.56%/13.16%,needs_reviewFalse. Opening signal close to25% guide.
  Zeroevaldiff0;static cap perturbations wholepositionmax3cp;no validationloss
  measured. Newprobe results/gold-advance-tools/gold-advance-probe
  SHA7735d0cbf2bccdfefb9474643e413c5b3913a40da0824947562cf8b7ba1074f0.
  Makefile/oldprobes unchanged;native20fixtures and9focusedtests pass.
  Preservedparent190+selection19 copies;new38files backedup/verified.
  Saved-results read-only audit accepted;404 root/leaf independentcountchecks,
  normalizedcrosssplit/test-key overlaps0. No test quality or newtestgames read.
- User authorized one20-update Gold run;COMPLETE and closed,no adoption.
  Same159/43,L2_1e-6,batch128,seed20261011,rate/step.05,cap±.5.
  Selected5 by unchanged integer-validation+L2 rule;average[+.107318,+.115765],
  raw[7033,7586]. Integertrain improves.010856%,validation.001307%:
  Black.002520%,Whiteunchanged,draw.004826%;only2validationleaf1cpchanges.
  FULLPRECISION validation WORSENS .001569%,so tinyintegerbenefit isrounding
  sensitive. One improvedexampleisattackinggold,notpuredefensivethickness.
  Average20[+.228069,+.233064],raw[14946,15274],integertrain+.021327%,
  validation-.041141%,White-.079511%,draw-.143246%. No caphit.
  Wholepositionmax1cp(selected5),2cp(trainroot20);smoothleafmax~1.396cp.
  All4 candidates and20trajectory saved. Fournewguards pass;arithmetic
  RNG/gradient/trajectory/4checkpoints audit exact;oldbackups+new22files and
  audit2files verified. No newteacher/qsearch/normal searches/games/testquality.
  Runtime/books/25cp/oldcandidates unchanged;no additional tuning/extension.
  [Gold learning result](docs/experiments/learning/gold-silver/2026-10-12-supported-gold-advance-learning-result.md).
  results/learning-pilot/2026-10-12-gold-advance-run-v1/report.json
  SHAcc92ce508ed449d09697d3ca101b7e24b1f22f9eddc510aca3327d171e48ca60;
  auditSHA5ec0cc12f5fb3f29b736ab7f59343501624212d1707b2e6ffebac7b03d8b3b91.
  Goldprep learning-attempt-v1.json locksrun;never remove/bypass.
- NEXT: discuss closure of thickness trials and next learning approach.
  Gold,centralpawn,pair,safety,tempo candidates remain held. No further
  learning/search/games/feature extension or adoption authorized. User requested
  one coarse Gold commit covering proposal,supplement,teacher/leaf preparation,
  implementation,andresults;check git history/status for its revision.
  Suggested discussion: a theme-free Shin-Yonenaga game-learning pilot using
  moves/outcomes,with current-base preservation and draw masking planned first.
  This is a proposal only;no new learning implementation/execution authorized.
- Deferred ideas: historical2games and Doronuma-ryu Furibisha-yaburi can guide
  motifs;no book ingestion/new dataset authorized. Theme-free game learning
  using moves/outcomes is for AFTER the thickness phase. Native Gikou combines
  move imitation,win/loss prediction,depth consistency and resets parameters;
  a current-base delta route would need separate planning. Our pilots use
  current-base cp teachers and do not explicitly teach Yonenaga's style.
- User knows Shogi but not learning: explain effects with piece coordinates
  and concrete worked/failed formations,using plain language.
- Old gold-silver examples already exposed games23/50 of test run
  `shin-black-silver38-pawn76-trial-r2`; this turn reread them before confirming
  the split, then excluded them from new case selection. Keep this exposure
  documented; do not rebuild splits or claim those games are unseen test data.

## Repository organization and data safety

- Tools and tests are physically grouped by books, analysis, and learning
  themes. Their usage and build details live in `docs/development.md`; avoid
  adding inventory/status prose to README files.
- Progress, current decisions, next steps, and temporary execution limits live
  here. READMEs describe directory roles, usage, and links. Experiment reports
  preserve methods, outcomes, uncertainty, and historical decisions.
- Raw games, search outputs, checkpoints, and audit JSON live in ignored
  `results/`. Reports record paths and SHA-256 identities. Historical audit
  metadata may contain old source paths; use its recorded revision or preserved
  source copy when reproducing old results.
- Important raw data has not been independently backed up outside this
  workspace. Never delete originals before a separate backup is verified. Keep
  third-party KIF and large raw game logs out of Git.
- Public documentation must use repository-relative paths or neutral
  placeholders, never personal home-directory paths. Avoid causal or strength
  claims unsupported by the experiment design; small game/search samples are
  descriptive.

## Recent repository maintenance

- Experiment reports are grouped under `docs/experiments/{books,learning,
  openings,selfplay}/`; each theme README is a durable index. `configs/` and
  `positions/` remain at their established paths.
- Two supplemental White-book analyses formerly kept in ignored `results/`
  are now tracked under `docs/experiments/books/white/`; parent report links
  point to them. Raw JSON remains in `results/`.
- Book source JSON is grouped under `books/sources/`, held candidates under
  `books/experiments/`, and retired reproducible sources under `books/archive/`.
  Active book text paths and contents were preserved during cleanup.
- Tools and tests were moved into category packages; imports and CLI entry
  points were updated. The last full verification after that move passed 196
  tests. No engine/evaluation code changed in the organization work.
- `docs/development.md` now covers build, tests, and durable data safeguards;
  dated learning-stage instructions belong in experiment reports.
- Previous pushed research-direction checkpoint: `52c8a33`. Recheck `git status`
  and recent history on resume; the supported-pawn review is a later change.
