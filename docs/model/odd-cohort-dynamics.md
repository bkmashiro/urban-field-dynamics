# ODD description: weighted cohort lifecycle dynamics

Status: implemented synthetic mechanism slice, schema version 0.7.0

## Entities and state

Households and firms remain weighted cohorts, not asserted person or establishment records. Household state adds annual population evolution. Firm state adds incumbent survival, employee expansion or contraction, and births from declared prototypes.

## Random identity

Household growth, firm death, firm expansion, and firm birth use separate mechanism-scoped Philox event tapes. Cohort-level shocks also carry an `entity_id`; adding or removing another cohort therefore cannot shift a surviving cohort's random stream. Policy and ablation identity are absent from every tape.

## Annual order

1. Release each cohort's previous occupancy from its assigned location.
2. Evolve household population or firm lifecycle state.
3. Allocate the evolved cohorts against explicit remaining capacity.
4. Fail closed if no feasible location can absorb a cohort.
5. Record terminal cohort weights, births, deaths, shocks, and assignments.

Firm birth IDs are deterministic `prototype-year` identities. A collision is an error rather than an implicit overwrite.

## Ablation

`cohort_dynamics_enabled` independently disables growth, birth, death, and expansion while preserving the other mechanisms. Shared incumbent location-taste shocks remain exactly matched. Birth cohorts and dead cohorts are absent by definition and are not supplied fake random events merely to equalize dictionary shape.

## Current synthetic scaled parameters

The scaled fixture uses 0.2% mean household growth with ±0.2% annual variation, 1% mean incumbent firm growth with ±2% variation, 1% annual firm death probability, and two 5% annual birth prototypes. These values are synthetic stress inputs, not local demographic or business calibration.

A one-world 2026–2050 execution completed without capacity failure. In that realization P3 ended with weighted population 241.41, weighted employment 175.88, five births, and four deaths; the no-dynamics arm remained at population 230 and employment 180. These are engineering observations, not policy evidence.
