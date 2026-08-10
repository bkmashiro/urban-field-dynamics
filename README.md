# Urban Field Dynamics

Seeded, multi-world urban evolution simulation engine for robust public-policy experiments.

## Scope

The engine owns stochastic world evolution, policy and ablation campaigns, and evidence export. The `open-city-ai/haidian` submission consumes pinned aggregate outputs and remains a separate formal package.

## Runtime layers

- NumPy/Pydantic authoritative reference engine
- process-level world parallelism
- optional Numba kernels only after profiling
- optional JAX/XLA batch acceleration only after CPU qualification

The core engine has only two direct runtime dependencies: NumPy and Pydantic. AequilibraE, analysis storage, acceleration, GPU and publication tooling remain opt-in extras.

## Development

```bash
uv sync
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
```

Run and fully replay-verify the original redevelopment smoke:

```bash
uv run urban-field smoke --output results/smoke-v1
uv run urban-field verify results/smoke-v1
```

Run and fully replay-verify the bounded synthetic P3 intensity canary:

```bash
uv run urban-field scaled-sweep \
  --output results/scaled-p3-intensity-canary-8-bounded \
  --worlds 8 --end-year 2050 --workers 4 \
  --source-revision "$(git rev-parse HEAD)"
uv run urban-field verify-sweep \
  results/scaled-p3-intensity-canary-8-bounded --workers 4
```

The declared accessibility threshold in this built-in canary is only a synthetic engineering
demonstration. Crossing brackets are not planning standards or calibrated policy advice.

Run and replay-verify the standard bounded P0–P3 stress matrix:

```bash
uv run urban-field scaled-stress \
  --output results/scaled-stress-2050-canary-8 \
  --worlds 8 --end-year 2050 --workers 4 \
  --source-revision "$(git rev-parse HEAD)"
uv run urban-field verify-stress \
  results/scaled-stress-2050-canary-8 --workers 4
```

Run and replay-verify the bounded scaled campaign:

```bash
uv run urban-field scaled-qualification \
  --output results/scaled-integrated-2050-qualification-32-bounded \
  --worlds 32 --end-year 2050 --workers 4 \
  --source-revision "$(git rev-parse HEAD)"
uv run urban-field verify-bounded \
  results/scaled-integrated-2050-qualification-32-bounded --workers 4
```

Each bounded workflow hashes `provenance.json`. Replay reads the frozen source revision from the
artifact and does not invoke Git. Fewer than 32 worlds are labelled engineering canaries; 32 or
more remain synthetic qualification, not empirical validation.

The engine also ships an integrated synthetic fixture covering P0–P3, weighted household and
firm cohorts, annual market feedback, multimodal transport, seasonal relative exposure, and
nine matched mechanism ablations. The frozen 8-world artifact is an engineering canary, not a
statistical policy result.

`smoke-v1` is a redevelopment-only synthetic mechanism check. Neither fixture is a calibrated
Haidian forecast.

## Research and decisions

- [Methodological foundation](docs/research/methodological-foundation.md)
- [Data requirements and empirical validation gates](docs/research/data-requirements-and-validation.md)
- [Bounded evidence reproduction](docs/reproduction.md)
- [Local pre-PR review packet](docs/review/pre-pr-review-packet.md)
- [ADR 0001: engine/submission boundary](docs/adr/0001-engine-submission-boundary.md)
- [Implemented redevelopment ODD slice](docs/model/odd-redevelopment-slice.md)
- [Implemented weighted cohort and market ODD slice](docs/model/odd-agent-market-slice.md)
- [Implemented transport and seasonal exposure ODD slice](docs/model/odd-transport-environment-slice.md)
- [Integrated 64/128-world synthetic qualification](docs/model/integrated-qualification-128.md)
- [Implemented 1,200-unit spatial substrate and morphology observers](docs/model/odd-scaled-spatial-slice.md)
- [Scaled 64-world synthetic qualification](docs/model/scaled-qualification-64.md)
- [Implemented rolling trigger planner](docs/model/odd-rolling-planner.md)
- [Implemented weighted cohort lifecycle dynamics](docs/model/odd-cohort-dynamics.md)
- [Implemented cohort-weighted equity observers](docs/model/equity-observers.md)
- [Implemented Pareto, tail-harm, and tipping diagnostics](docs/model/decision-diagnostics.md)
- [Implemented matched policy-intensity sweeps](docs/model/policy-intensity-sweeps.md)
- [Implemented weighted labor matching](docs/model/odd-labor-matching.md)
- [Implemented public budget and capacity ledger](docs/model/infrastructure-budget-ledger.md)
- [Implemented bounded annual market response](docs/model/odd-market-clearing.md)
- [Implemented matched stress and sensitivity matrices](docs/model/stress-sensitivity.md)
- [Measured exact transport optimisation](docs/model/scaled-runtime-profile.md)
- [Current 32-world 2026–2050 synthetic qualification](docs/model/scaled-qualification-2050-32.md)
- [Current 64-world 2026–2050 synthetic qualification](docs/model/scaled-qualification-2050-64.md)
- [Current 8-world 2026–2050 stress canary](docs/model/scaled-stress-canary-2050-8.md)
