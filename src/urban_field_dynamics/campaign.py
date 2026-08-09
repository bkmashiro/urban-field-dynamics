"""Matched-world policy and mechanism campaigns."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.contracts import SpatialUnitSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import (
    PolicySpec,
    WorldResult,
    WorldRunConfig,
    run_world,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")]


class CampaignArm(BaseModel):
    """One policy/mechanism combination evaluated on matched world IDs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    arm_id: Identifier
    policy: PolicySpec
    transition_inertia_enabled: bool = True


class CampaignSpec(BaseModel):
    """Validated experiment matrix for an ensemble campaign."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    campaign_id: Identifier
    root_seed: NonNegativeInt
    world_ids: Annotated[tuple[NonNegativeInt, ...], Field(min_length=1)]
    schedule: ScheduleConfig
    units: Annotated[tuple[SpatialUnitSpec, ...], Field(min_length=1)]
    arms: Annotated[tuple[CampaignArm, ...], Field(min_length=1)]
    development_shock_scale: NonNegativeFloat = 0.0

    @model_validator(mode="after")
    def validate_unique_matrix(self) -> CampaignSpec:
        if len(self.world_ids) != len(set(self.world_ids)):
            raise ValueError("world_ids must be unique")
        arm_ids = [arm.arm_id for arm in self.arms]
        if len(arm_ids) != len(set(arm_ids)):
            raise ValueError("arm_id values must be unique")
        return self


class ArmSummary(BaseModel):
    """Aggregate redevelopment evidence for one campaign arm."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    world_count: int
    worlds_with_redevelopment: int
    total_redevelopments: int
    mean_redevelopments: float


class CampaignSummary(BaseModel):
    """Small aggregate suitable for proposal evidence export."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_count: int
    matched_world_ids: tuple[int, ...]
    arms: dict[str, ArmSummary]


class CampaignRun(BaseModel):
    """One arm/world result with unambiguous experiment identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    arm_id: str
    world: WorldResult


class CampaignResult(BaseModel):
    """Complete small-campaign result before submission compression."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    campaign_id: str
    runs: tuple[CampaignRun, ...]
    summary: CampaignSummary


def run_campaign(spec: CampaignSpec) -> CampaignResult:
    """Run each arm over identical world IDs in deterministic order."""

    runs: list[CampaignRun] = []
    for world_id in spec.world_ids:
        for arm in spec.arms:
            runs.append(
                CampaignRun(
                    arm_id=arm.arm_id,
                    world=run_world(
                        WorldRunConfig(
                            root_seed=spec.root_seed,
                            world_id=world_id,
                            schedule=spec.schedule,
                            units=spec.units,
                            policy=arm.policy,
                            transition_inertia_enabled=arm.transition_inertia_enabled,
                            development_shock_scale=spec.development_shock_scale,
                        )
                    ),
                )
            )

    arm_summaries: dict[str, ArmSummary] = {}
    for arm in spec.arms:
        arm_runs = [run.world for run in runs if run.arm_id == arm.arm_id]
        counts = [run.redevelopment_count for run in arm_runs]
        arm_summaries[arm.arm_id] = ArmSummary(
            world_count=len(arm_runs),
            worlds_with_redevelopment=sum(count > 0 for count in counts),
            total_redevelopments=sum(counts),
            mean_redevelopments=sum(counts) / len(counts),
        )

    return CampaignResult(
        campaign_id=spec.campaign_id,
        runs=tuple(runs),
        summary=CampaignSummary(
            run_count=len(runs),
            matched_world_ids=spec.world_ids,
            arms=arm_summaries,
        ),
    )
