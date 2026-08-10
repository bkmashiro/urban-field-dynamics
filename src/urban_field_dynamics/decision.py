"""Transparent Pareto, tail-harm, and threshold-crossing diagnostics."""

from __future__ import annotations

from enum import StrEnum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.analysis import PairedConvergenceDiagnostic, QualificationDiagnostics
from urban_field_dynamics.campaign import CampaignResult, CampaignSpec
from urban_field_dynamics.equity import CampaignEquitySummary, world_group_metrics


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


class LeverageStatus(StrEnum):
    AVAILABLE = "available"
    NON_POSITIVE_INCREMENTAL_COST = "non_positive_incremental_cost"


class LeverageRatio(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    arm_id: str
    objective_id: str
    direction: ObjectiveDirection
    baseline_value: float
    arm_value: float
    numerator_improvement: float
    baseline_public_cost: float
    arm_public_cost: float
    incremental_public_cost: float
    denominator_provenance: str
    ratio_per_cost_unit: float | None = None
    status: LeverageStatus


class GroupTailHarmSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    baseline_arm: str
    comparator_arm: str
    group_id: str
    metric: str
    direction: ObjectiveDirection
    world_count: int = Field(gt=0)
    harmed_world_count: int = Field(ge=0)
    harmed_fraction: float = Field(ge=0.0, le=1.0)
    worst_harm: float = Field(ge=0.0)
    q90_harm: float = Field(ge=0.0)


class CampaignDecisionDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    campaign_id: str
    pareto: ParetoResult
    tail_harm: dict[str, TailHarmSummary]
    leverage: dict[str, LeverageRatio] = Field(default_factory=dict)
    group_tail_harm: dict[str, GroupTailHarmSummary] = Field(default_factory=dict)


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


def _policy_leverage(
    result: CampaignResult,
    policy_arm_ids: tuple[str, ...],
) -> dict[str, LeverageRatio]:
    baseline = result.summary.arms[policy_arm_ids[0]]
    baseline_cost = baseline.mean_cumulative_public_spend
    if baseline_cost is None:
        return {}
    objectives = (
        ("accessibility", ObjectiveDirection.MAXIMIZE, "mean_final_accessibility"),
        ("environment", ObjectiveDirection.MAXIMIZE, "mean_final_environment_quality"),
        ("rent", ObjectiveDirection.MINIMIZE, "mean_final_rent"),
        ("service-unmet", ObjectiveDirection.MINIMIZE, "mean_final_service_unmet_demand"),
        ("unemployment", ObjectiveDirection.MINIMIZE, "mean_final_unemployment_rate"),
    )
    evidence: dict[str, LeverageRatio] = {}
    for arm_id in policy_arm_ids[1:]:
        arm = result.summary.arms[arm_id]
        if arm.mean_cumulative_public_spend is None:
            continue
        incremental_cost = arm.mean_cumulative_public_spend - baseline_cost
        status = (
            LeverageStatus.AVAILABLE
            if incremental_cost > 0.0
            else LeverageStatus.NON_POSITIVE_INCREMENTAL_COST
        )
        for objective_id, direction, attribute in objectives:
            baseline_value = getattr(baseline, attribute)
            arm_value = getattr(arm, attribute)
            if baseline_value is None or arm_value is None:
                continue
            improvement = float(arm_value) - float(baseline_value)
            if direction is ObjectiveDirection.MINIMIZE:
                improvement = -improvement
            key = f"{arm_id}:{objective_id}"
            evidence[key] = LeverageRatio(
                arm_id=arm_id,
                objective_id=objective_id,
                direction=direction,
                baseline_value=float(baseline_value),
                arm_value=float(arm_value),
                numerator_improvement=improvement,
                baseline_public_cost=baseline_cost,
                arm_public_cost=arm.mean_cumulative_public_spend,
                incremental_public_cost=incremental_cost,
                denominator_provenance=(
                    "campaign mean cumulative synthetic public spend minus p0 campaign mean"
                ),
                ratio_per_cost_unit=(
                    improvement / incremental_cost if status is LeverageStatus.AVAILABLE else None
                ),
                status=status,
            )
    return evidence


def _group_tail_harm(
    spec: CampaignSpec,
    result: CampaignResult,
    policy_arm_ids: tuple[str, ...],
) -> dict[str, GroupTailHarmSummary]:
    runs = {(run.arm_id, run.world.world_id): run.world for run in result.runs}
    world_ids = result.summary.matched_world_ids
    baseline_id = policy_arm_ids[0]
    metrics = {
        "accessibility": ObjectiveDirection.MAXIMIZE,
        "environment": ObjectiveDirection.MAXIMIZE,
        "service": ObjectiveDirection.MAXIMIZE,
        "rent_burden": ObjectiveDirection.MINIMIZE,
        "relocation": ObjectiveDirection.MINIMIZE,
        "unemployment": ObjectiveDirection.MINIMIZE,
        "commute": ObjectiveDirection.MINIMIZE,
    }
    baseline = {
        world_id: world_group_metrics(spec, runs[(baseline_id, world_id)]) for world_id in world_ids
    }
    evidence: dict[str, GroupTailHarmSummary] = {}
    for arm_id in policy_arm_ids[1:]:
        comparator = {
            world_id: world_group_metrics(spec, runs[(arm_id, world_id)]) for world_id in world_ids
        }
        group_ids = sorted(baseline[world_ids[0]])
        for group_id in group_ids:
            for metric, direction in metrics.items():
                pairs = [
                    (
                        baseline[world_id][group_id][metric],
                        comparator[world_id][group_id][metric],
                    )
                    for world_id in world_ids
                ]
                if any(left is None or right is None for left, right in pairs):
                    continue
                improvements = [float(right) - float(left) for left, right in pairs]
                if direction is ObjectiveDirection.MINIMIZE:
                    improvements = [-value for value in improvements]
                harms = [max(0.0, -value) for value in improvements]
                key = f"{arm_id}:{group_id}:{metric}"
                evidence[key] = GroupTailHarmSummary(
                    baseline_arm=baseline_id,
                    comparator_arm=arm_id,
                    group_id=group_id,
                    metric=metric,
                    direction=direction,
                    world_count=len(world_ids),
                    harmed_world_count=sum(value > 0.0 for value in harms),
                    harmed_fraction=sum(value > 0.0 for value in harms) / len(harms),
                    worst_harm=max(harms),
                    q90_harm=float(np.quantile(harms, 0.9)),
                )
    return evidence


def campaign_decision_diagnostics(
    result: CampaignResult,
    equity: CampaignEquitySummary,
    qualification: QualificationDiagnostics,
    *,
    spec: CampaignSpec | None = None,
    policy_arm_ids: tuple[str, ...] = ("p0", "p1", "p2", "p3"),
) -> CampaignDecisionDiagnostics:
    """Build an unweighted Pareto front and matched-world tail-harm bundle."""

    if len({result.campaign_id, equity.campaign_id, qualification.campaign_id}) != 1:
        raise ValueError("decision inputs must share one campaign ID")
    if spec is not None and spec.campaign_id != result.campaign_id:
        raise ValueError("decision campaign spec must share the result campaign ID")
    objectives = [
        ObjectiveSpec(objective_id="accessibility", direction=ObjectiveDirection.MAXIMIZE),
        ObjectiveSpec(objective_id="environment", direction=ObjectiveDirection.MAXIMIZE),
        ObjectiveSpec(objective_id="rent", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="accessibility-gap", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="environment-gap", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="service-gap", direction=ObjectiveDirection.MINIMIZE),
        ObjectiveSpec(objective_id="rent-burden-gap", direction=ObjectiveDirection.MINIMIZE),
    ]
    labor_available = all(
        result.summary.arms.get(arm_id) is not None
        and result.summary.arms[arm_id].mean_final_unemployment_rate is not None
        and result.summary.arms[arm_id].mean_final_commute_minutes is not None
        and equity.arms.get(arm_id) is not None
        and equity.arms[arm_id].unemployment_rate_gap is not None
        and equity.arms[arm_id].commute_minutes_gap is not None
        for arm_id in policy_arm_ids
    )
    if labor_available:
        objectives.extend(
            (
                ObjectiveSpec(objective_id="unemployment", direction=ObjectiveDirection.MINIMIZE),
                ObjectiveSpec(objective_id="commute", direction=ObjectiveDirection.MINIMIZE),
                ObjectiveSpec(
                    objective_id="unemployment-gap", direction=ObjectiveDirection.MINIMIZE
                ),
                ObjectiveSpec(objective_id="commute-gap", direction=ObjectiveDirection.MINIMIZE),
            )
        )
    infrastructure_available = all(
        result.summary.arms.get(arm_id) is not None
        and result.summary.arms[arm_id].mean_cumulative_public_spend is not None
        and result.summary.arms[arm_id].mean_final_service_unmet_demand is not None
        for arm_id in policy_arm_ids
    )
    if infrastructure_available:
        objectives.extend(
            (
                ObjectiveSpec(objective_id="public-cost", direction=ObjectiveDirection.MINIMIZE),
                ObjectiveSpec(objective_id="service-unmet", direction=ObjectiveDirection.MINIMIZE),
            )
        )
    vectors: list[ArmObjectiveVector] = []
    for arm_id in policy_arm_ids:
        if arm_id not in result.summary.arms or arm_id not in equity.arms:
            raise ValueError(f"policy arm missing from decision inputs: {arm_id}")
        summary = result.summary.arms[arm_id]
        group = equity.arms[arm_id]
        values = {
            "accessibility": summary.mean_final_accessibility,
            "environment": summary.mean_final_environment_quality,
            "rent": summary.mean_final_rent,
            "accessibility-gap": group.accessibility_gap,
            "environment-gap": group.environment_quality_gap,
            "service-gap": group.service_access_gap,
            "rent-burden-gap": group.rent_burden_gap,
        }
        if labor_available:
            values.update(
                {
                    "unemployment": float(summary.mean_final_unemployment_rate),
                    "commute": float(summary.mean_final_commute_minutes),
                    "unemployment-gap": float(group.unemployment_rate_gap),
                    "commute-gap": float(group.commute_minutes_gap),
                }
            )
        if infrastructure_available:
            values.update(
                {
                    "public-cost": float(summary.mean_cumulative_public_spend),
                    "service-unmet": float(summary.mean_final_service_unmet_demand),
                }
            )
        vectors.append(ArmObjectiveVector(arm_id=arm_id, values=values))
    return CampaignDecisionDiagnostics(
        campaign_id=result.campaign_id,
        pareto=pareto_front(tuple(vectors), objectives),
        tail_harm={
            comparison_id: summarize_tail_harm(diagnostic)
            for comparison_id, diagnostic in qualification.comparisons.items()
        },
        leverage=_policy_leverage(result, policy_arm_ids),
        group_tail_harm=(
            _group_tail_harm(spec, result, policy_arm_ids) if spec is not None else {}
        ),
    )
