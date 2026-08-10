# Urban Field Dynamics

Seeded, multi-world urban evolution simulation engine for robust public-policy experiments.

## Scope

The engine owns stochastic world evolution, policy and ablation campaigns, and evidence export. The `open-city-ai/haidian` submission consumes pinned aggregate outputs and remains a separate formal package.

## Runtime layers

- NumPy/SciPy reference model
- process-level world parallelism
- optional Numba kernels after profiling
- optional JAX/XLA batch acceleration after CPU qualification

AequilibraE, analysis storage, GPU support, and browser-PDF tooling are optional dependencies rather than bootstrap requirements.

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

The engine also ships an integrated synthetic fixture covering P0–P3, weighted household and
firm cohorts, annual market feedback, multimodal transport, seasonal relative exposure, and
six matched mechanism ablations. The frozen 8-world artifact is an engineering canary, not a
statistical policy result.

`smoke-v1` is a redevelopment-only synthetic mechanism check. Neither fixture is a calibrated
Haidian forecast.

## Research and decisions

- [Methodological foundation](docs/research/methodological-foundation.md)
- [ADR 0001: engine/submission boundary](docs/adr/0001-engine-submission-boundary.md)
- [Implemented redevelopment ODD slice](docs/model/odd-redevelopment-slice.md)
- [Implemented weighted cohort and market ODD slice](docs/model/odd-agent-market-slice.md)
- [Implemented transport and seasonal exposure ODD slice](docs/model/odd-transport-environment-slice.md)
- [Integrated 64/128-world synthetic qualification](docs/model/integrated-qualification-128.md)
- [Implemented 1,200-unit spatial substrate and morphology observers](docs/model/odd-scaled-spatial-slice.md)
- [Scaled 64-world synthetic qualification](docs/model/scaled-qualification-64.md)
