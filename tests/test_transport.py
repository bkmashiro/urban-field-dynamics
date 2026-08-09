import pytest

from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentSpec,
    TransportEdgeSpec,
    TransportMode,
    assign_transport,
    opportunity_accessibility,
)


def edge(
    edge_id: str,
    *,
    mode: TransportMode,
    free_flow_minutes: float,
    capacity: float,
) -> TransportEdgeSpec:
    return TransportEdgeSpec(
        edge_id=edge_id,
        from_node="origin",
        to_node="destination",
        mode=mode,
        free_flow_minutes=free_flow_minutes,
        capacity=capacity,
        generalized_penalty_minutes=0.0,
    )


def assignment_spec() -> TransportAssignmentSpec:
    return TransportAssignmentSpec(
        bpr_alpha=0.15,
        bpr_beta=4.0,
        logit_theta=0.2,
        iterations=20,
    )


def test_capacity_feedback_raises_congested_road_travel_time() -> None:
    result = assign_transport(
        (edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=10.0, capacity=50.0),),
        (ODPair(origin="origin", destination="destination", demand=100.0),),
        assignment_spec(),
    )

    assert result.edge_flows["road-aa"] == pytest.approx(100.0)
    assert result.edge_travel_minutes["road-aa"] == pytest.approx(34.0)


def test_logit_mode_choice_shifts_demand_to_high_capacity_rail() -> None:
    result = assign_transport(
        (
            edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=8.0, capacity=20.0),
            edge("rail-aa", mode=TransportMode.RAIL, free_flow_minutes=12.0, capacity=500.0),
        ),
        (ODPair(origin="origin", destination="destination", demand=100.0),),
        assignment_spec(),
    )

    shares = result.od_mode_shares["origin->destination"]
    assert shares[TransportMode.RAIL] > shares[TransportMode.ROAD]
    assert sum(shares.values()) == pytest.approx(1.0)
    assert sum(result.edge_flows.values()) == pytest.approx(100.0)


def test_assignment_is_deterministic_and_input_order_invariant() -> None:
    edges = (
        edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=8.0, capacity=30.0),
        edge("rail-aa", mode=TransportMode.RAIL, free_flow_minutes=12.0, capacity=300.0),
    )
    ods = (
        ODPair(origin="origin", destination="destination", demand=60.0),
        ODPair(origin="origin", destination="destination", demand=40.0),
    )

    assert assign_transport(edges, ods, assignment_spec()) == assign_transport(
        tuple(reversed(edges)), tuple(reversed(ods)), assignment_spec()
    )


def test_opportunity_accessibility_rewards_lower_generalized_cost() -> None:
    accessibility = opportunity_accessibility(
        costs={
            "near->jobs": 10.0,
            "far->jobs": 30.0,
        },
        opportunities={"jobs": 100.0},
        decay=0.1,
    )

    assert accessibility["near"] > accessibility["far"]
    assert 0.0 <= accessibility["far"] <= accessibility["near"] <= 1.0
