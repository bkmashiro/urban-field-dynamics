"""Auditable multimodal transport assignment surrogate."""

from __future__ import annotations

import heapq
import math
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
PositiveInt = Annotated[int, Field(gt=0)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")]


class TransportMode(StrEnum):
    WALK = "walk"
    CYCLE = "cycle"
    ROAD = "road"
    BUS = "bus"
    RAIL = "rail"


class TransportEdgeSpec(BaseModel):
    """One directed modal edge in the fast surrogate graph."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    edge_id: Identifier
    from_node: Identifier
    to_node: Identifier
    mode: TransportMode
    free_flow_minutes: PositiveFloat
    capacity: PositiveFloat
    generalized_penalty_minutes: NonNegativeFloat = 0.0


class ODPair(BaseModel):
    """Aggregate representative-period travel demand."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    origin: Identifier
    destination: Identifier
    demand: NonNegativeFloat


class TransportAssignmentSpec(BaseModel):
    """Fixed numerical contract for logit plus BPR/MSC assignment."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    bpr_alpha: NonNegativeFloat
    bpr_beta: PositiveFloat
    logit_theta: PositiveFloat
    iterations: PositiveInt


class TransportAssignmentResult(BaseModel):
    """Deterministic aggregate transport assignment evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    edge_flows: dict[str, float]
    edge_travel_minutes: dict[str, float]
    od_mode_shares: dict[str, dict[TransportMode, float]]
    od_mode_costs: dict[str, dict[TransportMode, float]]


def _travel_minutes(
    edge: TransportEdgeSpec,
    flow: float,
    spec: TransportAssignmentSpec,
) -> float:
    return edge.free_flow_minutes * (1.0 + spec.bpr_alpha * (flow / edge.capacity) ** spec.bpr_beta)


def _modal_adjacency(
    edges: tuple[TransportEdgeSpec, ...],
) -> dict[TransportMode, dict[str, tuple[TransportEdgeSpec, ...]]]:
    grouped: dict[TransportMode, dict[str, list[TransportEdgeSpec]]] = {}
    for edge in edges:
        grouped.setdefault(edge.mode, {}).setdefault(edge.from_node, []).append(edge)
    return {
        mode: {
            node: tuple(sorted(outgoing, key=lambda edge: edge.edge_id))
            for node, outgoing in grouped[mode].items()
        }
        for mode in TransportMode
        if mode in grouped
    }


def _shortest_paths_from_origin(
    adjacency: dict[str, tuple[TransportEdgeSpec, ...]],
    costs: dict[str, float],
    origin: str,
    *,
    destinations: frozenset[str] | None = None,
) -> dict[str, tuple[float, tuple[str, ...]]]:
    """Return the deterministic shortest-path tree for one origin and mode."""

    queue: list[tuple[float, str, tuple[str, ...]]] = [(0.0, origin, ())]
    best: dict[str, float] = {origin: 0.0}
    paths: dict[str, tuple[float, tuple[str, ...]]] = {}
    remaining = set(destinations) if destinations is not None else None
    while queue:
        cost, node, path = heapq.heappop(queue)
        if cost > best.get(node, math.inf):
            continue
        paths[node] = (cost, path)
        if remaining is not None and node in remaining:
            remaining.remove(node)
            if not remaining:
                break
        for edge in adjacency.get(node, ()):
            candidate = cost + costs[edge.edge_id] + edge.generalized_penalty_minutes
            if candidate < best.get(edge.to_node, math.inf):
                best[edge.to_node] = candidate
                heapq.heappush(queue, (candidate, edge.to_node, (*path, edge.edge_id)))
    return paths


def _path_trees(
    adjacency_by_mode: dict[TransportMode, dict[str, tuple[TransportEdgeSpec, ...]]],
    costs: dict[str, float],
    destinations_by_origin: dict[str, frozenset[str]],
) -> dict[tuple[str, TransportMode], dict[str, tuple[float, tuple[str, ...]]]]:
    return {
        (origin, mode): _shortest_paths_from_origin(
            adjacency,
            costs,
            origin,
            destinations=destinations,
        )
        for origin, destinations in destinations_by_origin.items()
        for mode, adjacency in adjacency_by_mode.items()
    }


def _mode_paths_from_trees(
    trees: dict[tuple[str, TransportMode], dict[str, tuple[float, tuple[str, ...]]]],
    od: ODPair,
) -> dict[TransportMode, tuple[float, tuple[str, ...]]]:
    paths = {
        mode: destinations[od.destination]
        for (origin, mode), destinations in trees.items()
        if origin == od.origin and od.destination in destinations
    }
    if not paths:
        raise ValueError(f"no modal path for OD {od.origin}->{od.destination}")
    return paths


def generalized_cost_skim(
    edges: tuple[TransportEdgeSpec, ...],
    edge_travel_minutes: dict[str, float],
    *,
    nodes: tuple[str, ...] | None = None,
    origins: tuple[str, ...] | None = None,
    destinations: tuple[str, ...] | None = None,
) -> dict[str, float]:
    """Return reachable directed costs for all nodes or a requested OD subset."""

    edge_ids = {edge.edge_id for edge in edges}
    if set(edge_travel_minutes) != edge_ids:
        raise ValueError("edge travel costs must match transport edge IDs")
    if nodes is not None:
        if origins is not None or destinations is not None:
            raise ValueError("nodes cannot be combined with origins or destinations")
        origins = nodes
        destinations = nodes
    if origins is None or destinations is None:
        raise ValueError("provide nodes or both origins and destinations")

    ordered_origins = tuple(sorted(set(origins)))
    destination_set = frozenset(destinations)
    if not ordered_origins or not destination_set:
        return {}
    best_across_modes: dict[str, float] = {}
    for mode in TransportMode:
        adjacency: dict[str, list[TransportEdgeSpec]] = {}
        for edge in edges:
            if edge.mode is mode:
                adjacency.setdefault(edge.from_node, []).append(edge)
        for outgoing in adjacency.values():
            outgoing.sort(key=lambda edge: edge.edge_id)
        for origin in ordered_origins:
            queue: list[tuple[float, str]] = [(0.0, origin)]
            best: dict[str, float] = {origin: 0.0}
            remaining = set(destination_set)
            while queue:
                cost, node = heapq.heappop(queue)
                if cost > best.get(node, math.inf):
                    continue
                if node in remaining:
                    key = f"{origin}->{node}"
                    best_across_modes[key] = min(best_across_modes.get(key, math.inf), cost)
                    remaining.remove(node)
                    if not remaining:
                        break
                for edge in adjacency.get(node, []):
                    candidate = (
                        cost + edge_travel_minutes[edge.edge_id] + edge.generalized_penalty_minutes
                    )
                    if candidate < best.get(edge.to_node, math.inf):
                        best[edge.to_node] = candidate
                        heapq.heappush(queue, (candidate, edge.to_node))
    return best_across_modes


def _logit_shares(
    paths: dict[TransportMode, tuple[float, tuple[str, ...]]],
    theta: float,
) -> dict[TransportMode, float]:
    minimum = min(cost for cost, _path in paths.values())
    weights = {mode: math.exp(-theta * (cost - minimum)) for mode, (cost, _path) in paths.items()}
    total = sum(weights.values())
    return {mode: weight / total for mode, weight in weights.items()}


@lru_cache(maxsize=64)
def _assign_transport_cached(
    edges: tuple[TransportEdgeSpec, ...],
    od_pairs: tuple[ODPair, ...],
    spec: TransportAssignmentSpec,
) -> TransportAssignmentResult:
    """Assign demand with modal logit and deterministic MSA capacity feedback."""

    ordered_edges = tuple(sorted(edges, key=lambda edge: edge.edge_id))
    edge_ids = tuple(edge.edge_id for edge in ordered_edges)
    if len(edge_ids) != len(set(edge_ids)):
        raise ValueError("edge_id values must be unique")
    ordered_ods = tuple(sorted(od_pairs, key=lambda od: (od.origin, od.destination, od.demand)))
    destinations_by_origin = {
        origin: frozenset(od.destination for od in ordered_ods if od.origin == origin)
        for origin in sorted({od.origin for od in ordered_ods})
    }
    adjacency_by_mode = _modal_adjacency(ordered_edges)
    flows = dict.fromkeys(edge_ids, 0.0)

    for iteration in range(1, spec.iterations + 1):
        costs = {
            edge.edge_id: _travel_minutes(edge, flows[edge.edge_id], spec) for edge in ordered_edges
        }
        trees = _path_trees(adjacency_by_mode, costs, destinations_by_origin)
        assigned = dict.fromkeys(edge_ids, 0.0)
        for od in ordered_ods:
            paths = _mode_paths_from_trees(trees, od)
            shares = _logit_shares(paths, spec.logit_theta)
            for mode, share in shares.items():
                for edge_id in paths[mode][1]:
                    assigned[edge_id] += od.demand * share
        step = 1.0 / iteration
        flows = {
            edge_id: flows[edge_id] + step * (assigned[edge_id] - flows[edge_id])
            for edge_id in edge_ids
        }

    travel = {
        edge.edge_id: _travel_minutes(edge, flows[edge.edge_id], spec) for edge in ordered_edges
    }
    od_mode_shares: dict[str, dict[TransportMode, float]] = {}
    od_mode_costs: dict[str, dict[TransportMode, float]] = {}
    final_trees = _path_trees(adjacency_by_mode, travel, destinations_by_origin)
    for od in ordered_ods:
        key = f"{od.origin}->{od.destination}"
        paths = _mode_paths_from_trees(final_trees, od)
        od_mode_shares[key] = _logit_shares(paths, spec.logit_theta)
        od_mode_costs[key] = {mode: cost for mode, (cost, _path) in paths.items()}

    return TransportAssignmentResult(
        edge_flows=flows,
        edge_travel_minutes=travel,
        od_mode_shares=od_mode_shares,
        od_mode_costs=od_mode_costs,
    )


def assign_transport(
    edges: tuple[TransportEdgeSpec, ...],
    od_pairs: tuple[ODPair, ...],
    spec: TransportAssignmentSpec,
) -> TransportAssignmentResult:
    """Assign demand with a bounded pure-result cache and defensive copy."""

    ordered_edges = tuple(sorted(edges, key=lambda edge: edge.edge_id))
    ordered_ods = tuple(sorted(od_pairs, key=lambda od: (od.origin, od.destination, od.demand)))
    result = _assign_transport_cached(ordered_edges, ordered_ods, spec)
    return result.model_copy(
        update={
            "edge_flows": dict(result.edge_flows),
            "edge_travel_minutes": dict(result.edge_travel_minutes),
            "od_mode_shares": {key: dict(shares) for key, shares in result.od_mode_shares.items()},
            "od_mode_costs": {key: dict(costs) for key, costs in result.od_mode_costs.items()},
        }
    )


def opportunity_accessibility(
    *,
    costs: dict[str, float],
    opportunities: dict[str, float],
    decay: float,
) -> dict[str, float]:
    """Compute normalized gravity accessibility from ``origin->destination`` costs."""

    if decay < 0.0:
        raise ValueError("decay must be non-negative")
    total_opportunities = sum(opportunities.values())
    if total_opportunities <= 0.0:
        raise ValueError("opportunities must have positive total weight")
    values: dict[str, float] = {}
    for key, cost in sorted(costs.items()):
        origin, destination = key.split("->", 1)
        if destination not in opportunities:
            raise ValueError(f"missing opportunity weight for destination {destination}")
        values[origin] = values.get(origin, 0.0) + opportunities[destination] * math.exp(
            -decay * cost
        )
    return {origin: value / total_opportunities for origin, value in values.items()}
