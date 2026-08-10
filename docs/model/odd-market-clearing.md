# ODD description: bounded annual market response

Status: implemented synthetic market-feedback slice

## Purpose

The module converts observed annual housing and employment occupancy pressure into a bounded next-rent target for each synthetic location.

It is a shadow-rent feedback surrogate. It is not a same-year Walrasian equilibrium, transaction market, lease model, or empirical hedonic rent model.

## Annual target

Housing and employment occupancy are weighted by declared coefficients. Deviation from target occupancy determines a bounded annual rent multiplier.

Minimum and maximum rents plus maximum annual change are explicit bounds. Cohort demand responds to the resulting rent during the following year's location-choice phase.

## Solver and failure

A deterministic relaxed iteration approaches the declared target. The trace records the
relative residual observed before each iteration update. `max_residual` is recomputed from
the final post-update rents, so after an exhausted iteration budget it can be smaller than
the last history entry. The result also records convergence and binding rent bounds.

`require_convergence` raises `MarketClearingError` after the declared iteration bound. The scaled fixture enables this fail-closed mode.

## Evidence boundary

Campaign summaries report convergence fraction, mean iterations, and mean peak residual. Representative worlds retain every annual market trace.

All parameters and outputs remain synthetic until calibrated against observed housing, employment, and rent evidence.
