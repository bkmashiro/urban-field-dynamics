"""Matched-world descriptive statistics and convergence diagnostics."""

from __future__ import annotations

import math
import statistics
from enum import StrEnum
from typing import Annotated

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.campaign import CampaignResult
from urban_field_dynamics.world import WorldResult


class CampaignMetric(StrEnum):
    """Per-world scalar metrics supported by paired diagnostics."""

    REDEVELOPMENTS = "redevelopments"
    FINAL_ACCESSIBILITY = "final_accessibility"
    FINAL_ENVIRONMENT_QUALITY = "final_environment_quality"
    FINAL_RENT = "final_rent"
    SEASONAL_HEAT_RANGE = "seasonal_heat_range"
    FINAL_SERVICE_ACCESS = "final_service_access"
    FINAL_POPULATION = "final_population"
    FINAL_EMPLOYMENT = "final_employment"


class ConvergencePoint(BaseModel):
    """Descriptive paired-delta statistics at one prefix sample size."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    world_count: Annotated[int, Field(gt=0)]
    mean_delta: float
    median_delta: float
    q10_delta: float
    q90_delta: float
    standard_error: Annotated[float, Field(ge=0.0)]
    ci95_lower: float
    ci95_upper: float


class PairedConvergenceDiagnostic(BaseModel):
    """Matched-world delta trace and prefix convergence statistics."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    baseline_arm: str
    comparator_arm: str
    metric: CampaignMetric
    higher_is_better: bool
    world_ids: tuple[int, ...]
    deltas: tuple[float, ...]
    harmed_world_count: Annotated[int, Field(ge=0)]
    checkpoints: tuple[ConvergencePoint, ...]


class QualificationDiagnostics(BaseModel):
    """Fixed integrated qualification comparisons with shared checkpoints."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    campaign_id: str
    world_count: Annotated[int, Field(gt=0)]
    comparisons: dict[str, PairedConvergenceDiagnostic]


def _mean(values: dict[str, float]) -> float:
    return sum(values.values()) / len(values) if values else 0.0


def _seasonal_heat_range(world: WorldResult) -> float:
    ranges: list[float] = []
    for seasonal_results in world.environment_traces.values():
        unit_ids = {
            unit_id for unit_results in seasonal_results.values() for unit_id in unit_results
        }
        for unit_id in unit_ids:
            values = [unit_results[unit_id].heat for unit_results in seasonal_results.values()]
            ranges.append(max(values) - min(values))
    return sum(ranges) / len(ranges) if ranges else 0.0


def _service_access(world: WorldResult) -> float:
    values: list[float] = []
    for unit_id, quality in world.final_service_quality.items():
        capacity = world.final_service_capacity.get(unit_id)
        if capacity is None:
            values.append(quality)
            continue
        demand = world.final_households.get(unit_id, 0.0)
        values.append(quality * min(1.0, capacity / max(demand, 1.0)))
    return statistics.fmean(values) if values else 0.0


def _metric(world: WorldResult, metric: CampaignMetric) -> float:
    if metric is CampaignMetric.REDEVELOPMENTS:
        return float(world.redevelopment_count)
    if metric is CampaignMetric.FINAL_ACCESSIBILITY:
        return _mean(world.final_accessibility)
    if metric is CampaignMetric.FINAL_ENVIRONMENT_QUALITY:
        return _mean(world.final_environment_quality)
    if metric is CampaignMetric.FINAL_RENT:
        return _mean(world.final_rents)
    if metric is CampaignMetric.SEASONAL_HEAT_RANGE:
        return _seasonal_heat_range(world)
    if metric is CampaignMetric.FINAL_SERVICE_ACCESS:
        return _service_access(world)
    if metric is CampaignMetric.FINAL_POPULATION:
        return sum(world.final_household_populations.values())
    if metric is CampaignMetric.FINAL_EMPLOYMENT:
        return sum(world.final_firm_employees.values())
    raise AssertionError(f"unsupported campaign metric: {metric}")


def _point(values: tuple[float, ...]) -> ConvergencePoint:
    count = len(values)
    mean_delta = statistics.fmean(values)
    standard_error = statistics.stdev(values) / math.sqrt(count) if count > 1 else 0.0
    return ConvergencePoint(
        world_count=count,
        mean_delta=mean_delta,
        median_delta=statistics.median(values),
        q10_delta=float(np.quantile(values, 0.1)),
        q90_delta=float(np.quantile(values, 0.9)),
        standard_error=standard_error,
        ci95_lower=mean_delta - 1.96 * standard_error,
        ci95_upper=mean_delta + 1.96 * standard_error,
    )


def paired_convergence(
    result: CampaignResult,
    *,
    baseline_arm: str,
    comparator_arm: str,
    metric: CampaignMetric,
    checkpoints: tuple[int, ...] = (8, 16, 32, 64),
    higher_is_better: bool = True,
) -> PairedConvergenceDiagnostic:
    """Compare arm values by matched world and summarize stable prefix sizes."""

    by_arm: dict[str, dict[int, WorldResult]] = {}
    for run in result.runs:
        by_arm.setdefault(run.arm_id, {})[run.world.world_id] = run.world
    missing = [arm for arm in (baseline_arm, comparator_arm) if arm not in by_arm]
    if missing:
        raise ValueError(f"campaign arm not found: {', '.join(missing)}")

    baseline = by_arm[baseline_arm]
    comparator = by_arm[comparator_arm]
    if set(baseline) != set(comparator):
        raise ValueError("campaign arms do not contain identical matched world IDs")
    world_ids = tuple(sorted(baseline))
    deltas = tuple(
        _metric(comparator[world_id], metric) - _metric(baseline[world_id], metric)
        for world_id in world_ids
    )

    valid_checkpoints = tuple(sorted(set(checkpoints)))
    if not valid_checkpoints or valid_checkpoints[0] <= 0 or valid_checkpoints[-1] > len(deltas):
        raise ValueError("checkpoints must be positive and no larger than matched world count")
    harmed = sum(delta < 0.0 if higher_is_better else delta > 0.0 for delta in deltas)
    return PairedConvergenceDiagnostic(
        baseline_arm=baseline_arm,
        comparator_arm=comparator_arm,
        metric=metric,
        higher_is_better=higher_is_better,
        world_ids=world_ids,
        deltas=deltas,
        harmed_world_count=harmed,
        checkpoints=tuple(_point(deltas[:count]) for count in valid_checkpoints),
    )


def integrated_qualification_diagnostics(
    result: CampaignResult,
    *,
    checkpoints: tuple[int, ...],
) -> QualificationDiagnostics:
    """Build the declared P0-P3 and mechanism-ablation comparison bundle."""

    comparisons = {
        "p1-vs-p0-accessibility": paired_convergence(
            result,
            baseline_arm="p0",
            comparator_arm="p1",
            metric=CampaignMetric.FINAL_ACCESSIBILITY,
            checkpoints=checkpoints,
        ),
        "p2-vs-p0-environment": paired_convergence(
            result,
            baseline_arm="p0",
            comparator_arm="p2",
            metric=CampaignMetric.FINAL_ENVIRONMENT_QUALITY,
            checkpoints=checkpoints,
        ),
        "p3-vs-p0-rent": paired_convergence(
            result,
            baseline_arm="p0",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_RENT,
            checkpoints=checkpoints,
            higher_is_better=False,
        ),
        "inertia-effect": paired_convergence(
            result,
            baseline_arm="p3",
            comparator_arm="p3-no-inertia",
            metric=CampaignMetric.REDEVELOPMENTS,
            checkpoints=checkpoints,
        ),
        "agglomeration-effect": paired_convergence(
            result,
            baseline_arm="p3-no-agglomeration",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_ACCESSIBILITY,
            checkpoints=checkpoints,
        ),
        "transport-attraction-effect": paired_convergence(
            result,
            baseline_arm="p3-no-transport-attraction",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_ACCESSIBILITY,
            checkpoints=checkpoints,
        ),
        "seasonality-effect": paired_convergence(
            result,
            baseline_arm="p3-no-seasonality",
            comparator_arm="p3",
            metric=CampaignMetric.SEASONAL_HEAT_RANGE,
            checkpoints=checkpoints,
        ),
        "environmental-exposure-effect": paired_convergence(
            result,
            baseline_arm="p3-no-environmental-exposure",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_ENVIRONMENT_QUALITY,
            checkpoints=checkpoints,
        ),
        "public-coordination-effect": paired_convergence(
            result,
            baseline_arm="p3-no-public-coordination",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_ACCESSIBILITY,
            checkpoints=checkpoints,
        ),
    }
    arm_ids = {run.arm_id for run in result.runs}
    if "p3-no-service-provision" in arm_ids:
        comparisons["service-provision-effect"] = paired_convergence(
            result,
            baseline_arm="p3-no-service-provision",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_SERVICE_ACCESS,
            checkpoints=checkpoints,
        )
    if "p3-no-cohort-dynamics" in arm_ids:
        comparisons["cohort-dynamics-population-effect"] = paired_convergence(
            result,
            baseline_arm="p3-no-cohort-dynamics",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_POPULATION,
            checkpoints=checkpoints,
        )
        comparisons["cohort-dynamics-employment-effect"] = paired_convergence(
            result,
            baseline_arm="p3-no-cohort-dynamics",
            comparator_arm="p3",
            metric=CampaignMetric.FINAL_EMPLOYMENT,
            checkpoints=checkpoints,
        )
    world_count = len(next(iter(comparisons.values())).world_ids)
    return QualificationDiagnostics(
        campaign_id=result.campaign_id,
        world_count=world_count,
        comparisons=comparisons,
    )
