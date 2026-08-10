# Data requirements and empirical validation gates

Status: requirements only; no listed Haidian dataset has been integrated

## Current evidence class

All current campaigns use deterministic stylised geometry and synthetic parameters. They qualify software contracts and mechanism responses. They do not calibrate, forecast, rank real projects, or support implementation approval.

Increasing the world count reduces Monte Carlo error only for the declared synthetic model. It cannot repair missing observations, misspecified mechanisms, or uncertain policy objectives.

## Required data families

A calibration candidate needs versioned, licensed, time-stamped sources for:

- official study boundaries, coordinate reference systems, parcels, buildings, floor area, age, use, demolition and construction histories;
- planning controls, development rights, protected assets, public ownership and other hard constraints;
- household counts, composition, income, housing demand, tenure, relocation and demographic transitions at privacy-safe resolution;
- firms and workplaces by sector, employment, floor demand, entry, exit, growth and productivity;
- labor-force participation, skills or occupations, wages, reservations, vacancies, hiring flows, workplace locations and commute behavior;
- multimodal networks, service frequencies, fares, capacities, observed OD matrices, travel times and traffic or passenger counts;
- residential and commercial rents, prices, transactions, vacancies and supply additions;
- air, noise, light and heat observations with monitor metadata and seasonal coverage;
- schools, healthcare and other public-service locations, quality measures, capacities, catchments and demand;
- capital and operating budgets, unit costs, maintenance, delivery timing and realised project costs;
- historical policy changes and comparison periods suitable for backtesting.

Synthetic defaults must remain visibly separate from observed values. Every transformed field needs source identity, license, observation period, spatial support, units, missingness treatment and transformation code.

## Privacy and governance

Individual records are not required by the current weighted-cohort design. Inputs should use the minimum spatial and demographic detail necessary for the validation question. Access control, aggregation, disclosure review and retention rules must be defined before protected data enter the pipeline. Secrets and raw restricted records must never enter bounded public artifacts.

## Validation ladder

1. **Software validation:** deterministic replay, invariants, fail-closed schemas and exact serial/parallel checks.
2. **Synthetic mechanism qualification:** directional fixtures, matched ablations, stress matrices and convergence diagnostics.
3. **Calibration candidate:** estimate declared parameters from a documented training period; retain synthetic parameters only when explicitly labelled.
4. **Historical backtest:** initialise before a held-out period and compare aggregate spatial, distributional, transport, market, labor and service patterns.
5. **External validation:** test a different period, geography or policy episode without retuning to the target outcomes.
6. **Decision review:** domain experts examine objectives, harmed groups, tail risks, feasibility, legal constraints and cost assumptions. Model output remains one input rather than an approval.

Advancing a gate requires written acceptance criteria and retained failures. Good fit on one aggregate cannot compensate for severe errors in subgroup, spatial or capacity outcomes.

## Minimum reporting for any calibrated result

Report source versions, exclusions, imputation, parameter-estimation method, train/test periods, observed-versus-simulated diagnostics, sensitivity to plausible alternatives, unsupported mechanisms, uncertainty decomposition and all departures from the preregistered campaign.

Until those requirements are met, use the phrase **synthetic mechanism qualification** and avoid empirical confidence, prediction, optimisation, recommendation or government-endorsement claims.
