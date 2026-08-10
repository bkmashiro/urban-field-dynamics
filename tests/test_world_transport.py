from urban_field_dynamics.agents import LocationState
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentSpec,
    TransportEdgeSpec,
    TransportMode,
)
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def unit(unit_id: str) -> SpatialUnitSpec:
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
        accessibility=0.0,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def location(unit_id: str, *, jobs: float) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=0.0,
        rent=10.0,
        jobs=jobs,
        households=0.0,
        housing_capacity=100.0,
        employment_capacity=100.0,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def config(policy: PolicySpec) -> WorldRunConfig:
    return WorldRunConfig(
        root_seed=20260810,
        world_id=2,
        schedule=ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
        units=(unit("unit-aa"), unit("unit-bb")),
        policy=policy,
        locations=(location("unit-aa", jobs=0.0), location("unit-bb", jobs=100.0)),
        transport_edges=(
            TransportEdgeSpec(
                edge_id="road-aa",
                from_node="unit-aa",
                to_node="unit-bb",
                mode=TransportMode.ROAD,
                free_flow_minutes=10.0,
                capacity=20.0,
            ),
        ),
        transport_od=(ODPair(origin="unit-aa", destination="unit-bb", demand=100.0),),
        transport_assignment=TransportAssignmentSpec(
            bpr_alpha=0.15,
            bpr_beta=4.0,
            logit_theta=0.2,
            iterations=20,
        ),
        accessibility_decay=0.1,
    )


def test_transport_capacity_policy_improves_accessibility_through_assignment() -> None:
    baseline = run_world(config(PolicySpec(policy_id="p0", intervention_year=2026)))
    investment = run_world(
        config(
            PolicySpec(
                policy_id="p1",
                intervention_year=2026,
                transport_capacity_multiplier_by_edge={"road-aa": 10.0},
                transport_time_multiplier_by_edge={"road-aa": 0.5},
            )
        )
    )

    assert investment.final_accessibility["unit-aa"] > baseline.final_accessibility["unit-aa"]
    assert baseline.transport_traces[2026]["winter"].edge_flows["road-aa"] == 100.0
    assert (
        investment.transport_traces[2026]["winter"].edge_travel_minutes["road-aa"]
        < baseline.transport_traces[2026]["winter"].edge_travel_minutes["road-aa"]
    )


def test_transport_repeats_deterministically_across_representative_seasons() -> None:
    result = run_world(config(PolicySpec(policy_id="p0", intervention_year=2026)))

    seasons = result.transport_traces[2026]
    assert seasons["spring"] == seasons["summer"] == seasons["autumn"] == seasons["winter"]
