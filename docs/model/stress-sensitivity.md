# Matched stress and sensitivity matrices

Status: implemented synthetic robustness evidence

## Separation from policy

A stress scenario transforms declared exogenous campaign inputs. It does not change policy arms, mechanism switches, root seed, world IDs, or entity-scoped event-tape keys.

Common entities must retain identical random values across scenarios. Birth/death can change later entity sets, so identity is checked on the entity intersection rather than row position.

## Declared transforms

The contract can perturb household and firm growth, firm death and birth, edge capacity, seasonal heat, public-service capacity, and annual/cumulative public budgets.

The standard scaled matrix is one-at-a-time: baseline, growth pressure, firm contraction, transport disruption, heat stress, and service constraint. It evaluates P0–P3 only.

## Evidence

For each scenario/arm/metric, the export stores ensemble means. It also stores matched scenario shifts and policy effects, welfare direction, harmed-world count/fraction, and worst harm.

`stress-config.json`, `stress-evidence.json`, and `manifest.json` are canonical, hashed, bounded, and replay-verified byte for byte. Raw world results are not exported.

## Interpretation boundary

One-at-a-time scenarios expose local mechanism sensitivity, not a probability distribution over futures. Eight worlds are a canary; larger matrices need explicit qualification labels.

All scenario magnitudes are synthetic engineering assumptions, not observed Haidian shock distributions or forecasts.
