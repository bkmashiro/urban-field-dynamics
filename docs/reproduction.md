# Reproducing bounded synthetic evidence

## Authority and source pin

Python 3.12 is the authoritative simulation runtime. Browser or TypeScript code may replay exported evidence but does not implement a second simulation engine.

Checkout the source revision recorded in `provenance.json`. Verify the commit signature when Git history is available, then install the frozen environment:

```bash
git checkout --detach <source_revision>
uv sync --frozen
uv run pytest -q
```

Replay verification itself does not call Git. It parses the frozen config and provenance, reruns the campaign, reconstructs every derived artifact byte for byte, and checks the manifest hashes.

## Bounded campaign

```bash
uv run urban-field scaled-qualification \
  --output results/scaled-integrated-2050-qualification-32-bounded \
  --worlds 32 --end-year 2050 --workers 4 \
  --source-revision <full-commit-sha>
uv run urban-field verify-bounded \
  results/scaled-integrated-2050-qualification-32-bounded --workers 4
```

## Policy-intensity sweep

```bash
uv run urban-field scaled-sweep \
  --output results/scaled-p3-intensity-canary-8-bounded \
  --worlds 8 --end-year 2050 --workers 4 \
  --source-revision <full-commit-sha>
uv run urban-field verify-sweep \
  results/scaled-p3-intensity-canary-8-bounded --workers 4
```

## Stress matrix

```bash
uv run urban-field scaled-stress \
  --output results/scaled-stress-2050-canary-8-bounded \
  --worlds 8 --end-year 2050 --workers 4 \
  --source-revision <full-commit-sha>
uv run urban-field verify-stress \
  results/scaled-stress-2050-canary-8-bounded --workers 4
```

## Artifact contract

Every bounded package contains a canonical config, `provenance.json`, derived evidence and `manifest.json`. Campaign packages include summaries, qualification, equity, decision, morphology and representative-world evidence. Sweep and stress packages deliberately omit raw world results and retain only bounded matched diagnostics.

Output directories must be new or empty. Treat a manifest mismatch, parse failure, non-convergence exception or replay byte difference as a failed artifact; do not repair evidence files manually.

Fewer than 32 worlds are engineering canaries. A 32–64-world run can support synthetic qualification after convergence review. Larger ensembles still do not imply empirical validity without observed data and held-out validation.
