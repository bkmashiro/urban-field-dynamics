# Decision diagnostics contract

Status: implemented observer-only slice

## Pareto analysis

P0–P3 are compared without a scalar score. Each objective explicitly declares maximize or minimize semantics and an optional numerical tolerance. One arm dominates another only when it is no worse on every objective and strictly better on at least one objective beyond tolerance.

The default bundle includes accessibility, environment, rent, and group gaps. Labor and infrastructure objectives are added only when every P0–P3 arm has those observers. Mechanism ablations are not policy candidates.

A nondominated arm is not automatically recommended. The Pareto front only removes candidates that are unambiguously worse under the declared objective set.

## Tail harm

Every matched qualification comparison reports harmed-world count and fraction, worst welfare-aligned harm, and the 90th percentile harm. Harm direction follows the metric declaration: a positive rent delta is harmful when lower rent is preferred, while a negative accessibility delta is harmful when higher accessibility is preferred.

Group tail harm is reported separately by policy arm, equity group, metric, and matched world. Missing optional observers are omitted rather than represented as zero.

## Cost leverage

Each available policy/objective pair reports its objective improvement divided by incremental cumulative synthetic public spend relative to P0. Baseline cost, arm cost, incremental denominator, direction, and denominator provenance remain explicit.

Leverage ratios are not combined into a score. If incremental cost is non-positive, the ratio is `null` and the status records why division was refused.

## Tipping brackets

Ordered sweep results may be checked for threshold crossings. The diagnostic returns adjacent level brackets whose responses cross or touch the declared threshold. It does not interpolate an exact tipping value from sparse or stochastic observations.

## Reproducible evidence

`decision-diagnostics.json` is included in the bounded evidence manifest. Replay verification rebuilds the Pareto and tail-harm bundle from the frozen campaign result. These diagnostics remain synthetic until objective units, thresholds, and policy arms are locally grounded.
