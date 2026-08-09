from urban_field_dynamics.agents import (
    FirmCohortSpec,
    HouseholdCohortSpec,
    LocationState,
    allocate_firms,
    allocate_households,
)
from urban_field_dynamics.contracts import EvidenceStatus


def location(unit_id: str, *, accessibility: float = 0.5) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=accessibility,
        rent=10.0,
        jobs=0.0,
        households=0.0,
        housing_capacity=100.0,
        employment_capacity=100.0,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def household(cohort_id: str) -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id=cohort_id,
        population=60.0,
        initial_unit_id="unit-aa",
        income=40.0,
        housing_demand_per_person=1.0,
        accessibility_weight=1.0,
        jobs_weight=0.0,
        environment_weight=0.0,
        rent_burden_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def firm(cohort_id: str) -> FirmCohortSpec:
    return FirmCohortSpec(
        cohort_id=cohort_id,
        employees=60.0,
        initial_unit_id="unit-aa",
        floor_demand_per_employee=1.0,
        accessibility_weight=1.0,
        agglomeration_weight=0.0,
        rent_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def test_household_allocation_is_exactly_replayable_and_capacity_constrained() -> None:
    cohorts = (household("cohort-bb"), household("cohort-aa"))
    locations = (location("unit-bb"), location("unit-aa"))

    first = allocate_households(
        cohorts,
        locations,
        root_seed=20260810,
        world_id=7,
        year=2026,
        taste_shock_scale=0.2,
    )
    replay = allocate_households(
        tuple(reversed(cohorts)),
        tuple(reversed(locations)),
        root_seed=20260810,
        world_id=7,
        year=2026,
        taste_shock_scale=0.2,
    )

    assert first == replay
    assert set(first.assignments) == {"cohort-aa", "cohort-bb"}
    assert len(set(first.assignments.values())) == 2
    assert all(state.households == 60.0 for state in first.locations)


def test_policy_state_changes_choices_without_changing_household_taste_tape() -> None:
    cohorts = (household("cohort-aa"),)
    baseline = (location("unit-aa", accessibility=0.1), location("unit-bb", accessibility=0.2))
    investment = (
        location("unit-aa", accessibility=0.9),
        location("unit-bb", accessibility=0.2),
    )

    p0 = allocate_households(
        cohorts,
        baseline,
        root_seed=20260810,
        world_id=3,
        year=2026,
        taste_shock_scale=0.0,
    )
    p1 = allocate_households(
        cohorts,
        investment,
        root_seed=20260810,
        world_id=3,
        year=2026,
        taste_shock_scale=0.0,
    )

    assert p0.taste_shocks == p1.taste_shocks
    assert p0.assignments == {"cohort-aa": "unit-bb"}
    assert p1.assignments == {"cohort-aa": "unit-aa"}


def test_firm_allocation_updates_jobs_and_uses_separate_mechanism_tape() -> None:
    result = allocate_firms(
        (firm("firm-aa"),),
        (location("unit-aa"), location("unit-bb")),
        root_seed=20260810,
        world_id=1,
        year=2026,
        taste_shock_scale=0.2,
    )
    household_result = allocate_households(
        (household("firm-aa"),),
        (location("unit-aa"), location("unit-bb")),
        root_seed=20260810,
        world_id=1,
        year=2026,
        taste_shock_scale=0.2,
    )

    chosen = result.assignments["firm-aa"]
    by_id = {state.unit_id: state for state in result.locations}
    assert by_id[chosen].jobs == 60.0
    assert result.taste_shocks != household_result.taste_shocks
