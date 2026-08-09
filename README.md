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
