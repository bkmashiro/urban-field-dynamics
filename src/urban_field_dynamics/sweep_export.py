"""Bounded, deterministic, replay-verifiable policy-sweep evidence."""

from __future__ import annotations

import json
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.campaign import CampaignResult, run_campaign, run_campaign_parallel
from urban_field_dynamics.decision import ThresholdCrossingResult, detect_threshold_crossings
from urban_field_dynamics.provenance import ArtifactProvenance, artifact_provenance
from urban_field_dynamics.sweep import (
    BuiltPolicySweep,
    SweepMetric,
    SweepResponse,
    assert_matched_sweep_random_identity,
    summarize_sweep,
)

_ARTIFACT_NAMES = ("sweep-config.json", "provenance.json", "sweep-evidence.json")


class SweepExportVerificationError(RuntimeError):
    """Raised when sweep evidence fails integrity or replay verification."""


class SweepThresholdSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    metric: SweepMetric
    threshold: float
    threshold_status: Annotated[str, Field(min_length=1)]


class SweepExportSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sweep: BuiltPolicySweep
    metrics: Annotated[tuple[SweepMetric, ...], Field(min_length=1)]
    thresholds: tuple[SweepThresholdSpec, ...] = ()

    @model_validator(mode="after")
    def validate_evidence_contract(self) -> SweepExportSpec:
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError("sweep export metrics must be unique")
        threshold_metrics = tuple(item.metric for item in self.thresholds)
        if len(set(threshold_metrics)) != len(threshold_metrics):
            raise ValueError("sweep threshold metrics must be unique")
        if not set(threshold_metrics).issubset(self.metrics):
            raise ValueError("sweep threshold metric must be exported")
        return self


class SweepThresholdEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    threshold_status: str
    crossing: ThresholdCrossingResult


class SweepEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sweep_id: str
    matched_world_ids: tuple[int, ...]
    metrics: dict[str, SweepResponse]
    thresholds: dict[str, SweepThresholdEvidence]


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _execute(spec: SweepExportSpec, max_workers: int | None) -> CampaignResult:
    if max_workers is None:
        return run_campaign(spec.sweep.campaign)
    return run_campaign_parallel(spec.sweep.campaign, max_workers=max_workers)


def _build_evidence(spec: SweepExportSpec, result: CampaignResult) -> SweepEvidence:
    assert_matched_sweep_random_identity(spec.sweep, result)
    metrics = {
        metric.value: summarize_sweep(spec.sweep, result, metric=metric) for metric in spec.metrics
    }
    thresholds = {
        item.metric.value: SweepThresholdEvidence(
            threshold_status=item.threshold_status,
            crossing=detect_threshold_crossings(
                levels=metrics[item.metric.value].levels,
                responses=metrics[item.metric.value].responses,
                threshold=item.threshold,
            ),
        )
        for item in spec.thresholds
    }
    return SweepEvidence(
        sweep_id=spec.sweep.sweep_id,
        matched_world_ids=spec.sweep.campaign.world_ids,
        metrics=metrics,
        thresholds=thresholds,
    )


def _artifacts(
    spec: SweepExportSpec,
    result: CampaignResult,
    provenance: ArtifactProvenance,
) -> dict[str, bytes]:
    evidence = _build_evidence(spec, result)
    return {
        "sweep-config.json": _canonical_json(spec.model_dump(mode="json")),
        "provenance.json": _canonical_json(provenance.model_dump(mode="json")),
        "sweep-evidence.json": _canonical_json(evidence.model_dump(mode="json")),
    }


def export_bounded_sweep(
    sweep: BuiltPolicySweep,
    output_dir: Path,
    *,
    metrics: tuple[SweepMetric, ...],
    thresholds: tuple[SweepThresholdSpec, ...] = (),
    max_workers: int | None = None,
    source_revision: str = "unspecified",
) -> Path:
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"export destination is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    spec = SweepExportSpec(sweep=sweep, metrics=metrics, thresholds=thresholds)
    result = _execute(spec, max_workers)
    provenance = artifact_provenance(source_revision)
    artifacts = _artifacts(spec, result, provenance)
    for name, content in artifacts.items():
        (output_dir / name).write_bytes(content)
    manifest = {
        "schema_version": "0.1.0",
        "engine": {"name": "urban-field-dynamics", "version": version("urban-field-dynamics")},
        "sweep_id": sweep.sweep_id,
        "root_seed": sweep.campaign.root_seed,
        "matched_world_ids": list(sweep.campaign.world_ids),
        "evidence_status": "synthetic",
        "full_result_included": False,
        "replay_verification": "rerun full sweep and rebuild derived artifacts",
        "artifacts": [
            {
                "path": name,
                "sha256": _sha256_bytes(artifacts[name]),
                "media_type": "application/json",
            }
            for name in _ARTIFACT_NAMES
        ],
    }
    (output_dir / "manifest.json").write_bytes(_canonical_json(manifest))
    return output_dir


def verify_bounded_sweep(
    output_dir: Path,
    *,
    max_workers: int | None = None,
) -> SweepEvidence:
    output_dir = Path(output_dir)
    try:
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SweepExportVerificationError("manifest.json is missing or invalid") from exc
    declared = manifest.get("artifacts", [])
    if [item.get("path") for item in declared] != list(_ARTIFACT_NAMES):
        raise SweepExportVerificationError("manifest artifact list differs from contract")
    expected_paths = {"manifest.json", *_ARTIFACT_NAMES}
    actual_paths = {path.name for path in output_dir.iterdir() if path.is_file()}
    if actual_paths != expected_paths:
        raise SweepExportVerificationError("export directory contains undeclared files")
    for artifact in declared:
        name = artifact["path"]
        content = (output_dir / name).read_bytes()
        if _sha256_bytes(content) != artifact.get("sha256"):
            raise SweepExportVerificationError(f"sha256 mismatch: {name}")
    try:
        spec = SweepExportSpec.model_validate_json(
            (output_dir / "sweep-config.json").read_text(encoding="utf-8")
        )
        provenance = ArtifactProvenance.model_validate_json(
            (output_dir / "provenance.json").read_text(encoding="utf-8")
        )
    except (ValueError, UnicodeDecodeError) as exc:
        raise SweepExportVerificationError("sweep config or provenance parsing failed") from exc
    result = _execute(spec, max_workers)
    expected = _artifacts(spec, result, provenance)
    for name, content in expected.items():
        if (output_dir / name).read_bytes() != content:
            raise SweepExportVerificationError(f"replayed artifact differs: {name}")
    return _build_evidence(spec, result)
