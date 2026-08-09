from urban_field_dynamics.agents import HouseholdCohortSpec, LocationState
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.environment import (
    EnvironmentalUnitSpec,
    ExposureWeights,
    SeasonalEnvironmentSpec,
)
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig, Season
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def unit(unit_id: str) -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id=unit_id,
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESIDENTIAL,
        pin_kind=PinKind.HARD,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=100.0,
        transition_cost=0.0,
        accessibility=0.5,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def location(unit_id: str, *, households: float) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=0.5,
        rent=10.0,
        jobs=10.0,
        households=households,
        housing_capacity=100.0,
        employment_capacity=100.0,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def environmental(unit_id: str, *, green: float) -> EnvironmentalUnitSpec:
    return EnvironmentalUnitSpec(
        unit_id=unit_id,
        green_fraction=green,
        traffic_exposure_factor=0.0,
        activity_intensity=0.4,
        night_light_intensity=0.4,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def profiles() -> tuple[SeasonalEnvironmentSpec, ...]:
    return tuple(
        SeasonalEnvironmentSpec(
            season=season,
            air_background=0.2,
            noise_background_db=45.0,
            heat_stress=0.8 if season is Season.SUMMER else 0.3,
            night_length_factor=0.5 if season is Season.SUMMER else 0.8,
            green_cooling_strength=0.6,
            activity_heat_factor=0.1,
        )
        for season in Season
    )


def weights() -> ExposureWeights:
    return ExposureWeights(air=0.25, noise=0.25, light=0.25, heat=0.25)


def household() -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id="sensitive-households",
        population=40.0,
        initial_unit_id="unit-aa",
        income=100.0,
        housing_demand_per_person=1.0,
        accessibility_weight=0.0,
        jobs_weight=0.0,
        rent_burden_weight=0.0,
        environment_weight=5.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def config(policy: PolicySpec, *, with_household: bool = False) -> WorldRunConfig:
    return WorldRunConfig(
        root_seed=20260810,
        world_id=2,
        schedule=ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
        units=(unit("unit-aa"), unit("unit-bb")),
        policy=policy,
        locations=(
            location("unit-aa", households=40.0 if with_household else 0.0),
            location("unit-bb", households=0.0),
        ),
        households=(household(),) if with_household else (),
        market=(
            MarketClearingSpec(
                target_occupancy=0.5,
                adjustment_rate=0.0,
                housing_pressure_weight=0.5,
                employment_pressure_weight=0.5,
                minimum_rent=1.0,
            )
            if with_household
            else None
        ),
        environmental_units=(
            environmental("unit-aa", green=0.0),
            environmental("unit-bb", green=0.8),
        ),
        seasonal_environment=profiles(),
        exposure_weights=weights(),
        agent_taste_shock_scale=0.0,
    )


def test_blue_green_policy_changes_exposure_through_green_fraction() -> None:
    baseline = run_world(config(PolicySpec(policy_id="p0", intervention_year=2026)))
    blue_green = run_world(
        config(
            PolicySpec(
                policy_id="p2",
                intervention_year=2026,
                green_fraction_delta_by_unit={"unit-aa": 0.6},
            )
        )
    )

    assert (
        blue_green.environment_traces[2026]["summer"]["unit-aa"].heat
        < baseline.environment_traces[2026]["summer"]["unit-aa"].heat
    )
    assert (
        blue_green.final_environment_quality["unit-aa"]
        > baseline.final_environment_quality["unit-aa"]
    )


def test_sensitive_households_use_mean_seasonal_environment_quality() -> None:
    result = run_world(
        config(PolicySpec(policy_id="p0", intervention_year=2026), with_household=True)
    )

    assert result.final_environment_quality["unit-bb"] > result.final_environment_quality["unit-aa"]
    assert result.household_locations == {"sensitive-households": "unit-bb"}
