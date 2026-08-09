"""Deterministic annual rent adjustment from housing and employment pressure."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.agents import LocationState

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]


class MarketClearingSpec(BaseModel):
    """Auditable bounded tâtonnement parameters for the reference market."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    target_occupancy: UnitInterval
    adjustment_rate: UnitInterval
    housing_pressure_weight: UnitInterval
    employment_pressure_weight: UnitInterval
    minimum_rent: NonNegativeFloat

    @model_validator(mode="after")
    def validate_pressure_weights(self) -> MarketClearingSpec:
        if abs(self.housing_pressure_weight + self.employment_pressure_weight - 1.0) > 1e-12:
            raise ValueError("pressure weights must sum to one")
        return self


def _occupancy(demand: float, capacity: float) -> float:
    if capacity == 0.0:
        return 0.0 if demand == 0.0 else 1.0
    return demand / capacity


def clear_market(
    locations: tuple[LocationState, ...],
    spec: MarketClearingSpec,
) -> tuple[LocationState, ...]:
    """Adjust shared location rent from current weighted occupancy pressure."""

    cleared: list[LocationState] = []
    for location in sorted(locations, key=lambda item: item.unit_id):
        housing_pressure = _occupancy(location.households, location.housing_capacity)
        employment_pressure = _occupancy(location.jobs, location.employment_capacity)
        pressure = (
            spec.housing_pressure_weight * housing_pressure
            + spec.employment_pressure_weight * employment_pressure
        )
        multiplier = 1.0 + spec.adjustment_rate * (pressure - spec.target_occupancy)
        rent = max(spec.minimum_rent, location.rent * multiplier)
        cleared.append(location.model_copy(update={"rent": rent}))
    return tuple(cleared)
