"""Strict model contracts shared by simulation submodels."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]


class EvidenceStatus(StrEnum):
    """Authority and interpretation status of an input or output."""

    OFFICIAL = "official"
    PUBLIC_OBSERVED = "public_observed"
    PROVISIONAL = "provisional"
    SYNTHETIC = "synthetic"
    DESIGN_TARGET = "design_target"
    UNKNOWN = "unknown"


class LandUse(StrEnum):
    """Small MVP land-use vocabulary; adapters may map richer classifications."""

    RESIDENTIAL = "residential"
    RESEARCH = "research"
    COMMERCIAL = "commercial"
    GREEN = "green"
    PUBLIC_SERVICE = "public_service"
    MIXED = "mixed"


class PinKind(StrEnum):
    """Legal/physical pinning and transition-inertia classes."""

    HARD = "hard"
    SOFT = "soft"
    FREE = "free"


class SpatialUnitSpec(BaseModel):
    """Validated initial state and redevelopment candidate for one spatial unit."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    unit_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")]
    area_sqm: PositiveFloat
    current_use: LandUse
    candidate_use: LandUse
    pin_kind: PinKind
    asset_age_years: NonNegativeInt
    design_life_years: PositiveInt
    keep_npv: NonNegativeFloat
    candidate_base_npv: NonNegativeFloat
    transition_cost: NonNegativeFloat
    accessibility: UnitInterval
    accessibility_value_factor: NonNegativeFloat
    evidence_status: EvidenceStatus
