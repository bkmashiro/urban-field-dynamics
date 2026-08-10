# Integrated synthetic qualification at 64 and 128 worlds

Status: mechanism qualification only; not a formal policy result

Engine evidence was generated from the three-unit synthetic integrated fixture and fully replay-verified. No empirical Haidian inputs were used.

## Executed campaigns

- 64 matched worlds × 10 arms = 640 runs; export and full replay: 7.061 s.
- 128 matched worlds × 10 arms = 1,280 runs; export and full replay: 11.273 s.
- Arms: P0–P3 plus no-inertia, no-agglomeration, no-transport-attraction, no-seasonality, no-environmental-exposure, and no-public-coordination.
- Prefix diagnostics: 8, 16, 32, 64, and 128 worlds.

Runtime is a local engineering measurement, not a portable performance guarantee.

## 128-world matched diagnostics

| Comparison | Mean paired delta | 95% descriptive interval | Harmed worlds | 64→128 mean change | Interpretation |
|---|---:|---:|---:|---:|---|
| P1 vs P0 accessibility | -0.015507 | [-0.044664, 0.013650] | 40/128 | 0.012092 | unresolved; interval crosses zero and sign differed from the 8-world canary |
| P2 vs P0 environment quality | +0.022050 | [0.022050, 0.022050] | 0/128 | 0 | deterministic fixture effect |
| P3 vs P0 rent | -0.140900 | [-0.152568, -0.129232] | 0/128 | 0.008643 | stable direction in this fixture; lower rent is treated as favourable only for this diagnostic |
| Inertia effect, no-inertia minus P3 redevelopment | +2.789062 | [2.714851, 2.863274] | 0/128 | 0.070312 | mechanism is strongly distinguishable |
| Agglomeration effect on accessibility | +0.012738 | [-0.009692, 0.035168] | 25/128 | 0.007077 | unresolved; interval crosses zero |
| Transport-attraction effect on accessibility | +0.079598 | [0.050195, 0.109001] | 41/128 | 0.014153 | positive mean but heterogeneous and not yet stable |
| Seasonality effect on heat range | +0.494000 | [0.494000, 0.494000] | 0/128 | 0 | exact fixture invariant |
| Environmental-exposure effect on quality | +0.124445 | [0.124445, 0.124445] | 0/128 | 0 | exact fixture invariant |
| Public-coordination effect on accessibility | -0.015507 | [-0.044664, 0.013650] | 40/128 | 0.012092 | mirrors unresolved P1 effect in the current fixture |

Intervals are normal-approximation descriptive intervals over matched synthetic worlds. They are not empirical confidence intervals about Haidian.

## Decision

Do not promote this fixture to a 128–512 world formal campaign. The model has only three spatial units, a small cohort set, and stylised OD and capacity inputs. Increasing world count further would reduce Monte Carlo error while leaving structural uncertainty untouched.

The next qualification gate is structural:

1. generate 1,000–2,000 deterministic stylised spatial units with explicit adjacency and focus-zone labels;
2. add morphology observers and spatially resolved transition distributions;
3. rerun 8-world invariants and profile cost;
4. only then select a new 32–64 world qualification size.
