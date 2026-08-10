# ODD description: weighted labor matching

Status: implemented synthetic mechanism slice, schema version 0.11.0

## Purpose and boundary

The labor module connects weighted household labor supply, weighted firm vacancy demand, commuting accessibility, and annual firm adjustment. It does not represent individual workers, establishments, contracts, or observed Haidian employment.

## State

Household cohorts declare:

- labor-force share;
- one skill group;
- reservation wage;
- current location and synthetic population weight.

Firm cohorts declare:

- labor-demand share;
- one skill requirement;
- offered wage;
- current location and synthetic employee weight.

The scaled fixture's shares, skills, wages, commute limit, wage adjustment, and vacancy-retention rate are synthetic mechanism parameters, not estimates.

## Annual process

`LABOR_MATCHING` runs after firm dynamics and before market clearing.

1. Supply is population times labor-force share.
2. Demand is employees times labor-demand share.
3. Skills must match, except that `general` is an explicit wildcard.
4. Offered wage must satisfy the reservation wage.
5. A path must exist within the declared commute limit.
6. Divisible flows are allocated in deterministic descending net-wage order with stable ID tie-breaking.
7. Unemployment, vacancies, wages, commute minutes, and flows are observed.
8. Vacancy pressure adjusts next-year offered wages. Unfilled jobs are retained only at the declared retention rate; employee and location-job state are updated together.

The greedy flow is a transparent bounded surrogate, not a claim of equilibrium optimality.

## Transport coupling

Transport assignment still uses only declared travel demand. Labor matching receives an all-reachable-node generalized-cost skim computed from the resulting congested edge times. The skim does not inject extra flow. It prevents moved cohorts from becoming falsely disconnected merely because their new OD pair was absent from initial demand.

## Reproducibility and ablation

The mechanism consumes no random draws. It therefore cannot change Philox event identity. `p3-no-labor-matching` disables matching, wage adjustment, vacancy attrition, and labor traces while preserving every other mechanism and matched world ID.

## Evidence

Campaign summaries expose final unemployment, vacancy, commute, and firm-wage means. Equity evidence reports group unemployment and commute gaps when labor traces exist; disabled arms use `null`, not zero. Bounded representative worlds include final labor state and wages. Qualification diagnostics compare the downstream rent response with and without labor matching without treating either direction as pre-approved.

## Limitations

No observed wages, labor-force participation, occupations, vacancies, workplace counts, commute matrices, job-search frictions, hiring costs, worker transitions, or remote-work behavior are calibrated. Results remain synthetic mechanism qualification and are not Haidian employment forecasts.
