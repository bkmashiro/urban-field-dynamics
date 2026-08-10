"""Transparent Pareto, tail-harm, and threshold-crossing diagnostics."""

from __future__ import annotations

from enum import StrEnum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.analysis import PairedConvergenceDiagnostic, QualificationDiagnostics
from urban_field_dynamics.campaign import CampaignResult
from urban_field_dynamics.equity import CampaignEquitySummary


class ObjectiveDirection(StrEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class ObjectiveSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    objective_id: str
    direction: ObjectiveDirection
    tolerance: float = Field(default=0.0, ge=0.0)


class ArmObjectiveVector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    arm_id: str
    values: dict[str, float]


class ParetoResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    objectives: tuple[ObjectiveSpec, ...]
    nondominated_arm_ids: tuple[str, ...]
    dominated_by: dict[str, tuple[str, ...]]


class ThresholdCrossing(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    lower_level: float
    upper_level: float
    lower_response: float
    upper_response: float


class ThresholdCrossingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    threshold: float
    crossings: tuple[ThresholdCrossing, ...]


class TailHarmSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    baseline_arm: str
    comparator_arm: str
    harmed_world_count: int = Field(ge=0)
    harmed_fraction: float = Field(ge=0.0, le=1.0)
    worst_harm: float = Field(ge=0.0)
    q90_harm: float = Field(ge=0.0)


class CampaignDecisionDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    campaign_id: str
    pareto: ParetoResult
    tail_harm: dict[str, TailHarmSummary]


def _dominates(
    candidate: ArmObjectiveVector,
    other: ArmObjectiveVector,
    objectives: tuple[ObjectiveSpec, ...],
) -> bool:
    no_worse = True
    strictly_better = False
    for objective in objectives:
        candidate_value = candidate.values[objective.objective_id]
        other_value = other.values[objective.objective_id]
        delta = candidate_value - other_value
        if objective.direction is ObjectiveDirection.MINIMIZE:
            delta = -delta
        if delta < -objective.tolerance:
            no_worse = False
            break
        if delta > objective.tolerance:
            strictly_better = True
    return no_worse and strictly_better


def pareto_front(
    outcomes: tuple[ArmObjectiveVector, ...],
    objectives: tuple[ObjectiveSpec, ...],
) -> ParetoResult:
    if not outcomes or not objectives:
        raise ValueError("Pareto analysis requires outcomes and objectives")
    objective_ids = tuple(objective.objective_id for objective in objectives)
    if len(set(objective_ids)) != len(objective_ids):
        raise ValueError("objective IDs must be unique")
    arm_ids = tuple(outcome.arm_id for outcome in outcomes)
    if len(set(arm_ids)) != len(arm_ids):
        raise ValueError("arm IDs must be unique")
    required = set(objective_ids)
    if any(set(outcome.values) != required for outcome in outcomes):
        raise ValueError("every arm must provide exactly the declared objectives")

    dominators = {
        outcome.arm_id: tuple(
            sorted(
                candidate.arm_id
                for candidate in outcomes
                if candidate.arm_id != outcome.arm_id and _dominates(candidate, outcome, objectives)
            )
        )
        for outcome in outcomes
    }
    return ParetoResult(
        objectives=objectives,
        nondominated_arm_ids=tuple(sorted(arm_id for arm_id in arm_ids if not dominators[arm_id])),
        dominated_by={arm_id: values for arm_id, values in dominators.items() if values},
    )


def detect_threshold_crossings(
    *,
    levels: tuple[float, ...],
    responses: tuple[float, ...],
    threshold: float,
) -> ThresholdCrossingResult:
    if len(levels) != len(responses) or len(levels) < 2:
        raise ValueError("levels and responses must have equal length of at least two")
    if any(right <= left for left, right in zip(levels, levels[1:], strict=False)):
        raise ValueError("levels must be strictly increasing")
    crossings: list[ThresholdCrossing] = []
    for index in range(len(levels) - 1):
        lower_response = responses[index]
        upper_response = responses[index + 1]
        lower_delta = lower_response - threshold
        upper_delta = upper_response - threshold
        if lower_delta == 0.0 or upper_delta == 0.0 or lower_delta * upper_delta < 0.0:
            crossings.append(
                ThresholdCrossing(
                    lower_level=levels[index],
                    upper_level=levels[index + 1],
                    lower_response=lower_response,
                    upper_response=upper_response,
                )
            )
    return ThresholdCrossingResult(threshold=threshold, crossings=tuple(crossings))


def summarize_tail_harm(diagnostic: PairedConvergenceDiagnostic) -> TailHarmSummary:
    harms = tuple(
        max(0.0, -delta if diagnostic.higher_is_better else delta) for delta in diagnostic.deltas
    )
    return TailHarmSummary(
        baseline_arm=diagnostic.baseline_arm,
        comparator_arm=diagnostic.comparator_arm,
        harmed_world_count=sum(harm > 0.0 for harm in harms),
        harmed_fraction=sum(harm > 0.0 for harm in harms) / len(harms),
        worst_harm=max(harms),
        q90_harm=float(np.quantile(harms, 0.9)),
    )


def campaign_decision_diagnostics(
    result: CampaignResult,
    equity: CampaignEquitySummary,
    qualification: QualificationDiagnostics,
    *,
    policy_arm_ids: tuple[str, ...] = ("p0", "p1", "p2", "p3"),
) -> CampaignDecisionDiagnostics:
    """Build an unweighted Pareto front and matched-world tail-harm bundle."""

    if len({result.campaign_id, equity.campaign_id, qualification.campaign_id}) != 1:
        raise ValueError("decision inputs must share one campaign ID")
    objectives = (
        ObjectiveSpec(objective_id="accessibility", direction=ObjectiveDirection.MAXIMIZE),
        ObjectiveSpec(objective_id="environment", direction=ObjectiveDirection.MAXIMIZE),
        ObjectiveSpec(objective_id="rent", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="accessibility-gap", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="environment-gap", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="service-gap", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="rent-burden-gap", direction=ObjectiveDirection.MINIMIZE),
    )
    vectors: list[ArmObjectiveVector] = []
    for arm_id in policy_arm_ids:
        if arm_id not in result.summary.arms or arm_id not in equity.arms:
            raise ValueError(f"policy arm missing from decision inputs: {arm_id}")
        summary = result.summary.arms[arm_id]
        group = equity.arms[arm_id]
        vectors.append(
            ArmObjectiveVector(
                arm_id=arm_id,
                values={
                    "accessibility": summary.mean_final_accessibility,
                    "environment": summary.mean_final_environment_quality,
                    "rent": summary.mean_final_rent,
                    "accessibility-gap": group.accessibility_gap,
                    "environment-gap": group.environment_quality_gap,
                    "service-gap": group.service_access_gap,
                    "rent-burden-gap": group.rent_burden_gap,
                },
            )
        )
    return CampaignDecisionDiagnostics(
        campaign_id=result.campaign_id,
        pareto=pareto_front(tuple(vectors), objectives),
        tail_harm={
            comparison_id: summarize_tail_harm(diagnostic)
            for comparison_id, diagnostic in qualification.comparisons.items()
        },
    )
