"""Matched-world policy and mechanism campaigns."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec, LocationState
from urban_field_dynamics.contracts import SpatialUnitSpec
from urban_field_dynamics.environment import (
    EnvironmentalUnitSpec,
    ExposureWeights,
    SeasonalEnvironmentSpec,
)
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentSpec,
    TransportEdgeSpec,
)
from urban_field_dynamics.world import (
    MechanismSwitches,
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
    mechanisms: MechanismSwitches = MechanismSwitches()


class CampaignSpec(BaseModel):
    """Validated experiment matrix for an ensemble campaign."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    campaign_id: Identifier
    model_scope: str = "redevelopment-only qualification slice"
    root_seed: NonNegativeInt
    world_ids: Annotated[tuple[NonNegativeInt, ...], Field(min_length=1)]
    schedule: ScheduleConfig
    units: Annotated[tuple[SpatialUnitSpec, ...], Field(min_length=1)]
    arms: Annotated[tuple[CampaignArm, ...], Field(min_length=1)]
    development_shock_scale: NonNegativeFloat = 0.0
    locations: tuple[LocationState, ...] = ()
    location_members: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    households: tuple[HouseholdCohortSpec, ...] = ()
    firms: tuple[FirmCohortSpec, ...] = ()
    market: MarketClearingSpec | None = None
    agent_taste_shock_scale: NonNegativeFloat = 0.0
    transport_edges: tuple[TransportEdgeSpec, ...] = ()
    transport_od: tuple[ODPair, ...] = ()
    transport_assignment: TransportAssignmentSpec | None = None
    accessibility_decay: NonNegativeFloat = 0.0
    environmental_units: tuple[EnvironmentalUnitSpec, ...] = ()
    seasonal_environment: tuple[SeasonalEnvironmentSpec, ...] = ()
    exposure_weights: ExposureWeights | None = None

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
    mean_final_accessibility: float = 0.0
    mean_final_environment_quality: float = 0.0
    mean_final_rent: float = 0.0
    mean_household_relocations: float = 0.0
    mean_firm_relocations: float = 0.0
    mean_seasonal_heat_range: float = 0.0


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
                            mechanisms=arm.mechanisms,
                            locations=spec.locations,
                            location_members=spec.location_members,
                            households=spec.households,
                            firms=spec.firms,
                            market=spec.market,
                            agent_taste_shock_scale=spec.agent_taste_shock_scale,
                            transport_edges=spec.transport_edges,
                            transport_od=spec.transport_od,
                            transport_assignment=spec.transport_assignment,
                            accessibility_decay=spec.accessibility_decay,
                            environmental_units=spec.environmental_units,
                            seasonal_environment=spec.seasonal_environment,
                            exposure_weights=spec.exposure_weights,
                        )
                    ),
                )
            )

    arm_summaries: dict[str, ArmSummary] = {}
    for arm in spec.arms:
        arm_runs = [run.world for run in runs if run.arm_id == arm.arm_id]
        counts = [run.redevelopment_count for run in arm_runs]
        accessibility_means = [
            sum(run.final_accessibility.values()) / len(run.final_accessibility) for run in arm_runs
        ]
        environment_means = [
            sum(run.final_environment_quality.values()) / len(run.final_environment_quality)
            for run in arm_runs
            if run.final_environment_quality
        ]
        rent_means = [
            sum(run.final_rents.values()) / len(run.final_rents)
            for run in arm_runs
            if run.final_rents
        ]
        household_relocations = [
            sum(
                run.household_locations.get(cohort.cohort_id) != cohort.initial_unit_id
                for cohort in spec.households
            )
            for run in arm_runs
        ]
        firm_relocations = [
            sum(
                run.firm_locations.get(cohort.cohort_id) != cohort.initial_unit_id
                for cohort in spec.firms
            )
            for run in arm_runs
        ]
        seasonal_heat_ranges: list[float] = []
        for run in arm_runs:
            ranges: list[float] = []
            for seasonal_results in run.environment_traces.values():
                unit_ids = {
                    unit_id
                    for unit_results in seasonal_results.values()
                    for unit_id in unit_results
                }
                for unit_id in unit_ids:
                    values = [
                        unit_results[unit_id].heat for unit_results in seasonal_results.values()
                    ]
                    ranges.append(max(values) - min(values))
            seasonal_heat_ranges.append(sum(ranges) / len(ranges) if ranges else 0.0)
        arm_summaries[arm.arm_id] = ArmSummary(
            world_count=len(arm_runs),
            worlds_with_redevelopment=sum(count > 0 for count in counts),
            total_redevelopments=sum(counts),
            mean_redevelopments=sum(counts) / len(counts),
            mean_final_accessibility=sum(accessibility_means) / len(accessibility_means),
            mean_final_environment_quality=(
                sum(environment_means) / len(environment_means) if environment_means else 0.0
            ),
            mean_final_rent=sum(rent_means) / len(rent_means) if rent_means else 0.0,
            mean_household_relocations=(sum(household_relocations) / len(household_relocations)),
            mean_firm_relocations=sum(firm_relocations) / len(firm_relocations),
            mean_seasonal_heat_range=(sum(seasonal_heat_ranges) / len(seasonal_heat_ranges)),
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
