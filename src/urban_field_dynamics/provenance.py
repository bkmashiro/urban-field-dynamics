"""Frozen source/runtime provenance for replayable evidence."""

from importlib.metadata import version
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.contracts import EvidenceStatus


class ArtifactProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_repository: str = "https://github.com/bkmashiro/urban-field-dynamics"
    source_revision: str = Field(pattern=r"^(?:[0-9a-f]{7,64}|unspecified)$")
    python_runtime_authority: Literal["3.12"] = "3.12"
    package_name: Literal["urban-field-dynamics"] = "urban-field-dynamics"
    package_version: str
    evidence_status: Literal[EvidenceStatus.SYNTHETIC] = EvidenceStatus.SYNTHETIC


def artifact_provenance(source_revision: str = "unspecified") -> ArtifactProvenance:
    return ArtifactProvenance(
        source_revision=source_revision,
        package_version=version("urban-field-dynamics"),
    )
