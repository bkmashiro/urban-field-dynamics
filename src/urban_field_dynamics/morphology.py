"""Spatial morphology observers and robust decision-category classification."""

from __future__ import annotations

import math
from collections import Counter
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.campaign import CampaignResult
from urban_field_dynamics.contracts import LandUse
from urban_field_dynamics.spatial import StylizedGrid
from urban_field_dynamics.world import WorldResult

UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]


class DecisionCategory(StrEnum):
    """Decision classes derived from cross-world and cross-policy stability."""

    COMMITMENT = "commitment"
    OPTIONALITY = "optionality"
    TRIGGER = "trigger"


class DecisionClassificationSpec(BaseModel):
    """Declared probability thresholds and policy arms used for classification."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    arm_ids: Annotated[tuple[str, ...], Field(min_length=2)]
    commitment_probability: UnitInterval = 0.8
    trigger_probability_range: UnitInterval = 0.3

    @model_validator(mode="after")
    def validate_arm_ids(self) -> DecisionClassificationSpec:
        if len(self.arm_ids) != len(set(self.arm_ids)):
            raise ValueError("arm_ids must be unique")
        return self


class UnitDecisionClassification(BaseModel):
    """One unit's transparent probability evidence and resulting class."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    unit_id: str
    category: DecisionCategory
    commitment_outcome: Literal["keep", "transition"] | None
    transition_probability_by_arm: dict[str, UnitInterval]


class DecisionClassificationResult(BaseModel):
    """Stable row-major classifications for all units present in selected arms."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    arm_ids: tuple[str, ...]
    matched_world_ids: tuple[int, ...]
    units: tuple[UnitDecisionClassification, ...]


class MorphologyObservation(BaseModel):
    """Non-causal spatial summary of one completed world."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    redevelopment_share: UnitInterval
    normalized_land_use_entropy: UnitInterval
    adjacency_mixing_rate: UnitInterval
    corridor_redevelopment_share: UnitInterval
    focus_zone_redevelopment_share: dict[str, UnitInterval]


def classify_decision_categories(
    result: CampaignResult,
    spec: DecisionClassificationSpec,
) -> DecisionClassificationResult:
    """Classify robust keep/transition, policy-sensitive, and unresolved units."""

    by_arm: dict[str, dict[int, WorldResult]] = {}
    for run in result.runs:
        if run.arm_id in spec.arm_ids:
            by_arm.setdefault(run.arm_id, {})[run.world.world_id] = run.world
    missing = [arm_id for arm_id in spec.arm_ids if arm_id not in by_arm]
    if missing:
        raise ValueError(f"campaign arm not found: {', '.join(missing)}")
    matched_world_ids = tuple(sorted(by_arm[spec.arm_ids[0]]))
    if any(tuple(sorted(by_arm[arm_id])) != matched_world_ids for arm_id in spec.arm_ids):
        raise ValueError("selected arms must contain identical matched world IDs")

    first_world = by_arm[spec.arm_ids[0]][matched_world_ids[0]]
    unit_ids = tuple(sorted(first_world.redevelopment_years))
    if any(
        tuple(sorted(world.redevelopment_years)) != unit_ids
        for arm_id in spec.arm_ids
        for world in by_arm[arm_id].values()
    ):
        raise ValueError("selected worlds must contain identical spatial unit IDs")

    classifications: list[UnitDecisionClassification] = []
    for unit_id in unit_ids:
        probabilities = {
            arm_id: sum(
                by_arm[arm_id][world_id].redevelopment_years[unit_id] is not None
                for world_id in matched_world_ids
            )
            / len(matched_world_ids)
            for arm_id in spec.arm_ids
        }
        minimum = min(probabilities.values())
        maximum = max(probabilities.values())
        category = DecisionCategory.OPTIONALITY
        outcome: Literal["keep", "transition"] | None = None
        if maximum <= 1.0 - spec.commitment_probability:
            category = DecisionCategory.COMMITMENT
            outcome = "keep"
        elif minimum >= spec.commitment_probability:
            category = DecisionCategory.COMMITMENT
            outcome = "transition"
        elif maximum - minimum >= spec.trigger_probability_range:
            category = DecisionCategory.TRIGGER
        classifications.append(
            UnitDecisionClassification(
                unit_id=unit_id,
                category=category,
                commitment_outcome=outcome,
                transition_probability_by_arm=probabilities,
            )
        )
    return DecisionClassificationResult(
        arm_ids=spec.arm_ids,
        matched_world_ids=matched_world_ids,
        units=tuple(classifications),
    )


def observe_world_morphology(world: WorldResult, grid: StylizedGrid) -> MorphologyObservation:
    """Measure change, diversity, adjacency mixing, and labelled subset outcomes."""

    grid_by_id = {unit.spec.unit_id: unit for unit in grid.units}
    if set(grid_by_id) != set(world.final_uses) or set(grid_by_id) != set(
        world.redevelopment_years
    ):
        raise ValueError("world and grid must contain identical spatial unit IDs")
    total = len(grid.units)
    redevelopment_share = world.redevelopment_count / total

    counts = Counter(world.final_uses.values())
    entropy = -sum(
        (count / total) * math.log(count / total) for count in counts.values() if count > 0
    )
    normalized_entropy = entropy / math.log(len(LandUse))

    edges = {
        tuple(sorted((unit.spec.unit_id, neighbor_id)))
        for unit in grid.units
        for neighbor_id in unit.neighbor_ids
    }
    mixed_edges = sum(world.final_uses[left] != world.final_uses[right] for left, right in edges)
    adjacency_mixing = mixed_edges / len(edges) if edges else 0.0

    corridor_ids = [unit.spec.unit_id for unit in grid.units if unit.is_corridor_observer]
    corridor_share = sum(
        world.redevelopment_years[unit_id] is not None for unit_id in corridor_ids
    ) / len(corridor_ids)

    focus_ids: dict[str, list[str]] = {}
    for unit in grid.units:
        if unit.focus_zone_id is not None:
            focus_ids.setdefault(unit.focus_zone_id, []).append(unit.spec.unit_id)
    focus_shares = {
        zone_id: sum(world.redevelopment_years[unit_id] is not None for unit_id in zone_unit_ids)
        / len(zone_unit_ids)
        for zone_id, zone_unit_ids in sorted(focus_ids.items())
    }
    return MorphologyObservation(
        redevelopment_share=redevelopment_share,
        normalized_land_use_entropy=normalized_entropy,
        adjacency_mixing_rate=adjacency_mixing,
        corridor_redevelopment_share=corridor_share,
        focus_zone_redevelopment_share=focus_shares,
    )
