"""Relative seasonal environmental exposure surrogate."""

from __future__ import annotations

import math
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.schedule import Season

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")]


class EnvironmentalUnitSpec(BaseModel):
    """Stylised local drivers; values must retain their evidence authority."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    unit_id: Identifier
    green_fraction: UnitInterval
    traffic_exposure_factor: NonNegativeFloat
    activity_intensity: UnitInterval
    night_light_intensity: UnitInterval
    transport_edge_ids: tuple[Identifier, ...] = ()
    evidence_status: EvidenceStatus


class SeasonalEnvironmentSpec(BaseModel):
    """Representative seasonal background and response parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    season: Season
    air_background: UnitInterval
    noise_background_db: NonNegativeFloat
    heat_stress: UnitInterval
    night_length_factor: UnitInterval
    green_cooling_strength: UnitInterval
    activity_heat_factor: UnitInterval


class ExposureWeights(BaseModel):
    """Declared aggregation weights for the location-quality proxy."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    air: UnitInterval
    noise: UnitInterval
    light: UnitInterval
    heat: UnitInterval

    @model_validator(mode="after")
    def validate_sum(self) -> ExposureWeights:
        if not math.isclose(self.air + self.noise + self.light + self.heat, 1.0, abs_tol=1e-9):
            raise ValueError("exposure weights must sum to one")
        return self


class ExposureResult(BaseModel):
    """Relative exposure potential, not calibrated physical concentration."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    air: UnitInterval
    noise_db: NonNegativeFloat
    light: UnitInterval
    heat: UnitInterval
    environment_quality: UnitInterval


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def evaluate_exposure(
    unit: EnvironmentalUnitSpec,
    season: SeasonalEnvironmentSpec,
    *,
    traffic_pressure: float,
    weights: ExposureWeights,
) -> ExposureResult:
    """Evaluate one unit/season from relative traffic, activity, light, and green drivers."""

    if traffic_pressure < 0.0:
        raise ValueError("traffic_pressure must be non-negative")
    traffic_effect = traffic_pressure * unit.traffic_exposure_factor
    air = _clamp(season.air_background + traffic_effect)
    noise_db = season.noise_background_db + 10.0 * math.log10(1.0 + traffic_effect)
    light = _clamp(unit.night_light_intensity * season.night_length_factor)
    heat = _clamp(
        season.heat_stress * (1.0 - unit.green_fraction * season.green_cooling_strength)
        + unit.activity_intensity * season.activity_heat_factor
    )
    normalized_noise = _clamp(noise_db / 100.0)
    burden = (
        weights.air * air
        + weights.noise * normalized_noise
        + weights.light * light
        + weights.heat * heat
    )
    return ExposureResult(
        air=air,
        noise_db=noise_db,
        light=light,
        heat=heat,
        environment_quality=_clamp(1.0 - burden),
    )
