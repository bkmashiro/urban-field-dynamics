"""Frozen integrated synthetic fixture for policy and mechanism qualification."""

from __future__ import annotations

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec, LocationState
from urban_field_dynamics.campaign import CampaignArm, CampaignSpec
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.environment import (
    EnvironmentalUnitSpec,
    ExposureWeights,
    SeasonalEnvironmentSpec,
)
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig, Season
from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentSpec,
    TransportEdgeSpec,
    TransportMode,
)
from urban_field_dynamics.world import MechanismSwitches, PolicySpec


def _unit(unit_id: str, use: LandUse, accessibility: float) -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id=unit_id,
        area_sqm=10_000.0,
        current_use=use,
        candidate_use=LandUse.MIXED,
        pin_kind=PinKind.SOFT,
        asset_age_years=25,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=82.0,
        transition_cost=35.0,
        accessibility=accessibility,
        accessibility_value_factor=35.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def _location(
    unit_id: str,
    *,
    accessibility: float,
    households: float,
    jobs: float,
    quality: float,
) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=accessibility,
        rent=30.0,
        jobs=jobs,
        households=households,
        housing_capacity=120.0,
        employment_capacity=120.0,
        environment_quality=quality,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def _household(
    cohort_id: str,
    initial_unit_id: str,
    *,
    environment_weight: float,
    income: float,
) -> HouseholdCohortSpec:
    return HouseholdCohortSpec(
        cohort_id=cohort_id,
        population=40.0,
        initial_unit_id=initial_unit_id,
        income=income,
        housing_demand_per_person=1.0,
        accessibility_weight=2.0,
        jobs_weight=1.5,
        environment_weight=environment_weight,
        rent_burden_weight=2.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def _firm(cohort_id: str, initial_unit_id: str, employees: float) -> FirmCohortSpec:
    return FirmCohortSpec(
        cohort_id=cohort_id,
        employees=employees,
        initial_unit_id=initial_unit_id,
        floor_demand_per_employee=1.0,
        accessibility_weight=1.5,
        agglomeration_weight=2.0,
        rent_weight=0.4,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def _edge(
    edge_id: str,
    origin: str,
    *,
    mode: TransportMode,
    time: float,
    capacity: float,
) -> TransportEdgeSpec:
    return TransportEdgeSpec(
        edge_id=edge_id,
        from_node=origin,
        to_node="unit-central",
        mode=mode,
        free_flow_minutes=time,
        capacity=capacity,
    )


def _environment(unit_id: str, green: float, edge_id: str | None) -> EnvironmentalUnitSpec:
    return EnvironmentalUnitSpec(
        unit_id=unit_id,
        green_fraction=green,
        traffic_exposure_factor=0.3,
        activity_intensity=0.5,
        night_light_intensity=0.5,
        transport_edge_ids=(edge_id,) if edge_id else (),
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def _seasonal_profiles() -> tuple[SeasonalEnvironmentSpec, ...]:
    heat = {
        Season.SPRING: 0.35,
        Season.SUMMER: 0.85,
        Season.AUTUMN: 0.4,
        Season.WINTER: 0.2,
    }
    night = {
        Season.SPRING: 0.65,
        Season.SUMMER: 0.5,
        Season.AUTUMN: 0.75,
        Season.WINTER: 0.9,
    }
    return tuple(
        SeasonalEnvironmentSpec(
            season=season,
            air_background=0.2,
            noise_background_db=45.0,
            heat_stress=heat[season],
            night_length_factor=night[season],
            green_cooling_strength=0.6,
            activity_heat_factor=0.1,
        )
        for season in Season
    )


def integrated_smoke_campaign(*, world_count: int = 8) -> CampaignSpec:
    """Build P0-P3 plus six ablations over frozen synthetic units and cohorts."""

    if world_count <= 0:
        raise ValueError("world_count must be positive")
    p0 = PolicySpec(policy_id="p0", intervention_year=2026)
    p1 = PolicySpec(
        policy_id="p1",
        intervention_year=2026,
        transport_capacity_multiplier_by_edge={"road-north": 4.0, "road-south": 4.0},
    )
    p2 = PolicySpec(
        policy_id="p2",
        intervention_year=2026,
        green_fraction_delta_by_unit={"unit-north": 0.4, "unit-south": 0.3},
    )
    p3 = PolicySpec(
        policy_id="p3",
        intervention_year=2026,
        transport_capacity_multiplier_by_edge={"road-north": 4.0, "road-south": 4.0},
        green_fraction_delta_by_unit={"unit-north": 0.4, "unit-south": 0.3},
    )
    return CampaignSpec(
        campaign_id=(
            "integrated-smoke-v1" if world_count == 8 else f"integrated-qualification-{world_count}"
        ),
        model_scope=(
            "integrated agent, transport, environment, and redevelopment qualification slice"
        ),
        root_seed=20260810,
        world_ids=tuple(range(world_count)),
        schedule=ScheduleConfig(start_year=2026, end_year=2030, replan_years={2026, 2030}),
        units=(
            _unit("unit-north", LandUse.RESIDENTIAL, 0.2),
            _unit("unit-central", LandUse.RESEARCH, 0.6),
            _unit("unit-south", LandUse.MIXED, 0.3),
        ),
        arms=(
            CampaignArm(arm_id="p0", policy=p0),
            CampaignArm(arm_id="p1", policy=p1),
            CampaignArm(arm_id="p2", policy=p2),
            CampaignArm(arm_id="p3", policy=p3),
            CampaignArm(arm_id="p3-no-inertia", policy=p3, transition_inertia_enabled=False),
            CampaignArm(
                arm_id="p3-no-agglomeration",
                policy=p3,
                mechanisms=MechanismSwitches(agglomeration_enabled=False),
            ),
            CampaignArm(
                arm_id="p3-no-transport-attraction",
                policy=p3,
                mechanisms=MechanismSwitches(transport_attraction_enabled=False),
            ),
            CampaignArm(
                arm_id="p3-no-seasonality",
                policy=p3,
                mechanisms=MechanismSwitches(seasonality_enabled=False),
            ),
            CampaignArm(
                arm_id="p3-no-environmental-exposure",
                policy=p3,
                mechanisms=MechanismSwitches(environmental_exposure_enabled=False),
            ),
            CampaignArm(
                arm_id="p3-no-public-coordination",
                policy=p3,
                mechanisms=MechanismSwitches(public_coordination_enabled=False),
            ),
        ),
        development_shock_scale=12.0,
        locations=(
            _location("unit-north", accessibility=0.2, households=40.0, jobs=0.0, quality=0.45),
            _location("unit-central", accessibility=0.6, households=40.0, jobs=50.0, quality=0.55),
            _location("unit-south", accessibility=0.3, households=40.0, jobs=30.0, quality=0.5),
        ),
        households=(
            _household("students", "unit-north", environment_weight=1.0, income=80.0),
            _household("families", "unit-central", environment_weight=2.5, income=120.0),
            _household("service-workers", "unit-south", environment_weight=1.5, income=70.0),
        ),
        firms=(
            _firm("research-firms", "unit-central", 50.0),
            _firm("service-firms", "unit-south", 30.0),
        ),
        market=MarketClearingSpec(
            target_occupancy=0.7,
            adjustment_rate=0.1,
            housing_pressure_weight=0.6,
            employment_pressure_weight=0.4,
            minimum_rent=5.0,
        ),
        agent_taste_shock_scale=0.15,
        transport_edges=(
            _edge("road-north", "unit-north", mode=TransportMode.ROAD, time=8.0, capacity=25.0),
            _edge("rail-north", "unit-north", mode=TransportMode.RAIL, time=12.0, capacity=100.0),
            _edge("road-south", "unit-south", mode=TransportMode.ROAD, time=7.0, capacity=25.0),
            _edge("rail-south", "unit-south", mode=TransportMode.RAIL, time=11.0, capacity=100.0),
        ),
        transport_od=(
            ODPair(origin="unit-north", destination="unit-central", demand=90.0),
            ODPair(origin="unit-south", destination="unit-central", demand=80.0),
        ),
        transport_assignment=TransportAssignmentSpec(
            bpr_alpha=0.15,
            bpr_beta=4.0,
            logit_theta=0.2,
            iterations=20,
        ),
        accessibility_decay=0.08,
        environmental_units=(
            _environment("unit-north", 0.1, "road-north"),
            _environment("unit-central", 0.25, None),
            _environment("unit-south", 0.15, "road-south"),
        ),
        seasonal_environment=_seasonal_profiles(),
        exposure_weights=ExposureWeights(air=0.3, noise=0.2, light=0.15, heat=0.35),
    )
