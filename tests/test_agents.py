import pytest
from pydantic import ValidationError

from urban_field_dynamics.agents import (
    FirmCohortSpec,
    HouseholdCohortSpec,
    LocationState,
    choose_firm_location,
    choose_household_location,
)
from urban_field_dynamics.contracts import EvidenceStatus


def location(
    unit_id: str,
    *,
    accessibility: float,
    rent: float,
    jobs: float,
    households: float = 0.0,
    housing_capacity: float = 100.0,
    employment_capacity: float = 100.0,
    environment_quality: float = 0.5,
) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=accessibility,
        rent=rent,
        jobs=jobs,
        households=households,
        housing_capacity=housing_capacity,
        employment_capacity=employment_capacity,
        environment_quality=environment_quality,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def household(**updates: object) -> HouseholdCohortSpec:
    values: dict[str, object] = {
        "cohort_id": "service-workers",
        "population": 20.0,
        "initial_unit_id": "home",
        "income": 40.0,
        "housing_demand_per_person": 1.0,
        "accessibility_weight": 1.0,
        "jobs_weight": 1.0,
        "environment_weight": 0.0,
        "rent_burden_weight": 2.0,
        "evidence_status": EvidenceStatus.SYNTHETIC,
    }
    values.update(updates)
    return HouseholdCohortSpec(**values)


def firm(**updates: object) -> FirmCohortSpec:
    values: dict[str, object] = {
        "cohort_id": "ai-research",
        "employees": 20.0,
        "initial_unit_id": "origin",
        "floor_demand_per_employee": 1.0,
        "accessibility_weight": 1.0,
        "agglomeration_weight": 2.0,
        "rent_weight": 1.0,
        "evidence_status": EvidenceStatus.SYNTHETIC,
    }
    values.update(updates)
    return FirmCohortSpec(**values)


def test_agent_and_location_contracts_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        household(hidden_optimizer_target=1.0)

    with pytest.raises(ValidationError, match="extra_forbidden"):
        location("u-1", accessibility=0.5, rent=1.0, jobs=1.0).model_copy(
            update={"unknown": 1.0}
        ).model_validate(
            {
                **location("u-1", accessibility=0.5, rent=1.0, jobs=1.0).model_dump(),
                "unknown": 1.0,
            }
        )


def test_rent_sensitive_household_chooses_affordable_location() -> None:
    expensive = location("expensive", accessibility=1.0, rent=40.0, jobs=100.0)
    affordable = location("affordable", accessibility=0.5, rent=8.0, jobs=40.0)

    choice = choose_household_location(
        household(),
        (expensive, affordable),
        taste_shocks={"expensive": 0.0, "affordable": 0.0},
    )

    assert choice == "affordable"


def test_household_choice_respects_remaining_housing_capacity() -> None:
    full = location(
        "full",
        accessibility=1.0,
        rent=1.0,
        jobs=100.0,
        households=95.0,
        housing_capacity=100.0,
    )
    available = location("available", accessibility=0.4, rent=10.0, jobs=20.0)

    choice = choose_household_location(
        household(population=20.0),
        (full, available),
        taste_shocks={"full": 0.0, "available": 0.0},
    )

    assert choice == "available"


def test_firm_prefers_agglomeration_when_capacity_allows() -> None:
    cluster = location(
        "cluster",
        accessibility=0.7,
        rent=20.0,
        jobs=90.0,
        employment_capacity=150.0,
    )
    cheap = location(
        "cheap",
        accessibility=0.7,
        rent=5.0,
        jobs=5.0,
        employment_capacity=150.0,
    )

    choice = choose_firm_location(
        firm(),
        (cluster, cheap),
        taste_shocks={"cluster": 0.0, "cheap": 0.0},
    )

    assert choice == "cluster"


def test_location_choice_requires_exact_taste_shock_keys() -> None:
    locations = (
        location("aa", accessibility=0.5, rent=10.0, jobs=20.0),
        location("bb", accessibility=0.5, rent=10.0, jobs=20.0),
    )

    with pytest.raises(ValueError, match="taste_shocks must match location IDs"):
        choose_household_location(household(), locations, taste_shocks={"aa": 0.0})
