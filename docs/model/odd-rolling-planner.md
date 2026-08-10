# ODD description: rolling trigger planner

Status: implemented reference slice, schema version 0.6.0

The public-policy phase now supports either legacy fixed-year activation or declared state triggers evaluated only at configured replanning years. A trigger may observe mean rent, mean accessibility, mean environment quality, maximum housing occupancy, or maximum employment occupancy and compare it with a non-negative threshold using `>=` or `<=`. Multiple triggers combine with explicit `all` or `any` semantics.

The intervention year is the earliest eligible year. Once activated, an intervention is applied exactly once and `WorldResult.policy_activation_year` records the actual year. If no trigger is declared, behavior remains exactly the previous fixed intervention-year contract. If no trigger is met, the policy remains inactive.

Trigger evaluation uses current endogenous state at the start of the replanning phase. Trigger definitions and policy identity do not enter exogenous Philox event-tape identity, preserving matched counterfactuals.

This is a deterministic activation mechanism, not an optimizer and not evidence that its thresholds are appropriate for Haidian. Fiscal budgets, policy learning, multi-stage interventions, and calibrated trigger values remain future work.
