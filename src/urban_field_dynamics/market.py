"""Deterministic annual rent adjustment from housing and employment pressure."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.agents import LocationState

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
PositiveInt = Annotated[int, Field(gt=0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]


class MarketClearingError(RuntimeError):
    """Raised when a required bounded market solve does not converge."""


class MarketClearingSpec(BaseModel):
    """Auditable bounded tâtonnement parameters for the reference market."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    target_occupancy: UnitInterval
    adjustment_rate: UnitInterval
    housing_pressure_weight: UnitInterval
    employment_pressure_weight: UnitInterval
    minimum_rent: NonNegativeFloat
    maximum_rent: PositiveFloat = 1_000_000.0
    solver_relaxation: UnitInterval = 0.5
    maximum_annual_rent_change: UnitInterval = 1.0
    max_iterations: PositiveInt = 64
    convergence_tolerance: PositiveFloat = 1e-5
    require_convergence: bool = False

    @model_validator(mode="after")
    def validate_pressure_weights(self) -> MarketClearingSpec:
        if abs(self.housing_pressure_weight + self.employment_pressure_weight - 1.0) > 1e-12:
            raise ValueError("pressure weights must sum to one")
        if self.maximum_rent <= self.minimum_rent:
            raise ValueError("maximum_rent must exceed minimum_rent")
        if self.solver_relaxation == 0.0:
            raise ValueError("solver_relaxation must be positive")
        return self


class MarketClearingResult(BaseModel):
    """Bounded fixed-point result and convergence evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    locations: tuple[LocationState, ...]
    iterations: Annotated[int, Field(ge=0)]
    converged: bool
    max_residual: NonNegativeFloat
    residual_history: tuple[NonNegativeFloat, ...]
    minimum_rent_locations: tuple[str, ...]
    maximum_rent_locations: tuple[str, ...]


def _occupancy(demand: float, capacity: float) -> float:
    if capacity == 0.0:
        return 0.0 if demand == 0.0 else 1.0
    return demand / capacity


def _target_rent(location: LocationState, spec: MarketClearingSpec) -> float:
    """Return one bounded annual rent target from observed occupancy pressure."""

    housing = _occupancy(location.households, location.housing_capacity)
    employment = _occupancy(location.jobs, location.employment_capacity)
    pressure = spec.housing_pressure_weight * housing + spec.employment_pressure_weight * employment
    raw_multiplier = 1.0 + spec.adjustment_rate * (pressure - spec.target_occupancy)
    lower = 1.0 - spec.maximum_annual_rent_change
    upper = 1.0 + spec.maximum_annual_rent_change
    multiplier = max(lower, min(upper, raw_multiplier))
    return max(
        spec.minimum_rent,
        min(spec.maximum_rent, location.rent * multiplier),
    )


def clear_market(
    locations: tuple[LocationState, ...],
    spec: MarketClearingSpec,
) -> MarketClearingResult:
    """Converge to one bounded annual pressure-response target."""

    ordered = tuple(sorted(locations, key=lambda item: item.unit_id))
    references = {
        location.unit_id: max(location.rent, spec.minimum_rent, 1e-9) for location in ordered
    }
    targets = {location.unit_id: _target_rent(location, spec) for location in ordered}
    rents = {
        location.unit_id: max(
            spec.minimum_rent,
            min(spec.maximum_rent, location.rent),
        )
        for location in ordered
    }
    residual_history: list[float] = []
    converged = not ordered
    iterations = 0

    for iteration in range(1, spec.max_iterations + 1):
        residuals = {
            location.unit_id: abs(targets[location.unit_id] - rents[location.unit_id])
            / references[location.unit_id]
            for location in ordered
        }
        max_residual = max(residuals.values(), default=0.0)
        residual_history.append(max_residual)
        iterations = iteration
        if max_residual <= spec.convergence_tolerance:
            converged = True
            rents.update(targets)
            break
        for location in ordered:
            unit_id = location.unit_id
            rents[unit_id] += spec.solver_relaxation * (targets[unit_id] - rents[unit_id])

    final_residuals = [
        abs(targets[location.unit_id] - rents[location.unit_id]) / references[location.unit_id]
        for location in ordered
    ]
    max_residual = max(final_residuals, default=0.0)
    if max_residual <= spec.convergence_tolerance:
        converged = True
    if spec.require_convergence and not converged:
        raise MarketClearingError(
            f"market did not converge after {iterations} iterations; residual={max_residual:.12g}"
        )

    cleared = tuple(
        location.model_copy(update={"rent": rents[location.unit_id]}) for location in ordered
    )
    tolerance = 1e-12
    return MarketClearingResult(
        locations=cleared,
        iterations=iterations,
        converged=converged,
        max_residual=max_residual,
        residual_history=tuple(residual_history),
        minimum_rent_locations=tuple(
            location.unit_id
            for location in ordered
            if rents[location.unit_id] <= spec.minimum_rent + tolerance
        ),
        maximum_rent_locations=tuple(
            location.unit_id
            for location in ordered
            if rents[location.unit_id] >= spec.maximum_rent - tolerance
        ),
    )
