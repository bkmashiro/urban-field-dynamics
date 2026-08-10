import pytest
from pydantic import ValidationError

from urban_field_dynamics.schedule import (
    AnnualPhase,
    ScheduleConfig,
    Season,
    iter_schedule,
)


def test_schedule_has_explicit_replanning_seasons_and_annual_order() -> None:
    config = ScheduleConfig(start_year=2026, end_year=2027, replan_years={2026})

    steps = list(iter_schedule(config))

    assert [(step.year, step.phase, step.season) for step in steps] == [
        (2026, AnnualPhase.PUBLIC_POLICY, None),
        (2026, AnnualPhase.SEASONAL_OPERATIONS, Season.SPRING),
        (2026, AnnualPhase.SEASONAL_OPERATIONS, Season.SUMMER),
        (2026, AnnualPhase.SEASONAL_OPERATIONS, Season.AUTUMN),
        (2026, AnnualPhase.SEASONAL_OPERATIONS, Season.WINTER),
        (2026, AnnualPhase.HOUSEHOLD_RELOCATION, None),
        (2026, AnnualPhase.FIRM_DYNAMICS, None),
        (2026, AnnualPhase.LABOR_MATCHING, None),
        (2026, AnnualPhase.MARKET_CLEARING, None),
        (2026, AnnualPhase.DEVELOPMENT, None),
        (2026, AnnualPhase.INFRASTRUCTURE_AGING, None),
        (2026, AnnualPhase.OBSERVATION, None),
        (2027, AnnualPhase.SEASONAL_OPERATIONS, Season.SPRING),
        (2027, AnnualPhase.SEASONAL_OPERATIONS, Season.SUMMER),
        (2027, AnnualPhase.SEASONAL_OPERATIONS, Season.AUTUMN),
        (2027, AnnualPhase.SEASONAL_OPERATIONS, Season.WINTER),
        (2027, AnnualPhase.HOUSEHOLD_RELOCATION, None),
        (2027, AnnualPhase.FIRM_DYNAMICS, None),
        (2027, AnnualPhase.LABOR_MATCHING, None),
        (2027, AnnualPhase.MARKET_CLEARING, None),
        (2027, AnnualPhase.DEVELOPMENT, None),
        (2027, AnnualPhase.INFRASTRUCTURE_AGING, None),
        (2027, AnnualPhase.OBSERVATION, None),
    ]


def test_schedule_is_reiterable_and_deterministic() -> None:
    config = ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026})

    assert list(iter_schedule(config)) == list(iter_schedule(config))


def test_schedule_rejects_replanning_outside_horizon() -> None:
    with pytest.raises(ValidationError):
        ScheduleConfig(start_year=2026, end_year=2030, replan_years={2035})


def test_schedule_rejects_reversed_horizon() -> None:
    with pytest.raises(ValidationError):
        ScheduleConfig(start_year=2030, end_year=2026)


def test_schedule_contract_is_strict() -> None:
    with pytest.raises(ValidationError):
        ScheduleConfig.model_validate({"start_year": 2026, "end_year": 2030, "unknown": True})
