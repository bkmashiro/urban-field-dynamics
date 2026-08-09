"""Deterministic, mechanism-scoped random event tapes."""

from __future__ import annotations

from hashlib import blake2b
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

NonNegativeInt = Annotated[int, Field(ge=0)]


class EventTapeSpec(BaseModel):
    """Stable identity for one chunk of exogenous random events.

    Policy is deliberately absent: matched policy and ablation runs consume the
    same tape identity.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    root_seed: NonNegativeInt
    world_id: NonNegativeInt
    year: NonNegativeInt
    mechanism: Annotated[str, Field(min_length=1, pattern=r"^[a-z][a-z0-9_-]*$")]


def _philox_seed(spec: EventTapeSpec) -> int:
    identity = (f"{spec.root_seed}\x1f{spec.world_id}\x1f{spec.year}\x1f{spec.mechanism}").encode()
    digest = blake2b(identity, digest_size=16, person=b"urban-field-v1").digest()
    return int.from_bytes(digest, byteorder="little", signed=False)


def generate_event_tape(
    spec: EventTapeSpec,
    *,
    shape: tuple[int, ...],
) -> NDArray[np.float64]:
    """Generate a deterministic ``[0, 1)`` event tape for ``spec`` and ``shape``."""

    if not shape or any(not isinstance(size, int) or size <= 0 for size in shape):
        raise ValueError("shape must be a non-empty tuple of positive integers")

    generator = np.random.Generator(np.random.Philox(_philox_seed(spec)))
    return generator.random(shape, dtype=np.float64)
