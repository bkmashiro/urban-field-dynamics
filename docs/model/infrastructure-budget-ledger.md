# Public budget and infrastructure-capacity ledger

Status: implemented synthetic accounting and constraint slice

## Purpose

The ledger makes public-resource assumptions explicit. It does not estimate real Haidian costs or budgets. All amounts in the scaled fixture are dimensionless synthetic units.

## Cost declarations

Each policy declares one activation capital cost and one annual operating cost. The ledger also declares a public cost per realised redevelopment transition.

Operating cost begins in the year after activation. Annual and cumulative limits are checked at every allocation. Redevelopment cost is checked after the realised transition count is known.

## Failure and rationing semantics

`fail_closed` raises `BudgetExceededError` before an unfunded action can produce a result. Operating and redevelopment costs are always fail closed.

`proportional` applies only to a divisible activation capital package. Additive deltas scale linearly; capacity and time multipliers interpolate around neutral value one.

## Capacity observers

Each annual trace records edge flow/capacity ratios, overloaded edge IDs, service demand/capacity ratios, and unmet service demand.

Transport overload is handled by the declared BPR congestion rule; service overload is handled by the declared crowding rule. The ledger observes both instead of silently clipping demand.

## Evidence boundary

Summary evidence includes cumulative spend, peak transport utilisation, and final service unmet demand. Representative worlds include the full annual ledger.

These values support mechanism qualification and comparative stress tests only. They are not empirical cost estimates, approved budgets, or implementation recommendations.
