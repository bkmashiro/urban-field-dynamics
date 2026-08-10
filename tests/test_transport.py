import pytest

import urban_field_dynamics.transport as transport_module
from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentSpec,
    TransportEdgeSpec,
    TransportMode,
    assign_transport,
    generalized_cost_skim,
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


def test_assignment_reuses_one_shortest_path_tree_per_origin_mode_iteration(monkeypatch) -> None:
    edges = (
        edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=8.0, capacity=30.0),
        edge("rail-aa", mode=TransportMode.RAIL, free_flow_minutes=12.0, capacity=300.0),
    )
    ods = (
        ODPair(origin="origin", destination="destination", demand=60.0),
        ODPair(origin="origin", destination="destination", demand=40.0),
    )
    original = transport_module._shortest_paths_from_origin
    transport_module._assign_transport_cached.cache_clear()
    calls = 0
    requested_destinations: list[frozenset[str] | None] = []

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        requested_destinations.append(kwargs.get("destinations"))
        return original(*args, **kwargs)

    monkeypatch.setattr(transport_module, "_shortest_paths_from_origin", counted)
    assign_transport(edges, ods, assignment_spec())

    assert calls == 2 * (assignment_spec().iterations + 1)
    assert requested_destinations == [frozenset({"destination"})] * calls


def test_assignment_cache_is_reused_and_defensively_copied(monkeypatch) -> None:
    edges = (edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=8.0, capacity=30.0),)
    ods = (ODPair(origin="origin", destination="destination", demand=10.0),)
    original = transport_module._shortest_paths_from_origin
    transport_module._assign_transport_cached.cache_clear()
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(transport_module, "_shortest_paths_from_origin", counted)
    first = assign_transport(edges, ods, assignment_spec())
    initial_calls = calls
    second = assign_transport(edges, ods, assignment_spec())
    first.edge_flows["road-aa"] = 999.0
    first.od_mode_shares["origin->destination"][TransportMode.ROAD] = 0.0
    third = assign_transport(edges, ods, assignment_spec())

    assert initial_calls > 0
    assert calls == initial_calls
    assert second.edge_flows["road-aa"] == pytest.approx(10.0)
    assert third.edge_flows["road-aa"] == pytest.approx(10.0)
    assert third.od_mode_shares["origin->destination"][TransportMode.ROAD] == pytest.approx(1.0)


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


def test_generalized_cost_skim_covers_declared_nodes_without_adding_demand() -> None:
    edges = (
        edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=8.0, capacity=30.0),
        edge("rail-aa", mode=TransportMode.RAIL, free_flow_minutes=12.0, capacity=300.0),
    )
    assignment = assign_transport(
        edges,
        (ODPair(origin="origin", destination="destination", demand=10.0),),
        assignment_spec(),
    )

    skim = generalized_cost_skim(
        edges,
        assignment.edge_travel_minutes,
        nodes=("origin", "destination"),
    )

    assert skim["origin->origin"] == 0.0
    assert skim["destination->destination"] == 0.0
    assert skim["origin->destination"] > 0.0
    assert "destination->origin" not in skim


def test_generalized_cost_skim_can_limit_origins_and_destinations() -> None:
    edges = (edge("road-aa", mode=TransportMode.ROAD, free_flow_minutes=8.0, capacity=30.0),)

    skim = generalized_cost_skim(
        edges,
        {"road-aa": 8.0},
        origins=("origin",),
        destinations=("destination",),
    )

    assert skim == {"origin->destination": 8.0}
