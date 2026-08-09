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

## Research and decisions

- [Methodological foundation](docs/research/methodological-foundation.md)
- [ADR 0001: engine/submission boundary](docs/adr/0001-engine-submission-boundary.md)
