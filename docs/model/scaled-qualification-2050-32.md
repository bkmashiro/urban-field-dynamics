# Scaled 2026–2050 synthetic qualification at 32 worlds

Status: current-engine mechanism qualification; not calibration, forecast or implementation advice

## Frozen execution

- Engine source: signed commit `64a8e7df522e82e8b0e6ead0edf0063d79955350`.
- Runtime authority: Python 3.12.
- Campaign: `scaled-integrated-2050-qualification-32`.
- Matrix: 32 matched worlds × 13 policy/ablation arms = 416 runs.
- Horizon: 2026–2050.
- Export: 32.58 seconds; independent full replay: 31.13 seconds with four workers.
- Bounded artifact: 25,243,317 bytes across eight hash-manifested derived files plus the manifest.
- `provenance.json` pins the source revision; replay did not read Git.

## P0–P3 ensemble outcomes

All quantities are synthetic model units. Public cost is cumulative synthetic spend, not currency.

| Arm | Accessibility | Environment | Rent surrogate | Unemployment | Public cost | Peak transport utilisation | Final service unmet demand |
|---|---:|---:|---:|---:|---:|---:|---:|
| P0 | 0.522350 | 0.600982 | 5.066399 | 0.036015 | 20.315 | 0.568847 | 151.399 |
| P1 | 0.524997 | 0.607438 | 5.061168 | 0.035906 | 236.316 | 0.361551 | 145.469 |
| P2 | 0.522350 | 0.618104 | 5.067195 | 0.036134 | 182.315 | 0.568847 | 151.727 |
| P3 | 0.524848 | 0.624560 | 5.083809 | 0.042397 | 452.316 | 0.361551 | 127.138 |

Every P0–P3 annual market response converged under the declared fail-closed solver. No arm exceeded the declared synthetic budget limits. These checks validate execution contracts, not realism of the limits.

## Matched diagnostics

Effects are comparator minus baseline. Intervals are descriptive normal-approximation intervals over matched synthetic worlds.

| Comparison | Mean delta | 95% interval | Harmed worlds |
|---|---:|---:|---:|
| P1 vs P0 accessibility | +0.002647 | [+0.002244, +0.003050] | 2/32 |
| P2 vs P0 environment | +0.017122 | point-identical | 0/32 |
| P3 vs P0 rent | +0.017409 | [+0.009115, +0.025704] | 27/32 |
| Agglomeration accessibility effect | +0.001185 | [+0.000510, +0.001860] | 5/32 |
| Transport-attraction accessibility effect | +0.024023 | [+0.023571, +0.024475] | 0/32 |
| Cohort-dynamics employment effect | +10.266 | [+1.849, +18.684] | 9/32 |
| Labor-matching rent effect | -0.013534 | [-0.018045, -0.009023] | 2/32 |
| Service-provision effect | +0.139659 | [+0.139258, +0.140061] | 0/32 |
| Inertia effect on redevelopment | +45.750 | [+44.806, +46.694] | 0/32 |

A positive P3 rent delta is adverse under the declared rent-minimisation direction. The result therefore does not support a claim that the integrated policy improves rent outcomes.

## Equity and decision evidence

P3 reduced the service-access gap from 0.293718 under P0 to 0.105842 and the commute gap from 2.739007 to 0.452903. It increased the unemployment-rate gap from 0.076256 to 0.091647 and the rent-burden gap from 0.051170 to 0.051862.

Group-level matched tails are material. Under P3, family, accessibility-needs and research-talent rent burden was worse in 26/32 worlds; service-worker rent burden was worse in 25/32 and student rent burden in 24/32. Older-adult relocation was worse in 21/32 worlds, and older-adult effective service was worse in 17/32.

P0, P1, P2 and P3 were all non-dominated across the 13 declared objectives. The artifact reports 15 objective-specific leverage ratios and 116 group-tail diagnostics without a hidden scalar score. P3 improved synthetic service unmet demand by 24.262 relative to P0 at 432.001 incremental cost units, while its rent and unemployment leverage numerators were adverse.

## Qualification decision

Proceed to a 64-world matched rerun to test 32-to-64 stability, especially cohort employment heterogeneity, P3 rent harm, agglomeration, and group tails. Do not jump directly to 128 worlds: more Monte Carlo samples cannot resolve missing empirical data or structural uncertainty.

No official boundary, parcel, building, ownership, OD, capacity, count, rent, firm, wage, environmental, service or public-finance dataset was used. This document is synthetic mechanism qualification only.
