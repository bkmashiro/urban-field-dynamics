# Matched policy-intensity sweep contract

Status: implemented experiment slice, schema version 0.10.0

A sweep clones one declared campaign arm over ordered intensity levels from zero to one. All levels retain the same world IDs, mechanism switches, transition-inertia setting, schedule, and policy-independent event tapes.

Intensity zero neutralizes additive deltas and sets every capacity or time multiplier to one. Intensity one reproduces the target policy exactly except for its experiment ID. Intermediate additive effects scale linearly; multipliers interpolate around one rather than being multiplied directly by intensity.

The sweep currently summarizes redevelopment, final accessibility, final environmental quality, and final rent. Threshold diagnostics consume the ordered response and return adjacent crossing brackets only.

A one-world scaled P3 sweep at intensities 0, 0.25, 0.5, 0.75, and 1 produced accessibility responses 0.522350, 0.522754, 0.523167, 0.523785, and 0.525591. Mean rent was nearly flat and slightly higher at full intensity. For a demonstration threshold of 0.524, the crossing bracket was 0.75–1.0. The threshold is an engineering example, not a planning standard, and one world is not statistical evidence.
