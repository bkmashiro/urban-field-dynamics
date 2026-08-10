# Equity observer contract

Status: implemented observer-only slice, schema version 0.8.0

Household cohorts may declare an `equity_group`. The observer uses existing synthetic cohort income and housing demand; it does not introduce a second income model or alter household utility.

For every arm and matched world, outcomes are first weighted by final cohort population within each declared group. Group values are then averaged equally across worlds, preventing a high-growth world from dominating the ensemble. Reported fields are accessibility, environmental quality, effective service access, rent burden, relocation rate, and mean population.

Effective service access combines final service quality with a capacity-to-demand factor. Rent burden is the location rent multiplied by per-person housing demand and divided by cohort income. Both are dimensionless synthetic observers until units and local data are calibrated.

Arm summaries include max-minus-min group gaps for all five outcome dimensions. A lower gap is not automatically a welfare improvement: it can result from improving the worst group, harming the best group, or both. Pareto and tail-harm diagnostics must inspect levels and gaps together.

`equity-summary.json` is part of the bounded evidence package and its SHA-256 manifest. Verification reruns the full campaign and rebuilds the equity bytes; stale or tampered summaries fail closed.
