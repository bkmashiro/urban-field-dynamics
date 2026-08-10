# ODD description: weighted cohort and market slice

Status: implemented reference slice, schema version 0.2.0

This document describes the executable household, firm, public-service, and annual rent-feedback layer added after the redevelopment qualification slice. Transport and environmental systems are documented in their later ODD slices.

## 1. Purpose and evidence boundary

The slice tests whether weighted cohorts can respond to accessibility, jobs, environmental quality, public-service quality and congestion, rent, agglomeration, and finite capacity while preserving matched stochastic identity across policy arms.

Every cohort and location input carries an evidence status. Current fixtures are synthetic. A cohort represents a population or establishment class, not a real person or company, and the slice is not calibrated to Haidian observations.

## 2. Entities and state

### Household cohort

A household cohort has stable identity, population weight, current location, income, per-person housing demand, and explicit non-negative utility weights for accessibility, jobs, environment, effective service access, and rent burden.

### Firm cohort

A firm cohort has stable identity, employee weight, current location, per-employee floor demand, and explicit non-negative utility weights for accessibility, agglomeration, and rent.

### Location

A location records accessibility, shared rent, jobs, households, housing capacity, employment capacity, environment quality, service quality, optional service capacity, and evidence status. Locations can either match spatial-unit IDs or cover them through an explicit, exhaustive, non-overlapping `location_members` mapping.

## 3. Annual process order

The authoritative schedule remains:

1. rolling public policy;
2. representative seasonal operations;
3. household relocation;
4. firm dynamics;
5. market clearing;
6. redevelopment;
7. infrastructure aging;
8. observation.

Household relocation, firm dynamics, market clearing, policy, redevelopment, and aging now mutate state. Seasonal operations and observation remain placeholders.

Before each annual relocation, the runner removes each simulated cohort from its current location and reallocates it once. This prevents population or jobs from being counted repeatedly across years.

## 4. Location choice

Household utility is:

```text
accessibility_weight × accessibility
+ jobs_weight × jobs / employment_capacity
+ environment_weight × environment_quality
+ service_weight × service_quality × min(1, service_capacity / prospective demand)
- rent_burden_weight × rent / income
+ matched taste shock
```

Firm utility is:

```text
accessibility_weight × accessibility
+ agglomeration_weight × jobs / employment_capacity
- rent_weight × rent / 100
+ matched taste shock
```

Cohorts are allocated in stable ID order. A location is feasible only when it has sufficient remaining housing or employment capacity. Ties are deterministic.

## 5. Stochasticity

Household and firm taste tapes are separate NumPy Philox mechanisms:

- `household-location-taste`;
- `firm-location-taste`.

Tape identity contains root seed, world ID, year, and mechanism. It excludes policy identity. Spatial policy can therefore alter accessibility and choices without changing exogenous tastes in matched counterfactuals.

## 6. Market clearing

The reference market uses a bounded annual tâtonnement update. Housing and employment occupancy are combined with declared weights that must sum to one. Rent changes according to deviation from target occupancy and cannot fall below a declared floor.

This is a qualification mechanism, not a claim that one shared rent index reproduces residential and commercial markets. Separate tenure, floor-space, and price submarkets remain future work.

## 7. Current qualification patterns

Automated tests establish that:

- strict contracts reject unknown fields;
- rent-sensitive households can prefer an affordable location over a more accessible one;
- household and firm choices obey remaining capacity;
- firms can prefer agglomeration when capacity allows;
- allocation is invariant to input ordering and exactly replayable;
- household and firm mechanisms consume separate event tapes;
- per-unit accessibility policy changes choices without changing matched taste tapes;
- annual relocation does not duplicate weighted population or employment;
- finite service capacity can redirect a service-sensitive cohort, and planner capacity expansion can change that choice;
- service provision can be disabled independently in matched ablation;
- high occupancy raises rent, low occupancy lowers it, and the rent floor is preserved.

## 8. Not yet implemented

- cohort births, deaths, splitting, merging, entry, or exit;
- explicit labour matching or commuting OD;
- separate housing, commercial floor-space, and land markets;
- endogenous service-capacity investment, fiscal budgets, and facility aging (current capacity changes are declared policy interventions);
- multimodal assignment and congestion feedback;
- seasonal air, noise, light, heat, or hydrology fields;
- calibrated local household, firm, rent, capacity, or mobility inputs.
