from urban_field_dynamics.agents import (
    HouseholdCohortSpec,
    LocationState,
    choose_household_location,
)
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def household() -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id="families",
        population=40.0,
        initial_unit_id="unit-aa",
        income=100.0,
        housing_demand_per_person=1.0,
        accessibility_weight=0.0,
        jobs_weight=0.0,
        environment_weight=0.0,
        service_weight=5.0,
        rent_burden_weight=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def location(
    unit_id: str,
    *,
    service_quality: float,
    service_capacity: float,
    households: float = 0.0,
) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=0.5,
        rent=10.0,
        jobs=0.0,
        households=households,
        housing_capacity=100.0,
        employment_capacity=100.0,
        environment_quality=0.5,
        service_quality=service_quality,
        service_capacity=service_capacity,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def unit(unit_id: str) -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id=unit_id,
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


def config(policy: PolicySpec) -> WorldRunConfig:
    return WorldRunConfig(
        root_seed=1,
        world_id=0,
        schedule=ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
        units=(unit("unit-aa"), unit("unit-bb")),
        policy=policy,
        locations=(
            location(
                "unit-aa",
                service_quality=1.0,
                service_capacity=10.0,
                households=40.0,
            ),
            location("unit-bb", service_quality=0.8, service_capacity=100.0),
        ),
        households=(household(),),
        market=MarketClearingSpec(
            target_occupancy=0.5,
            adjustment_rate=0.0,
            housing_pressure_weight=0.5,
            employment_pressure_weight=0.5,
            minimum_rent=1.0,
        ),
    )


def test_service_sensitive_household_prefers_higher_service_quality() -> None:
    chosen = choose_household_location(
        household(),
        (
            location("unit-aa", service_quality=1.0, service_capacity=10.0),
            location("unit-bb", service_quality=0.8, service_capacity=100.0),
        ),
        taste_shocks={"unit-aa": 0.0, "unit-bb": 0.0},
    )

    assert chosen == "unit-bb"


def test_public_service_policy_changes_relocation_through_location_state() -> None:
    baseline = run_world(config(PolicySpec(policy_id="p0", intervention_year=2026)))
    investment = run_world(
        config(
            PolicySpec(
                policy_id="p3",
                intervention_year=2026,
                service_capacity_multiplier_by_location={"unit-aa": 10.0},
            )
        )
    )

    assert baseline.household_locations == {"families": "unit-bb"}
    assert investment.household_locations == {"families": "unit-aa"}
    assert investment.final_service_capacity["unit-aa"] == 100.0
