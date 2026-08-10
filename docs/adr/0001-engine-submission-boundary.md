# ADR 0001: Separate the authoritative Python engine from the formal submission

- Status: accepted
- Date: 2026-08-09

## Context

The Haidian formal-submission contract accepts structured planning artifacts, GeoJSON, local visual assets, HTML, images and PDFs. Its participant validator does not accept arbitrary Python source trees inside a submission. At the same time, Urban Field Dynamics requires a testable scientific engine, experiment configurations and potentially large intermediate outputs.

Placing the authoritative model only in browser JavaScript would satisfy the file whitelist but weaken the numerical, geospatial, transport and ensemble toolchain. Hiding Python source in unsupported extensions or generated prose would weaken auditability. Adding engine files to the upstream pull request would violate the required participant change scope.

## Decision

Maintain two linked public artifacts:

1. `bkmashiro/urban-field-dynamics` is the authoritative Python engine and research record.
2. `bkmashiro/haidian`, branch `submission/bkmashiro/urban-field-dynamics`, contains only the formal submission package allowed by upstream.

The submission records an immutable engine commit or release, campaign configuration identity, source registry entry and generation timestamp. The engine exports submission-safe aggregate JSON, representative traces, GeoJSON, SVG/PNG figures and manifests.

The browser visual is a replay and evidence interface. It does not contain a second implementation of the urban evolution model. A small JavaScript checker may verify internal consistency among exported metrics, layers and interface data, but it does not claim to reproduce the Python campaign.

## Engine architecture

- Python 3.12 is the supported runtime.
- NumPy reference implementations define numerical semantics.
- Numba may accelerate qualified CPU kernels.
- Multiprocessing distributes independent worlds.
- JAX may accelerate qualified array kernels after profiling and parity checks.
- NumPy Philox event tapes provide mechanism-scoped matched randomness.
- Shapely and PyProj may own future observed-geometry and CRS adapters; the current stylised lattice does not require them.
- Polars/Parquet and DuckDB remain optional analysis-layer candidates, not hot-state dependencies.
- A fast transport surrogate runs in ensembles; AequilibraE remains an optional future selected-scenario oracle.

## Evidence boundary

Every exported result carries one of these statuses:

- `official`: supported by a cleared official source for the stated use;
- `public_observed`: measured or published public data with traceable scope;
- `provisional`: repository or project approximation unsuitable for official control;
- `synthetic`: generated fixture, initial condition or experiment parameter;
- `design_target`: proposed target or policy value;
- `unknown`: required value not currently supported.

Simulation output does not inherit a higher status than its inputs. A synthetic run over provisional geometry remains synthetic/provisional even if its arithmetic is exact.

## Consequences

### Positive

- Python tools can be used without weakening the upstream package contract.
- Engine tests, experiments and source history remain public and reusable.
- The formal package stays small, offline and reviewable.
- Browser code cannot silently diverge from the scientific model.
- Heavy raw campaign artifacts can be versioned independently from the submission.

### Costs

- Two repositories must remain linked by immutable identities.
- Export contracts require tests.
- A reviewer needs the companion repository for a full rerun.
- Release automation must fail if the configured engine identity does not match exported provenance.

## Rejected alternatives

### Implement the simulator in TypeScript

Rejected as the authoritative path. TypeScript remains appropriate for the offline replay UI, while the authoritative engine uses Python, NumPy event tapes and optional scientific adapters only when an implemented mechanism requires them.

### Commit Python under the formal submission

Rejected because it conflicts with the upstream file and change-scope contract.

### Keep Python only in a local ignored directory

Rejected because results would not be independently reproducible.

### Maintain Python and TypeScript simulators

Rejected because semantic drift would make evidence provenance ambiguous.

## Verification

The boundary is accepted only if:

- engine tests pass from a clean `uv sync`;
- a frozen campaign export can be regenerated from its recorded engine commit and config;
- submission assets contain no undeclared remote dependency;
- aggregate values used by proposal, figures and UI trace to the same export manifest;
- the upstream participant preflight accepts the final submission scope.
