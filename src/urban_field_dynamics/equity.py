"""Cohort-weighted equity observers for matched campaigns."""

from __future__ import annotations

import statistics
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.campaign import CampaignResult, CampaignSpec
from urban_field_dynamics.world import WorldResult


class EquityGroupSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    group_id: str
    mean_population: float = Field(ge=0.0)
    mean_accessibility: float
    mean_environment_quality: float
    mean_service_access: float
    mean_rent_burden: float = Field(ge=0.0)
    mean_relocation_rate: float = Field(ge=0.0, le=1.0)


class ArmEquitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    arm_id: str
    world_count: int = Field(gt=0)
    groups: dict[str, EquityGroupSummary]
    accessibility_gap: float = Field(ge=0.0)
    environment_quality_gap: float = Field(ge=0.0)
    service_access_gap: float = Field(ge=0.0)
    rent_burden_gap: float = Field(ge=0.0)
    relocation_rate_gap: float = Field(ge=0.0)


class CampaignEquitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    campaign_id: str
    arms: dict[str, ArmEquitySummary]


def _weighted_mean(values: list[tuple[float, float]]) -> float:
    weight = sum(item_weight for _, item_weight in values)
    return sum(value * item_weight for value, item_weight in values) / weight


def _world_groups(spec: CampaignSpec, world: WorldResult) -> dict[str, dict[str, float]]:
    accumulators: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for cohort in spec.households:
        population = world.final_household_populations.get(cohort.cohort_id, cohort.population)
        location_id = world.household_locations[cohort.cohort_id]
        service_quality = world.final_service_quality.get(location_id, 0.5)
        service_capacity = world.final_service_capacity.get(location_id)
        service_access = service_quality
        if service_capacity is not None:
            demand = world.final_households.get(location_id, 0.0)
            service_access *= min(1.0, service_capacity / max(demand, 1.0))
        metrics = {
            "population": population,
            "accessibility": world.final_accessibility.get(location_id, 0.0),
            "environment": world.final_environment_quality.get(location_id, 0.5),
            "service": service_access,
            "rent_burden": (
                world.final_rents.get(location_id, 0.0)
                * cohort.housing_demand_per_person
                / cohort.income
            ),
            "relocation": float(location_id != cohort.initial_unit_id),
        }
        for metric, value in metrics.items():
            accumulators[cohort.equity_group][metric].append((value, population))

    return {
        group_id: {
            metric: (
                sum(value for value, _ in values)
                if metric == "population"
                else _weighted_mean(values)
            )
            for metric, values in metrics.items()
        }
        for group_id, metrics in accumulators.items()
    }


def _gap(groups: dict[str, EquityGroupSummary], attribute: str) -> float:
    values = [float(getattr(group, attribute)) for group in groups.values()]
    return max(values) - min(values) if values else 0.0


def observe_campaign_equity(
    spec: CampaignSpec,
    result: CampaignResult,
) -> CampaignEquitySummary:
    """Observe group outcomes with equal weighting across matched worlds."""

    if spec.campaign_id != result.campaign_id:
        raise ValueError("campaign spec and result IDs must match")
    arm_summaries: dict[str, ArmEquitySummary] = {}
    for arm in spec.arms:
        worlds = sorted(
            (run.world for run in result.runs if run.arm_id == arm.arm_id),
            key=lambda world: world.world_id,
        )
        if not worlds:
            raise ValueError(f"campaign arm has no runs: {arm.arm_id}")
        observed = [_world_groups(spec, world) for world in worlds]
        group_ids = sorted(observed[0])
        if any(sorted(item) != group_ids for item in observed):
            raise ValueError("equity group membership changed across worlds")
        groups = {
            group_id: EquityGroupSummary(
                group_id=group_id,
                mean_population=statistics.fmean(item[group_id]["population"] for item in observed),
                mean_accessibility=statistics.fmean(
                    item[group_id]["accessibility"] for item in observed
                ),
                mean_environment_quality=statistics.fmean(
                    item[group_id]["environment"] for item in observed
                ),
                mean_service_access=statistics.fmean(
                    item[group_id]["service"] for item in observed
                ),
                mean_rent_burden=statistics.fmean(
                    item[group_id]["rent_burden"] for item in observed
                ),
                mean_relocation_rate=statistics.fmean(
                    item[group_id]["relocation"] for item in observed
                ),
            )
            for group_id in group_ids
        }
        arm_summaries[arm.arm_id] = ArmEquitySummary(
            arm_id=arm.arm_id,
            world_count=len(worlds),
            groups=groups,
            accessibility_gap=_gap(groups, "mean_accessibility"),
            environment_quality_gap=_gap(groups, "mean_environment_quality"),
            service_access_gap=_gap(groups, "mean_service_access"),
            rent_burden_gap=_gap(groups, "mean_rent_burden"),
            relocation_rate_gap=_gap(groups, "mean_relocation_rate"),
        )
    return CampaignEquitySummary(campaign_id=result.campaign_id, arms=arm_summaries)
