"""Matched policy-intensity sweeps without hidden stochastic changes."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.campaign import (
    CampaignArm,
    CampaignResult,
    CampaignSpec,
)
from urban_field_dynamics.world import PolicySpec

UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")]


class SweepMetric(StrEnum):
    REDEVELOPMENTS = "redevelopments"
    FINAL_ACCESSIBILITY = "final_accessibility"
    FINAL_ENVIRONMENT_QUALITY = "final_environment_quality"
    FINAL_RENT = "final_rent"


class PolicySweepSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    sweep_id: Identifier
    source_arm_id: Identifier
    intensities: Annotated[tuple[UnitInterval, ...], Field(min_length=2)]

    @model_validator(mode="after")
    def validate_intensities(self) -> PolicySweepSpec:
        if len(set(self.intensities)) != len(self.intensities):
            raise ValueError("sweep intensities must be unique")
        if tuple(sorted(self.intensities)) != self.intensities:
            raise ValueError("sweep intensities must be increasing")
        return self


class BuiltPolicySweep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sweep_id: str
    campaign: CampaignSpec
    intensity_by_arm: dict[str, float]


class SweepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    sweep_id: str
    metric: SweepMetric
    levels: tuple[float, ...]
    responses: tuple[float, ...]


def _scale_deltas(values: dict[str, float], intensity: float) -> dict[str, float]:
    return {key: value * intensity for key, value in values.items()}


def _scale_multipliers(values: dict[str, float], intensity: float) -> dict[str, float]:
    return {key: 1.0 + intensity * (value - 1.0) for key, value in values.items()}


def scale_policy(
    target: PolicySpec,
    *,
    intensity: UnitInterval,
    policy_id: str,
) -> PolicySpec:
    """Interpolate an intervention from neutral conditions to its target values."""

    values = target.model_dump()
    values.update(
        policy_id=policy_id,
        accessibility_delta=target.accessibility_delta * intensity,
        accessibility_delta_by_unit=_scale_deltas(target.accessibility_delta_by_unit, intensity),
        transport_capacity_multiplier_by_edge=_scale_multipliers(
            target.transport_capacity_multiplier_by_edge, intensity
        ),
        transport_time_multiplier_by_edge=_scale_multipliers(
            target.transport_time_multiplier_by_edge, intensity
        ),
        green_fraction_delta_by_unit=_scale_deltas(target.green_fraction_delta_by_unit, intensity),
        service_quality_delta_by_location=_scale_deltas(
            target.service_quality_delta_by_location, intensity
        ),
        service_capacity_multiplier_by_location=_scale_multipliers(
            target.service_capacity_multiplier_by_location, intensity
        ),
    )
    return PolicySpec.model_validate(values)


def build_policy_intensity_sweep(
    base: CampaignSpec,
    sweep: PolicySweepSpec,
) -> BuiltPolicySweep:
    source = next((arm for arm in base.arms if arm.arm_id == sweep.source_arm_id), None)
    if source is None:
        raise ValueError(f"source arm not found: {sweep.source_arm_id}")
    arms: list[CampaignArm] = []
    intensity_by_arm: dict[str, float] = {}
    for index, intensity in enumerate(sweep.intensities):
        arm_id = f"sweep-{index:02d}"
        intensity_by_arm[arm_id] = intensity
        arms.append(
            CampaignArm(
                arm_id=arm_id,
                policy=scale_policy(
                    source.policy,
                    intensity=intensity,
                    policy_id=arm_id,
                ),
                transition_inertia_enabled=source.transition_inertia_enabled,
                mechanisms=source.mechanisms,
            )
        )
    campaign = CampaignSpec.model_validate(
        {
            **base.model_dump(exclude={"campaign_id", "arms"}),
            "campaign_id": sweep.sweep_id,
            "arms": [arm.model_dump() for arm in arms],
        }
    )
    return BuiltPolicySweep(
        sweep_id=sweep.sweep_id,
        campaign=campaign,
        intensity_by_arm=intensity_by_arm,
    )


def summarize_sweep(
    sweep: BuiltPolicySweep,
    result: CampaignResult,
    *,
    metric: SweepMetric | str,
) -> SweepResponse:
    if result.campaign_id != sweep.campaign.campaign_id:
        raise ValueError("sweep campaign and result IDs must match")
    selected = SweepMetric(metric)
    attribute = {
        SweepMetric.REDEVELOPMENTS: "mean_redevelopments",
        SweepMetric.FINAL_ACCESSIBILITY: "mean_final_accessibility",
        SweepMetric.FINAL_ENVIRONMENT_QUALITY: "mean_final_environment_quality",
        SweepMetric.FINAL_RENT: "mean_final_rent",
    }[selected]
    ordered = sorted(sweep.intensity_by_arm.items(), key=lambda item: item[1])
    return SweepResponse(
        sweep_id=sweep.sweep_id,
        metric=selected,
        levels=tuple(level for _, level in ordered),
        responses=tuple(
            float(getattr(result.summary.arms[arm_id], attribute)) for arm_id, _ in ordered
        ),
    )
