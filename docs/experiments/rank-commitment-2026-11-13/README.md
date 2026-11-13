# Rank commitment prototype (unadopted)

Checkpoint of the counterplay experiment and the user's positional judgments.
The operational baseline remains support10/D10. These patches are research
artifacts; neither changes normal builds nor installs the prototype.

The general aim is thick shogi: support sustainable territory, use an
unsustainable rank as bait when counterplay is available, and convert thickness
into attack at the right moment. Keeping the shape is not an end in itself.

- User strongly prefers the trial's P2e/P3e counterplay against S7f commitment.
- In the central-rank case the user prefers S4d liquidation to S3f maintenance.
- The timed comparison changed choices, but fixed-depth diagnosis ranks S3f
  first with and without the correction. Tracing finds only White penalties in
  the S4d branch. A direct penalty on Black's liquidation is unsupported.
- Historical unrestricted timed divergence remains unexplained. No tuning,
  strength claim, operational adoption or long-match rerun follows from this.

See [trial](trial-result.md), [follow-up](followup-result.md),
[diagnosis](diagnosis-result.md), and [trace](trace-result.md).
`summaries.json` preserves compact measured evidence. Full local runs, native
probes, logs and plans remain in ignored `results/teatsui-rank-*/` folders;
this checkpoint does not archive all raw search data.

## Reconstruct the experimental source

Build a new adopted snapshot using its tracked build script, then apply the
trial patch only in that snapshot (commands run from repository root):

```sh
python3 adopted/support-contact-2026-11-13/build.py --output results/rank-rebuild
patch -d results/rank-rebuild/source -p1 --batch -i ../../../docs/experiments/rank-commitment-2026-11-13/trial.patch
```

For the diagnostic logging version, also apply `trace.patch` the same way.
Recompile that snapshot before running it; applying a patch alone does not
change the already-built runtime. Rebuild from the repository root with:

```sh
rank_repo_root="$PWD"
make -C results/rank-rebuild/source TARGET=development executable -j2 \
  output_file=../runtime/release \
  LDFLAGS="-Llib/libomp-x86_64/lib -Wl,-rpath,$rank_repo_root/lib/libomp-x86_64/lib"
```

The regular repository build remains unchanged. See
[build prerequisites](../../development.md).

`RAKUYOU_RANK_COMMITMENT_CP=0` disables the correction (the default); `10`
enables the experimental correction. Both use support10/D10. In the optional
trace build, `RAKUYOU_RANK_TRACE_PATH` names a new TSV output file; it is opened
for writing, so never point it at an existing artifact. Use a single search
thread and a fresh process. Logging is capped at20,000 qualifying calls.

`source-hashes.json` records full source hashes for adopted/trial/trace versions.
Both patches were applied sequentially to a temporary adopted-source copy;
every resulting source hash matched the tested snapshots exactly. Trace runs
matched all non-time reported fields of the original fixed-depth searches.

## Next positional review

[Liquidation comparison](liquidation-review.html) is standalone and works
without the ignored results directory. `liquidation-review-data.json` retains
root history and the three saved PVs. All42 displayed states were matched to
native replay; no new searches.

Both sides play S4d/Gx4d/P5c+/R3b. At49 the previously preferred line plays
P*6b, whereas the detailed restricted searches play P4f before White's
P*5e/R5i/S*5g sequence. The latter is NOT established as a refutation of the
former: Black's own move differs first. Review the need for P4f versus immediate
P*6b before attributing tactical trouble to the whole S4d plan. User review of
this branch is pending. Baseline and trial coefficients remain unchanged.

Nov14 follow-up: corrected P4f (not gold); [two continuation searches](continuation-result.md) and [new viewer](continuation-review.html). Both correction0, after49; P*6b receives better finite-search evaluation, with both roots still White-favored. See the new concrete continuations before judging.
