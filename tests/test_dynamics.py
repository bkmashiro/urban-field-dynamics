import pytest

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec
from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.dynamics import (
    FirmBirthPrototype,
    FirmDynamicsSpec,
    HouseholdDynamicsSpec,
    evolve_firms,
    evolve_households,
)


def household() -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id="household-aa",
        population=100.0,
        initial_unit_id="zone-aa",
        income=50.0,
        housing_demand_per_person=1.0,
        accessibility_weight=1.0,
        jobs_weight=0.0,
        environment_weight=0.0,
        rent_burden_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def firm() -> FirmCohortSpec:
    return FirmCohortSpec(
        cohort_id="firm-aa",
        employees=20.0,
        initial_unit_id="zone-aa",
        floor_demand_per_employee=1.0,
        accessibility_weight=1.0,
        agglomeration_weight=0.0,
        rent_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def test_household_growth_is_deterministic_and_policy_independent() -> None:
    spec = HouseholdDynamicsSpec(mean_growth_rate=0.02, growth_volatility=0.01)

    first = evolve_households((household(),), spec, root_seed=7, world_id=3, year=2027)
    second = evolve_households((household(),), spec, root_seed=7, world_id=3, year=2027)

    assert first == second
    assert first.cohorts[0].population != 100.0
    assert first.growth_shocks == second.growth_shocks


def test_firm_death_expansion_and_birth_have_independent_tapes() -> None:
    prototype = FirmBirthPrototype(
        prototype_id="startup",
        annual_birth_probability=1.0,
        employees=5.0,
        initial_unit_id="zone-aa",
        floor_demand_per_employee=1.0,
        accessibility_weight=1.0,
        agglomeration_weight=0.0,
        rent_weight=0.0,
        labor_demand_share=0.8,
        skill_requirement="research",
        offered_wage=120.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )
    spec = FirmDynamicsSpec(
        annual_death_probability=0.0,
        mean_employee_growth_rate=0.1,
        employee_growth_volatility=0.0,
        birth_prototypes=(prototype,),
    )

    result = evolve_firms((firm(),), spec, root_seed=7, world_id=3, year=2027)

    by_id = {cohort.cohort_id: cohort for cohort in result.cohorts}
    assert by_id["firm-aa"].employees == pytest.approx(22.0)
    assert by_id["startup-2027"].employees == 5.0
    assert by_id["startup-2027"].skill_requirement == "research"
    assert by_id["startup-2027"].offered_wage == 120.0
    assert result.deaths == ()
    assert result.births == ("startup-2027",)
    assert set(result.death_shocks) == {"firm-aa"}
    assert set(result.expansion_shocks) == {"firm-aa"}
    assert set(result.birth_shocks) == {"startup"}


def test_certain_firm_death_removes_incumbent() -> None:
    result = evolve_firms(
        (firm(),),
        FirmDynamicsSpec(annual_death_probability=1.0),
        root_seed=7,
        world_id=3,
        year=2027,
    )

    assert result.cohorts == ()
    assert result.deaths == ("firm-aa",)


def test_firm_entity_shocks_do_not_shift_when_another_cohort_is_absent() -> None:
    first = firm()
    second = firm().model_copy(update={"cohort_id": "firm-bb"})
    spec = FirmDynamicsSpec(
        annual_death_probability=0.0,
        mean_employee_growth_rate=0.0,
        employee_growth_volatility=0.1,
    )

    together = evolve_firms((first, second), spec, root_seed=7, world_id=3, year=2027)
    alone = evolve_firms((first,), spec, root_seed=7, world_id=3, year=2027)

    assert together.death_shocks["firm-aa"] == alone.death_shocks["firm-aa"]
    assert together.expansion_shocks["firm-aa"] == alone.expansion_shocks["firm-aa"]
