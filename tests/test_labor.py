import pytest

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec
from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.labor import LaborMatchingSpec, match_labor

SYNTHETIC = EvidenceStatus.SYNTHETIC


def household(
    cohort_id: str,
    *,
    population: float,
    labor_force_share: float,
    skill_group: str,
    reservation_wage: float,
    unit_id: str,
) -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id=cohort_id,
        population=population,
        initial_unit_id=unit_id,
        income=100.0,
        housing_demand_per_person=1.0,
        accessibility_weight=1.0,
        jobs_weight=1.0,
        environment_weight=1.0,
        rent_burden_weight=1.0,
        labor_force_share=labor_force_share,
        skill_group=skill_group,
        reservation_wage=reservation_wage,
        evidence_status=SYNTHETIC,
    )


def firm(
    cohort_id: str,
    *,
    employees: float,
    skill_requirement: str,
    offered_wage: float,
    unit_id: str,
) -> FirmCohortSpec:
    return FirmCohortSpec(
        cohort_id=cohort_id,
        employees=employees,
        initial_unit_id=unit_id,
        floor_demand_per_employee=1.0,
        accessibility_weight=1.0,
        agglomeration_weight=1.0,
        rent_weight=1.0,
        labor_demand_share=1.0,
        skill_requirement=skill_requirement,
        offered_wage=offered_wage,
        evidence_status=SYNTHETIC,
    )


def test_labor_matching_respects_skill_wage_commute_and_capacity() -> None:
    households = (
        household(
            "knowledge-workers",
            population=10.0,
            labor_force_share=1.0,
            skill_group="knowledge",
            reservation_wage=80.0,
            unit_id="north",
        ),
        household(
            "service-workers",
            population=8.0,
            labor_force_share=1.0,
            skill_group="service",
            reservation_wage=60.0,
            unit_id="south",
        ),
    )
    firms = (
        firm(
            "research-firm",
            employees=6.0,
            skill_requirement="knowledge",
            offered_wage=120.0,
            unit_id="central",
        ),
        firm(
            "service-firm",
            employees=10.0,
            skill_requirement="service",
            offered_wage=70.0,
            unit_id="south",
        ),
    )

    result = match_labor(
        households,
        firms,
        household_locations={"knowledge-workers": "north", "service-workers": "south"},
        firm_locations={"research-firm": "central", "service-firm": "south"},
        commute_costs={"north->central": 30.0, "south->south": 0.0},
        spec=LaborMatchingSpec(
            max_commute_minutes=45.0,
            commute_cost_per_minute=1.0,
            wage_adjustment_rate=0.1,
            vacancy_retention_rate=0.5,
        ),
    )

    assert result.flows == {
        "knowledge-workers->research-firm": 6.0,
        "service-workers->service-firm": 8.0,
    }
    assert result.household_unemployed == {
        "knowledge-workers": 4.0,
        "service-workers": 0.0,
    }
    assert result.firm_vacancies == {"research-firm": 0.0, "service-firm": 2.0}
    assert result.household_mean_commute_minutes == {
        "knowledge-workers": 30.0,
        "service-workers": 0.0,
    }
    assert result.mean_commute_minutes == pytest.approx(30.0 * 6.0 / 14.0)
    assert result.adjusted_firm_wages["service-firm"] > 70.0
    assert result.adjusted_firm_employees == {
        "research-firm": 6.0,
        "service-firm": 9.0,
    }


def test_labor_matching_rejects_low_wage_and_missing_commute_path() -> None:
    households = (
        household(
            "workers",
            population=5.0,
            labor_force_share=1.0,
            skill_group="knowledge",
            reservation_wage=100.0,
            unit_id="north",
        ),
    )
    firms = (
        firm(
            "low-wage",
            employees=5.0,
            skill_requirement="knowledge",
            offered_wage=90.0,
            unit_id="south",
        ),
    )

    result = match_labor(
        households,
        firms,
        household_locations={"workers": "north"},
        firm_locations={"low-wage": "south"},
        commute_costs={},
        spec=LaborMatchingSpec(
            max_commute_minutes=45.0,
            commute_cost_per_minute=1.0,
            wage_adjustment_rate=0.1,
        ),
    )

    assert result.flows == {}
    assert result.household_unemployed == {"workers": 5.0}
    assert result.firm_vacancies == {"low-wage": 5.0}


def test_labor_matching_is_input_order_invariant() -> None:
    households = (
        household(
            "workers-aa",
            population=4.0,
            labor_force_share=1.0,
            skill_group="general",
            reservation_wage=0.0,
            unit_id="north",
        ),
        household(
            "workers-bb",
            population=3.0,
            labor_force_share=1.0,
            skill_group="general",
            reservation_wage=0.0,
            unit_id="south",
        ),
    )
    firms = (
        firm(
            "firm-aa",
            employees=3.0,
            skill_requirement="general",
            offered_wage=100.0,
            unit_id="north",
        ),
        firm(
            "firm-bb",
            employees=4.0,
            skill_requirement="general",
            offered_wage=90.0,
            unit_id="south",
        ),
    )
    kwargs = {
        "household_locations": {"workers-aa": "north", "workers-bb": "south"},
        "firm_locations": {"firm-aa": "north", "firm-bb": "south"},
        "commute_costs": {"north->south": 10.0, "south->north": 10.0},
        "spec": LaborMatchingSpec(
            max_commute_minutes=45.0,
            commute_cost_per_minute=1.0,
            wage_adjustment_rate=0.1,
        ),
    }

    assert match_labor(households, firms, **kwargs) == match_labor(
        tuple(reversed(households)), tuple(reversed(firms)), **kwargs
    )
