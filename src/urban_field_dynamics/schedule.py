"""Explicit multi-timescale process scheduling.

The schedule is deliberately separate from state-transition implementations so process
ordering can be inspected and tested before individual submodels are coupled.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

Year = Annotated[int, Field(ge=0)]


class Season(StrEnum):
    """Canonical seasonal order for representative operational periods."""

    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class AnnualPhase(StrEnum):
    """Process phases in one simulation year."""

    PUBLIC_POLICY = "public_policy"
    SEASONAL_OPERATIONS = "seasonal_operations"
    HOUSEHOLD_RELOCATION = "household_relocation"
    FIRM_DYNAMICS = "firm_dynamics"
    MARKET_CLEARING = "market_clearing"
    DEVELOPMENT = "development"
    INFRASTRUCTURE_AGING = "infrastructure_aging"
    OBSERVATION = "observation"


class ScheduleConfig(BaseModel):
    """Validated inclusive simulation horizon and rolling-planning years."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start_year: Year
    end_year: Year
    replan_years: frozenset[Year] = frozenset()

    @model_validator(mode="after")
    def validate_horizon(self) -> ScheduleConfig:
        if self.end_year < self.start_year:
            raise ValueError("end_year must be greater than or equal to start_year")
        outside = sorted(
            year for year in self.replan_years if year < self.start_year or year > self.end_year
        )
        if outside:
            raise ValueError(f"replan_years outside simulation horizon: {outside}")
        return self


@dataclass(frozen=True, slots=True)
class ScheduleStep:
    """One inspectable point in the simulation process order."""

    year: int
    phase: AnnualPhase
    season: Season | None = None


_ANNUAL_PRIVATE_AND_OBSERVATION_PHASES = (
    AnnualPhase.HOUSEHOLD_RELOCATION,
    AnnualPhase.FIRM_DYNAMICS,
    AnnualPhase.MARKET_CLEARING,
    AnnualPhase.DEVELOPMENT,
    AnnualPhase.INFRASTRUCTURE_AGING,
    AnnualPhase.OBSERVATION,
)


def iter_schedule(config: ScheduleConfig) -> Iterator[ScheduleStep]:
    """Yield deterministic policy, seasonal, annual, and observation phases."""

    for year in range(config.start_year, config.end_year + 1):
        if year in config.replan_years:
            yield ScheduleStep(year=year, phase=AnnualPhase.PUBLIC_POLICY)

        for season in Season:
            yield ScheduleStep(
                year=year,
                phase=AnnualPhase.SEASONAL_OPERATIONS,
                season=season,
            )

        for phase in _ANNUAL_PRIVATE_AND_OBSERVATION_PHASES:
            yield ScheduleStep(year=year, phase=phase)
