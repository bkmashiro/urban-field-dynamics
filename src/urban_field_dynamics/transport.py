"""Auditable multimodal transport assignment surrogate."""

from __future__ import annotations

import heapq
import math
from enum import StrEnum
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


def _shortest_path(
    edges: tuple[TransportEdgeSpec, ...],
    costs: dict[str, float],
    *,
    origin: str,
    destination: str,
    mode: TransportMode,
) -> tuple[float, tuple[str, ...]] | None:
    adjacency: dict[str, list[TransportEdgeSpec]] = {}
    for edge in edges:
        if edge.mode is mode:
            adjacency.setdefault(edge.from_node, []).append(edge)
    for outgoing in adjacency.values():
        outgoing.sort(key=lambda edge: edge.edge_id)

    queue: list[tuple[float, str, tuple[str, ...]]] = [(0.0, origin, ())]
    best: dict[str, float] = {origin: 0.0}
    while queue:
        cost, node, path = heapq.heappop(queue)
        if cost > best.get(node, math.inf):
            continue
        if node == destination:
            return cost, path
        for edge in adjacency.get(node, []):
            candidate = cost + costs[edge.edge_id] + edge.generalized_penalty_minutes
            if candidate < best.get(edge.to_node, math.inf):
                best[edge.to_node] = candidate
                heapq.heappush(queue, (candidate, edge.to_node, (*path, edge.edge_id)))
    return None


def _mode_paths(
    edges: tuple[TransportEdgeSpec, ...],
    costs: dict[str, float],
    od: ODPair,
) -> dict[TransportMode, tuple[float, tuple[str, ...]]]:
    paths: dict[TransportMode, tuple[float, tuple[str, ...]]] = {}
    for mode in TransportMode:
        path = _shortest_path(
            edges,
            costs,
            origin=od.origin,
            destination=od.destination,
            mode=mode,
        )
        if path is not None:
            paths[mode] = path
    if not paths:
        raise ValueError(f"no modal path for OD {od.origin}->{od.destination}")
    return paths


def _logit_shares(
    paths: dict[TransportMode, tuple[float, tuple[str, ...]]],
    theta: float,
) -> dict[TransportMode, float]:
    minimum = min(cost for cost, _path in paths.values())
    weights = {mode: math.exp(-theta * (cost - minimum)) for mode, (cost, _path) in paths.items()}
    total = sum(weights.values())
    return {mode: weight / total for mode, weight in weights.items()}


def assign_transport(
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
    flows = dict.fromkeys(edge_ids, 0.0)

    for iteration in range(1, spec.iterations + 1):
        costs = {
            edge.edge_id: _travel_minutes(edge, flows[edge.edge_id], spec) for edge in ordered_edges
        }
        assigned = dict.fromkeys(edge_ids, 0.0)
        for od in ordered_ods:
            paths = _mode_paths(ordered_edges, costs, od)
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
    for od in ordered_ods:
        key = f"{od.origin}->{od.destination}"
        paths = _mode_paths(ordered_edges, travel, od)
        od_mode_shares[key] = _logit_shares(paths, spec.logit_theta)
        od_mode_costs[key] = {mode: cost for mode, (cost, _path) in paths.items()}

    return TransportAssignmentResult(
        edge_flows=flows,
        edge_travel_minutes=travel,
        od_mode_shares=od_mode_shares,
        od_mode_costs=od_mode_costs,
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
