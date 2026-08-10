"""Deterministic stylised spatial grid and observer labels."""

from __future__ import annotations

import math
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.contracts import (
    EvidenceStatus,
    LandUse,
    PinKind,
    SpatialUnitSpec,
)
from urban_field_dynamics.event_tape import EventTapeSpec, generate_event_tape

PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")]


class FocusZoneSpec(BaseModel):
    """Observer-only circular label in grid coordinates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    zone_id: Identifier
    center_row: NonNegativeInt
    center_column: NonNegativeInt
    radius_cells: PositiveInt


class StylizedGridSpec(BaseModel):
    """Policy-independent synthetic grid bootstrap identity."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    root_seed: NonNegativeInt
    rows: Annotated[int, Field(ge=2)]
    columns: Annotated[int, Field(ge=2)]
    cell_size_m: PositiveFloat
    corridor_center_column: NonNegativeInt
    corridor_half_width_cells: NonNegativeInt
    focus_zones: tuple[FocusZoneSpec, ...] = ()

    @model_validator(mode="after")
    def validate_observer_geometry(self) -> StylizedGridSpec:
        if self.corridor_center_column >= self.columns:
            raise ValueError("corridor center column must be inside grid")
        zone_ids = [zone.zone_id for zone in self.focus_zones]
        if len(zone_ids) != len(set(zone_ids)):
            raise ValueError("focus zone IDs must be unique")
        if any(
            zone.center_row >= self.rows or zone.center_column >= self.columns
            for zone in self.focus_zones
        ):
            raise ValueError("focus zone centers must be inside grid")
        return self


class StylizedSpatialUnit(BaseModel):
    """One strict simulation unit plus non-causal observer metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    spec: SpatialUnitSpec
    row: NonNegativeInt
    column: NonNegativeInt
    centroid_x_m: NonNegativeInt | float
    centroid_y_m: NonNegativeInt | float
    neighbor_ids: tuple[str, ...]
    focus_zone_id: str | None = None
    is_corridor_observer: bool


class StylizedGrid(BaseModel):
    """Complete deterministic grid in stable row-major order."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    spec: StylizedGridSpec
    units: tuple[StylizedSpatialUnit, ...]


def _unit_id(row: int, column: int) -> str:
    return f"cell-r{row:02d}-c{column:02d}"


def _neighbors(row: int, column: int, rows: int, columns: int) -> tuple[str, ...]:
    candidates = (
        (row - 1, column),
        (row + 1, column),
        (row, column - 1),
        (row, column + 1),
    )
    return tuple(
        sorted(
            _unit_id(candidate_row, candidate_column)
            for candidate_row, candidate_column in candidates
            if 0 <= candidate_row < rows and 0 <= candidate_column < columns
        )
    )


def _focus_label(row: int, column: int, zones: tuple[FocusZoneSpec, ...]) -> str | None:
    eligible = [
        (
            math.hypot(row - zone.center_row, column - zone.center_column),
            zone.zone_id,
        )
        for zone in zones
        if math.hypot(row - zone.center_row, column - zone.center_column) <= zone.radius_cells
    ]
    return min(eligible)[1] if eligible else None


def generate_stylized_grid(spec: StylizedGridSpec) -> StylizedGrid:
    """Generate synthetic initial states without using observer labels as causes."""

    count = spec.rows * spec.columns
    tape = generate_event_tape(
        EventTapeSpec(
            root_seed=spec.root_seed,
            world_id=0,
            year=0,
            mechanism="spatial-bootstrap",
        ),
        shape=(count, 9),
    )
    land_uses = tuple(LandUse)
    units: list[StylizedSpatialUnit] = []
    for row in range(spec.rows):
        for column in range(spec.columns):
            index = row * spec.columns + column
            values = tape[index]
            current_index = min(int(values[0] * len(land_uses)), len(land_uses) - 1)
            candidate_offset = 1 + min(
                int(values[1] * (len(land_uses) - 1)),
                len(land_uses) - 2,
            )
            pin_value = values[8]
            pin_kind = (
                PinKind.HARD
                if pin_value < 0.03
                else PinKind.SOFT
                if pin_value < 0.38
                else PinKind.FREE
            )
            unit = SpatialUnitSpec(
                unit_id=_unit_id(row, column),
                area_sqm=spec.cell_size_m**2,
                current_use=land_uses[current_index],
                candidate_use=land_uses[(current_index + candidate_offset) % len(land_uses)],
                pin_kind=pin_kind,
                asset_age_years=int(values[2] * 61),
                design_life_years=40 + int(values[3] * 31),
                keep_npv=80.0 + 40.0 * float(values[4]),
                candidate_base_npv=75.0 + 50.0 * float(values[5]),
                transition_cost=10.0 + 50.0 * float(values[6]),
                accessibility=float(values[7]),
                accessibility_value_factor=35.0,
                evidence_status=EvidenceStatus.SYNTHETIC,
            )
            units.append(
                StylizedSpatialUnit(
                    spec=unit,
                    row=row,
                    column=column,
                    centroid_x_m=(column + 0.5) * spec.cell_size_m,
                    centroid_y_m=(row + 0.5) * spec.cell_size_m,
                    neighbor_ids=_neighbors(row, column, spec.rows, spec.columns),
                    focus_zone_id=_focus_label(row, column, spec.focus_zones),
                    is_corridor_observer=(
                        abs(column - spec.corridor_center_column) <= spec.corridor_half_width_cells
                    ),
                )
            )
    return StylizedGrid(spec=spec, units=tuple(units))
