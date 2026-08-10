from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec, LocationState
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def unit(unit_id: str, *, accessibility: float) -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id=unit_id,
        area_sqm=10_000.0,
        current_use=LandUse.MIXED,
        candidate_use=LandUse.MIXED,
        pin_kind=PinKind.HARD,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=100.0,
        transition_cost=0.0,
        accessibility=accessibility,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def location(
    unit_id: str,
    *,
    accessibility: float,
    households: float,
    jobs: float,
) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=accessibility,
        rent=10.0,
        jobs=jobs,
        households=households,
        housing_capacity=100.0,
        employment_capacity=100.0,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def household() -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id="household-aa",
        population=60.0,
        initial_unit_id="unit-aa",
        income=100.0,
        housing_demand_per_person=1.0,
        accessibility_weight=2.0,
        jobs_weight=0.0,
        environment_weight=0.0,
        rent_burden_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def firm() -> FirmCohortSpec:
    return FirmCohortSpec(
        cohort_id="firm-aa",
        employees=60.0,
        initial_unit_id="unit-aa",
        floor_demand_per_employee=1.0,
        accessibility_weight=2.0,
        agglomeration_weight=0.0,
        rent_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def market() -> MarketClearingSpec:
    return MarketClearingSpec(
        target_occupancy=0.5,
        adjustment_rate=0.2,
        housing_pressure_weight=0.5,
        employment_pressure_weight=0.5,
        minimum_rent=1.0,
    )


def config(policy: PolicySpec, *, end_year: int = 2026) -> WorldRunConfig:
    return WorldRunConfig(
        root_seed=20260810,
        world_id=2,
        schedule=ScheduleConfig(start_year=2026, end_year=end_year, replan_years={2026}),
        units=(unit("unit-aa", accessibility=0.2), unit("unit-bb", accessibility=0.6)),
        policy=policy,
        locations=(
            location("unit-aa", accessibility=0.2, households=60.0, jobs=60.0),
            location("unit-bb", accessibility=0.6, households=0.0, jobs=0.0),
        ),
        households=(household(),),
        firms=(firm(),),
        market=market(),
        agent_taste_shock_scale=0.0,
    )


def test_spatial_policy_changes_agent_locations_without_changing_taste_tapes() -> None:
    baseline = run_world(
        config(
            PolicySpec(
                policy_id="p0",
                intervention_year=2026,
                accessibility_delta=0.0,
            )
        )
    )
    investment = run_world(
        config(
            PolicySpec(
                policy_id="p1",
                intervention_year=2026,
                accessibility_delta_by_unit={"unit-aa": 0.8},
            )
        )
    )

    assert baseline.household_locations == {"household-aa": "unit-bb"}
    assert investment.household_locations == {"household-aa": "unit-aa"}
    assert baseline.firm_locations == {"firm-aa": "unit-bb"}
    assert investment.firm_locations == {"firm-aa": "unit-aa"}
    assert baseline.household_taste_shocks == investment.household_taste_shocks
    assert baseline.firm_taste_shocks == investment.firm_taste_shocks


def test_repeated_annual_relocation_does_not_duplicate_weighted_cohorts() -> None:
    result = run_world(
        config(
            PolicySpec(
                policy_id="p0",
                intervention_year=2026,
                accessibility_delta=0.0,
            ),
            end_year=2027,
        )
    )

    assert sum(result.final_households.values()) == 60.0
    assert sum(result.final_jobs.values()) == 60.0
    assert result.final_rents["unit-bb"] > 10.0
    assert set(result.market_traces) == {2026, 2027}
    assert all(trace.converged for trace in result.market_traces.values())
