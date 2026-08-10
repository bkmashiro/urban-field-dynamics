import pytest

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec, LocationState
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.dynamics import (
    FirmBirthPrototype,
    FirmDynamicsSpec,
    HouseholdDynamicsSpec,
)
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def test_world_applies_growth_expansion_and_birth_without_double_counting() -> None:
    location = LocationState(
        unit_id="zone-aa",
        accessibility=0.5,
        rent=10.0,
        jobs=20.0,
        households=100.0,
        housing_capacity=1_000.0,
        employment_capacity=1_000.0,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )
    unit = SpatialUnitSpec(
        unit_id="zone-aa",
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.MIXED,
        pin_kind=PinKind.HARD,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=100.0,
        transition_cost=50.0,
        accessibility=0.5,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )
    household = HouseholdCohortSpec(
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
    firm = FirmCohortSpec(
        cohort_id="firm-aa",
        employees=20.0,
        initial_unit_id="zone-aa",
        floor_demand_per_employee=1.0,
        accessibility_weight=1.0,
        agglomeration_weight=0.0,
        rent_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )
    prototype = FirmBirthPrototype(
        prototype_id="startup",
        annual_birth_probability=1.0,
        employees=5.0,
        initial_unit_id="zone-aa",
        floor_demand_per_employee=1.0,
        accessibility_weight=1.0,
        agglomeration_weight=0.0,
        rent_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )
    result = run_world(
        WorldRunConfig(
            root_seed=7,
            world_id=3,
            schedule=ScheduleConfig(
                start_year=2026,
                end_year=2027,
                replan_years={2026},
            ),
            units=(unit,),
            policy=PolicySpec(policy_id="p0", intervention_year=2026),
            locations=(location,),
            households=(household,),
            firms=(firm,),
            household_dynamics=HouseholdDynamicsSpec(
                mean_growth_rate=0.1,
                growth_volatility=0.0,
            ),
            firm_dynamics=FirmDynamicsSpec(
                annual_death_probability=0.0,
                mean_employee_growth_rate=0.1,
                employee_growth_volatility=0.0,
                birth_prototypes=(prototype,),
            ),
            market=MarketClearingSpec(
                target_occupancy=0.5,
                adjustment_rate=0.0,
                housing_pressure_weight=0.5,
                employment_pressure_weight=0.5,
                minimum_rent=0.0,
            ),
        )
    )

    assert result.final_household_populations == {"household-aa": pytest.approx(121.0)}
    assert result.final_households == {"zone-aa": pytest.approx(121.0)}
    assert result.final_firm_employees == {
        "firm-aa": pytest.approx(24.2),
        "startup-2026": pytest.approx(5.5),
        "startup-2027": pytest.approx(5.0),
    }
    assert result.final_jobs == {"zone-aa": pytest.approx(34.7)}
    assert result.firm_births == {
        2026: ("startup-2026",),
        2027: ("startup-2027",),
    }
    assert result.firm_deaths == {2026: (), 2027: ()}
