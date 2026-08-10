# Methodological foundation for Urban Field Dynamics

Status: research baseline, 2026-08-09

## 1. Intended use

Urban Field Dynamics is an exploratory policy model. Its purpose is to compare how public interventions change the distribution of long-run urban outcomes under explicit assumptions. It is not a parcel forecast, an official planning model, or a substitute for surveyed boundaries, observed OD matrices, regulatory controls, property records, or environmental monitoring.

This boundary follows established urban microsimulation practice. UrbanSim represents households, businesses, developers, parcels and buildings, advances the system through annual steps, and couples land use to transport accessibility. Its documentation also warns that a specific development on a specific parcel twenty years ahead is unlikely to be predicted correctly; appropriate use requires aggregation, sensitivity testing and multiple runs. [1]

Accordingly, this project may report:

- distributions over policy outcomes;
- directional or aggregate spatial tendencies;
- matched-seed policy differences;
- mechanism-sensitive emergent patterns;
- conditions under which an intervention becomes vulnerable;
- commitment, optionality and trigger classifications.

It may not report a stochastic realization as the planned or predicted 2050 city.

## 2. Description protocol

The model will be documented with the ODD structure: Purpose and patterns; Entities, state variables and scales; Process overview and scheduling; Design concepts; Initialization; Input data; and Submodels. The ODD update describes this structure as a human-readable, implementation-independent route to understanding and reimplementation, and explicitly asks the first element to state the patterns used to evaluate the model. [2]

The source tree will therefore maintain an executable model contract and a corresponding ODD document. The process schedule is code, not only prose. Every submodel must declare:

- state read and written;
- spatial and temporal scale;
- process order;
- source or assumption status;
- stochastic event tape consumed;
- invariants and failure behavior;
- observations emitted.

Large submodels such as transport and environmental exposure may receive nested ODD sections, consistent with the ODD recommendation for complex coupled models. [2]

## 3. Time and process structure

The initial schedule is deliberately explicit:

1. rolling public-policy update in declared replanning years;
2. annual public-capital or operating-budget allocation;
3. spring, summer, autumn and winter representative operations;
4. household relocation and cohort growth;
5. firm entry, exit, growth and relocation;
6. weighted labor matching and vacancy/wage/employment feedback;
7. bounded annual market response and price update;
8. development and redevelopment decisions;
9. infrastructure aging;
10. observation and result emission.

This order is a model assumption subject to testing. It is not claimed as a universal causal order. Seasonal operations summarize representative time blocks; the MVP will not simulate every clock hour of every year. An hourly or microscopic adapter can replace a qualified surrogate later without changing the outer contract.

## 4. Randomness and comparisons

Randomness is explicit data. Each world receives mechanism-scoped Philox event tapes derived from a stable identity containing the root seed, world ID, year and mechanism. Policy labels do not alter tape identity. Baseline, policy and ablation runs therefore consume matched exogenous events.

This design supports paired comparisons and prevents the common failure where disabling one mechanism changes every subsequent random draw. JAX also avoids implicit global random state and uses explicit random keys so compiled or parallel execution is not constrained by sequential mutation. The GPU adapter will follow the same principle and consume frozen event tapes rather than introduce an independent random stream. [7]

Exact CPU/GPU floating-point equality is not assumed. The NumPy reference defines semantics; Numba and JAX backends must satisfy frozen-state parity fixtures and aggregate tolerances.

## 5. Calibration, qualification and validation

Three different activities must not be conflated:

### Software validation

Tests establish deterministic replay, strict schemas, process ordering, topology, hard-pin behavior, non-negative capacities and populations, budget accounting, and finite numerical state.

### Mechanism qualification

Synthetic fixtures check whether a mechanism responds in the intended direction. Examples include redevelopment falling as transition cost rises, route cost increasing above capacity, and sensitive cohorts preferring otherwise-equivalent lower-exposure locations. These checks qualify code behavior; they do not calibrate Haidian.

### Empirical calibration and validation

Local parameter estimation and historical backtesting require observed data. UrbanSim documentation similarly distinguishes data assembly, local estimation, calibration and validation over time. [1] In the absence of cleared local building, OD, price, firm, household and environment histories, those parameters remain synthetic, literature-informed or unknown. The model must label them accordingly.

Pattern-oriented modelling is used only when evaluation patterns were specified before the run. ODD 2020 incorporates “purpose and patterns” specifically so patterns can guide model design and evaluation, and requires reporting important observed patterns that the model fails to reproduce. [2][3]

## 6. Deep uncertainty and policy robustness

Long-term land use and growth probabilities are examples of quantities that may not be reliably verifiable. The World Bank review defines deep uncertainty as disagreement or ignorance about models, probability distributions and outcome values, and contrasts prediction-first approaches with stress-testing options across many plausible assumptions. It recommends identifying vulnerabilities, trade-offs and flexibility rather than presenting one purported optimum. [4]

Urban Field Dynamics will therefore separate:

- aleatory variation represented by event tapes;
- parametric uncertainty represented by bounded scenario ensembles;
- structural uncertainty represented by alternate submodels or ablations;
- value uncertainty represented by Pareto analysis and weight sweeps.

A policy is robust only with respect to the declared ensemble and objectives. Robustness is never written as unconditional.

## 7. Transport fidelity ladder

The transport subsystem has two levels:

1. a fast surrogate used inside every stochastic world;
2. an AequilibraE adapter used on selected snapshots and scenarios.

The surrogate provides multimodal graph costs, sparse skims, probabilistic route or mode choice, and a BPR-style capacity feedback. It is deliberately approximate.

AequilibraE provides explicit traffic classes, demand matrices, graph fields, generalized-cost components, volume-delay functions, assignment algorithms and final/blended skims. Its assignment pipeline is therefore suitable as a higher-fidelity oracle once the project has defensible network and OD inputs. [5] Without observed OD, capacities and counts, running a sophisticated assignment algorithm does not make the result calibrated.

## 8. State storage and analysis

NumPy arrays and SciPy sparse matrices hold hot simulation state. Polars and Parquet hold tidy snapshots and event records outside the timestep loop. Polars documents Parquet as a columnar format supporting compression, efficient access and lazy scanning. [8]

DuckDB queries Parquet campaign outputs. Its Spatial extension is installed and loaded separately, so it remains optional until cross-layer SQL geometry operations provide clear value. Core geometry and CRS transformations remain in Shapely and PyProj. [6]

The formal submission receives aggregate JSON, selected traces, GeoJSON, figures and a manifest. Raw campaign artifacts remain in versioned engine releases or declared local artifacts and are not forced into the submission’s 40 MiB package.

## 9. Initial falsifiable hypotheses

The first qualified campaign will test, rather than assume, these hypotheses:

- **H1 — transition inertia:** increasing transition cost reduces and delays redevelopment, all else matched.
- **H2 — accessibility feedback:** an accessibility intervention changes location utility before it changes firm entry, household location and development.
- **H3 — exposure sorting:** when otherwise-equivalent units differ in exposure, sensitive cohorts shift toward lower-exposure units; any macro buffer claim additionally requires a matched no-exposure ablation.
- **H4 — coordination threshold:** a public investment can move a synthetic system across a declared entry/development threshold; hysteresis is claimed only if reversal runs fail to return to the original state distribution.
- **H5 — optionality:** units whose preferred use changes across plausible structural or parameter ensembles receive higher outcome entropy than stable commitment units.

A failed hypothesis is retained as evidence. The model will not tune parameters solely to force the desired morphology.

## 10. Immediate engineering consequences

- Implement the process schedule before coupling submodels.
- Keep the NumPy reference path after adding Numba or JAX.
- Freeze random event tapes independently from policy definitions.
- Run an 8-world engineering smoke before any statistical campaign.
- Pre-register formal campaign configurations and observers.
- Treat provisional geometry as an intake scaffold, not an official constraint.
- Export provenance for every figure and aggregate metric.

## Sources

[1] https://cloud.urbansim.com/docs/general/documentation/urbansim.html
[2] https://bio.uib.no/te/papers/Grimm_2020_The_ODD_protocol_for_describing_agent-based.pdf
[3] https://pubs.usgs.gov/publication/70161783
[4] https://documents1.worldbank.org/curated/en/365031468338971343/pdf/WPS6906.pdf
[5] https://www.aequilibrae.com/develop/python/traffic_assignment/assignment_procedures.html
[6] https://duckdb.org/docs/current/core_extensions/spatial/overview
[7] https://docs.jax.dev/en/latest/random-numbers.html
[8] https://docs.pola.rs/user-guide/io/parquet/
