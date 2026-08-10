# Scaled 2026–2050 synthetic qualification at 64 worlds

Status: current-engine mechanism qualification; not calibration, forecast or implementation advice

## Frozen execution

- Engine source: signed commit `64a8e7df522e82e8b0e6ead0edf0063d79955350`.
- Campaign: `scaled-integrated-2050-qualification-64`.
- Matrix: 64 matched worlds × 13 policy/ablation arms = 832 runs.
- Export: 81.79 seconds; independent full replay: 78.21 seconds with four workers.
- Bounded artifact: 25,265,721 bytes; all eight derived files and `provenance.json` are manifest-hashed.
- Python 3.12 is authoritative and replay did not read Git.

## P0–P3 ensemble outcomes

All values are synthetic model units. Public cost is not currency.

| Arm | Accessibility | Environment | Rent surrogate | Unemployment | Public cost | Peak transport utilisation | Final service unmet demand |
|---|---:|---:|---:|---:|---:|---:|---:|
| P0 | 0.522350 | 0.600982 | 5.067292 | 0.044887 | 20.310 | 0.568847 | 149.855 |
| P1 | 0.525105 | 0.607438 | 5.058647 | 0.044524 | 236.311 | 0.361551 | 146.595 |
| P2 | 0.522350 | 0.618104 | 5.068103 | 0.044947 | 182.310 | 0.568847 | 150.019 |
| P3 | 0.524905 | 0.624560 | 5.078088 | 0.047470 | 452.311 | 0.361551 | 126.973 |

All annual market solves converged. No declared synthetic budget limit failed. These are execution and mechanism checks, not evidence that real capacities, costs or service demand have been represented correctly.

## 32-to-64 matched convergence

| Comparison | 64-world mean | 64-world 95% interval | Harmed worlds | Mean change from 32 |
|---|---:|---:|---:|---:|
| P1 vs P0 accessibility | +0.002755 | [+0.002511, +0.002999] | 2/64 | +0.000108 |
| P2 vs P0 environment | +0.017122 | point-identical | 0/64 | 0 |
| P3 vs P0 rent | +0.010796 | [+0.002564, +0.019027] | 50/64 | -0.006613 |
| Agglomeration accessibility effect | +0.001289 | [+0.000880, +0.001697] | 9/64 | +0.000104 |
| Transport-attraction accessibility effect | +0.024080 | [+0.023789, +0.024371] | 0/64 | +0.000057 |
| Cohort-dynamics employment effect | +10.774 | [+4.463, +17.085] | 18/64 | +0.508 |
| Labor-matching rent effect | -0.012858 | [-0.016995, -0.008721] | 4/64 | +0.000676 |
| Service-provision effect | +0.139672 | [+0.139389, +0.139956] | 0/64 | +0.000013 |
| Inertia effect on redevelopment | +46.422 | [+45.725, +47.119] | 0/64 | +0.672 |

No selected comparison changed direction from 32 to 64 worlds. The P3 rent mean moved within overlapping intervals and remained adverse under the declared rent-minimisation direction.

## Distributional trade-offs

P3 reduced the service-access gap from 0.309124 under P0 to 0.118191 and the commute gap from 3.235387 to 0.658388. It increased the unemployment-rate gap from 0.085003 to 0.098667 and the rent-burden gap from 0.051438 to 0.052221.

P3 rent burden was worse for families, accessibility-needs and research-talent groups in 49/64 worlds, service workers in 48/64, students in 47/64 and older adults in 42/64. Older-adult relocation was worse in 40/64 worlds and effective service was worse in 37/64.

P0, P1, P2 and P3 remained non-dominated across all 13 declared objectives. The model therefore does not select one policy. P3 combines accessibility, environment, commute and service-capacity benefits with higher synthetic cost, rent, unemployment and several group harms.

## Decision on 128 worlds

Do not run a 128-world campaign for this pre-PR synthetic phase. The 32-to-64 check retained directions, overlapping uncertainty ranges and similar harmed-world fractions. Another doubling would reduce Monte Carlo error for the same stylised structure but would not resolve missing observations, synthetic objectives, simplified labor and market behavior, or uncertain public costs.

A future 128–512-world campaign is justified only after an empirical calibration or a newly declared structural experiment changes the validation question. The required data and gates are listed in `docs/research/data-requirements-and-validation.md`.

This evidence must not be described as a Haidian prediction, policy ranking, budget estimate, project recommendation, implementation approval or government endorsement.
