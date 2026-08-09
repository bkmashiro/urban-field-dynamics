"""Minimal auditable world runner for the first vertical slice."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.contracts import LandUse, SpatialUnitSpec
from urban_field_dynamics.event_tape import EventTapeSpec, generate_event_tape
from urban_field_dynamics.redevelopment import evaluate_redevelopment
from urban_field_dynamics.schedule import AnnualPhase, ScheduleConfig, iter_schedule

NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
AccessibilityDelta = Annotated[float, Field(ge=-1.0, le=1.0)]


class PolicySpec(BaseModel):
    """One public intervention applied at an explicit replanning year."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    policy_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")]
    intervention_year: NonNegativeInt
    accessibility_delta: AccessibilityDelta = 0.0


class WorldRunConfig(BaseModel):
    """Complete input identity for a small deterministic world run."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    root_seed: NonNegativeInt
    world_id: NonNegativeInt
    schedule: ScheduleConfig
    units: Annotated[tuple[SpatialUnitSpec, ...], Field(min_length=1)]
    policy: PolicySpec
    transition_inertia_enabled: bool = True
    development_shock_scale: NonNegativeFloat = 0.0

    @model_validator(mode="after")
    def validate_policy_and_units(self) -> WorldRunConfig:
        if self.policy.intervention_year not in self.schedule.replan_years:
            raise ValueError("policy intervention_year must be a declared replan_year")
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("unit_id values must be unique")
        return self


class WorldResult(BaseModel):
    """Small, JSON-safe trace and terminal state for one world-policy run."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    root_seed: int
    world_id: int
    policy_id: str
    transition_inertia_enabled: bool
    redevelopment_years: dict[str, int | None]
    final_accessibility: dict[str, float]
    final_uses: dict[str, LandUse]
    development_shocks: dict[int, dict[str, float]]

    @property
    def redevelopment_count(self) -> int:
        return sum(year is not None for year in self.redevelopment_years.values())


def run_world(config: WorldRunConfig) -> WorldResult:
    """Run the qualified redevelopment-only vertical slice."""

    unit_ids = tuple(unit.unit_id for unit in config.units)
    initial_by_id = {unit.unit_id: unit for unit in config.units}
    accessibility = {unit.unit_id: unit.accessibility for unit in config.units}
    asset_age = {unit.unit_id: unit.asset_age_years for unit in config.units}
    current_use = {unit.unit_id: unit.current_use for unit in config.units}
    redevelopment_years: dict[str, int | None] = {unit.unit_id: None for unit in config.units}
    development_shocks: dict[int, dict[str, float]] = {}

    for step in iter_schedule(config.schedule):
        if step.phase is AnnualPhase.PUBLIC_POLICY:
            if step.year == config.policy.intervention_year:
                for unit_id in unit_ids:
                    accessibility[unit_id] = min(
                        1.0,
                        max(
                            0.0,
                            accessibility[unit_id] + config.policy.accessibility_delta,
                        ),
                    )

        elif step.phase is AnnualPhase.DEVELOPMENT:
            tape = generate_event_tape(
                EventTapeSpec(
                    root_seed=config.root_seed,
                    world_id=config.world_id,
                    year=step.year,
                    mechanism="development-shock",
                ),
                shape=(len(unit_ids),),
            )
            year_shocks = {
                unit_id: float((tape[index] - 0.5) * 2.0 * config.development_shock_scale)
                for index, unit_id in enumerate(unit_ids)
            }
            development_shocks[step.year] = year_shocks

            for unit_id in unit_ids:
                if redevelopment_years[unit_id] is not None:
                    continue
                initial = initial_by_id[unit_id]
                current = initial.model_copy(
                    update={
                        "asset_age_years": asset_age[unit_id],
                        "accessibility": accessibility[unit_id],
                        "current_use": current_use[unit_id],
                    }
                )
                decision = evaluate_redevelopment(
                    current,
                    candidate_shock=year_shocks[unit_id],
                    transition_inertia_enabled=config.transition_inertia_enabled,
                )
                if decision.should_redevelop:
                    redevelopment_years[unit_id] = step.year
                    current_use[unit_id] = initial.candidate_use
                    asset_age[unit_id] = 0

        elif step.phase is AnnualPhase.INFRASTRUCTURE_AGING:
            for unit_id in unit_ids:
                if redevelopment_years[unit_id] != step.year:
                    asset_age[unit_id] += 1

    return WorldResult(
        root_seed=config.root_seed,
        world_id=config.world_id,
        policy_id=config.policy.policy_id,
        transition_inertia_enabled=config.transition_inertia_enabled,
        redevelopment_years=redevelopment_years,
        final_accessibility=accessibility,
        final_uses=current_use,
        development_shocks=development_shocks,
    )
