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
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESEARCH,
        pin_kind=PinKind.HARD,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=90.0,
        transition_cost=20.0,
        accessibility=0.1,
        accessibility_value_factor=20.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def location(unit_id: str, *, jobs: float) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=0.1,
        rent=20.0,
        jobs=jobs,
        households=0.0,
        housing_capacity=100.0,
        employment_capacity=100.0,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def test_transport_zone_accessibility_propagates_to_all_member_cells() -> None:
    result = run_world(
        WorldRunConfig(
            root_seed=1,
            world_id=0,
            schedule=ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
            units=tuple(unit(unit_id) for unit_id in ("cell-aa", "cell-ab", "cell-ba", "cell-bb")),
            policy=PolicySpec(policy_id="p0", intervention_year=2026),
            locations=(location("zone-a", jobs=0.0), location("zone-b", jobs=100.0)),
            location_members={
                "zone-a": ("cell-aa", "cell-ab"),
                "zone-b": ("cell-ba", "cell-bb"),
            },
            transport_edges=(
                TransportEdgeSpec(
                    edge_id="road-ab",
                    from_node="zone-a",
                    to_node="zone-b",
                    mode=TransportMode.ROAD,
                    free_flow_minutes=10.0,
                    capacity=100.0,
                ),
            ),
            transport_od=(ODPair(origin="zone-a", destination="zone-b", demand=10.0),),
            transport_assignment=TransportAssignmentSpec(
                bpr_alpha=0.15,
                bpr_beta=4.0,
                logit_theta=0.2,
                iterations=5,
            ),
            accessibility_decay=0.1,
        )
    )

    assert result.final_accessibility["cell-aa"] == result.final_accessibility["cell-ab"]
    assert result.final_accessibility["cell-aa"] > 0.1
    assert result.final_accessibility["cell-ba"] == result.final_accessibility["cell-bb"]


def test_location_members_must_cover_each_spatial_unit_once() -> None:
    try:
        WorldRunConfig(
            root_seed=1,
            world_id=0,
            schedule=ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
            units=(unit("cell-aa"), unit("cell-ab")),
            policy=PolicySpec(policy_id="p0", intervention_year=2026),
            locations=(location("zone-a", jobs=0.0),),
            location_members={"zone-a": ("cell-aa",)},
        )
    except ValueError as exc:
        assert "cover every spatial unit exactly once" in str(exc)
    else:
        raise AssertionError("invalid location member coverage was accepted")
