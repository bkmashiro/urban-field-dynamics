# Matched policy-intensity sweep contract

Status: implemented experiment slice, schema version 0.10.0

A sweep clones one declared campaign arm over ordered intensity levels from zero to one. All levels retain the same world IDs, mechanism switches, transition-inertia setting, schedule, and policy-independent event tapes.

Intensity zero neutralizes additive deltas and sets every capacity or time multiplier to one. Intensity one reproduces the target policy exactly except for its experiment ID. Intermediate additive effects scale linearly; multipliers interpolate around one rather than being multiplied directly by intensity.

The sweep currently summarizes redevelopment, final accessibility, final environmental quality, and final rent. Threshold diagnostics consume the ordered response and return adjacent crossing brackets only.

A one-world scaled P3 sweep at intensities 0, 0.25, 0.5, 0.75, and 1 produced accessibility responses 0.522350, 0.522754, 0.523167, 0.523785, and 0.525591. Mean rent was nearly flat and slightly higher at full intensity. For a demonstration threshold of 0.524, the crossing bracket was 0.75–1.0. The threshold is an engineering example, not a planning standard, and one world is not statistical evidence.

## Bounded evidence

`urban-field scaled-sweep` exports the full sweep config, mean and per-world responses, declared
threshold status, crossing brackets, and a SHA-256 manifest. `urban-field verify-sweep` checks every
hash, reruns the complete matched sweep, revalidates random identity, and rebuilds each artifact byte.

The 8-world 2026–2050 engineering canary produced 40 runs per execution and was then fully replayed.
The bounded package was 1.1 MiB. Mean synthetic responses across intensities 0, 0.25, 0.5, 0.75,
and 1 were:

- accessibility: 0.522350, 0.522754, 0.522912, 0.523207, 0.524516;
- environment quality: 0.600982, 0.606773, 0.612665, 0.618613, 0.624560;
- rent: 5.079628, 5.082970, 5.083626, 5.091030, 5.078114.

The deliberately synthetic demonstration threshold 0.524 was bracketed only between intensity 0.75
and 1.0. No interpolation or planning-standard claim is made, and eight worlds remain canary evidence.
