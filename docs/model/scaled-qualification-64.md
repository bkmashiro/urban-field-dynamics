# Scaled integrated synthetic qualification at 64 worlds

Status: structural and mechanism qualification; not a Haidian forecast or formal 2026–2050 policy campaign

## Executed configuration

- 1,200 synthetic redevelopment cells;
- 48 explicit agent, market, transport, and environment zones;
- six household cohorts and six firm cohorts;
- walk, cycle, road, bus, and corridor rail;
- P0–P3 plus six mechanism ablations;
- 2026–2028 horizon;
- 64 matched worlds and 640 runs.

The bounded package reran the full campaign during verification. Export plus replay took approximately 6 minutes 52 seconds on the recorded local environment. The package was 2.9 MiB. Full traces remain local and untracked.

## Paired diagnostics

Effects are comparator minus baseline. Intervals are descriptive normal-approximation intervals over matched synthetic worlds.

| Comparison | Mean delta | 95% interval | Harmed worlds |
|---|---:|---:|---:|
| P1 vs P0 accessibility | +0.003193 | [0.003125, 0.003260] | 0/64 |
| transport-attraction mechanism | +0.024415 | [0.024007, 0.024822] | 0/64 |
| P2 vs P0 environment quality | +0.017122 | point-identical in fixture | 0/64 |
| environmental-exposure mechanism | +0.124560 | point-identical in fixture | 0/64 |
| no-inertia vs P3 redevelopment count | +95.718750 | [94.599445, 96.838055] | 0/64 |
| seasonality heat range | +0.547765 | point-identical in fixture | 0/64 |
| agglomeration accessibility effect | +0.000393 | [-0.000189, 0.000975] | 4/64 |
| P3 vs P0 rent | +0.000023 | [-0.000047, 0.000094] | 14/64 |

The 32-to-64 mean changes were small for the non-zero qualified mechanisms. Agglomeration and rent intervals cross zero and do not support directional claims.

## Decision classifications

Across all selected policy and ablation arms, the transparent probability rule classified:

- 974 Commitment units: 825 robust transition and 149 robust keep;
- 144 Trigger units;
- 82 Optionality units.

These are synthetic cross-world classifications. Focus-zone and corridor labels are observers only and never enter initial physical or economic state.

## Interpretation boundary

The qualification supports implementation and mechanism observability, not empirical validity. It uses no official Haidian polygon, parcel, building, ownership, OD, rent, environmental monitoring, or historical change dataset. It must not be cited as a land-use recommendation, site prediction, implementation approval, or government endorsement.

The horizon is only 2026–2028. Before a formal 2026–2050 campaign, the engine needs world-level parallel execution and measured profiling; simply multiplying the current replay duration would be wasteful.
