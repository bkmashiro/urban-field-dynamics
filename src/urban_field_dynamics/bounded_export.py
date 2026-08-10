"""Bounded, deterministic, replay-verifiable integrated campaign export."""

from __future__ import annotations

import json
import statistics
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Any

from urban_field_dynamics.analysis import integrated_qualification_diagnostics
from urban_field_dynamics.campaign import CampaignResult, CampaignSpec, run_campaign
from urban_field_dynamics.morphology import (
    DecisionClassificationSpec,
    classify_decision_categories,
)

_ARTIFACT_NAMES = (
    "campaign-config.json",
    "summary.json",
    "qualification-diagnostics.json",
    "decision-classifications.json",
    "representative-worlds.json",
)


class BoundedExportVerificationError(RuntimeError):
    """Raised when a bounded artifact fails integrity or replay checks."""


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _checkpoints(world_count: int) -> tuple[int, ...]:
    declared = tuple(count for count in (8, 16, 32, 64, 128, 256, 512) if count <= world_count)
    return declared or (world_count,)


def _representative_worlds(
    spec: CampaignSpec,
    result: CampaignResult,
) -> dict[str, Any]:
    representatives: dict[str, Any] = {}
    for arm in spec.arms:
        candidates = [run.world for run in result.runs if run.arm_id == arm.arm_id]
        target = statistics.median(world.redevelopment_count for world in candidates)
        world = min(
            candidates,
            key=lambda item: (abs(item.redevelopment_count - target), item.world_id),
        )
        representatives[arm.arm_id] = {
            "world_id": world.world_id,
            "redevelopment_years": {
                unit_id: year
                for unit_id, year in world.redevelopment_years.items()
                if year is not None
            },
            "final_accessibility": world.final_accessibility,
            "final_uses": {
                unit_id: land_use.value for unit_id, land_use in world.final_uses.items()
            },
            "household_locations": world.household_locations,
            "firm_locations": world.firm_locations,
            "final_households": world.final_households,
            "final_jobs": world.final_jobs,
            "final_rents": world.final_rents,
            "final_environment_quality": world.final_environment_quality,
        }
    return representatives


def _derived_artifacts(
    spec: CampaignSpec,
    result: CampaignResult,
) -> dict[str, bytes]:
    arm_ids = tuple(arm.arm_id for arm in spec.arms)
    classifications = classify_decision_categories(
        result,
        DecisionClassificationSpec(
            arm_ids=arm_ids,
            commitment_probability=0.8,
            trigger_probability_range=0.25,
        ),
    )
    diagnostics = integrated_qualification_diagnostics(
        result,
        checkpoints=_checkpoints(len(spec.world_ids)),
    )
    return {
        "campaign-config.json": _canonical_json(spec.model_dump(mode="json")),
        "summary.json": _canonical_json(result.summary.model_dump(mode="json")),
        "qualification-diagnostics.json": _canonical_json(diagnostics.model_dump(mode="json")),
        "decision-classifications.json": _canonical_json(classifications.model_dump(mode="json")),
        "representative-worlds.json": _canonical_json(_representative_worlds(spec, result)),
    }


def export_bounded_campaign(spec: CampaignSpec, output_dir: Path) -> Path:
    """Run once and write a bounded derived evidence package."""

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"export destination is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_campaign(spec)
    artifacts = _derived_artifacts(spec, result)
    for name, content in artifacts.items():
        (output_dir / name).write_bytes(content)
    manifest = {
        "schema_version": "0.1.0",
        "engine": {
            "name": "urban-field-dynamics",
            "version": version("urban-field-dynamics"),
        },
        "campaign_id": spec.campaign_id,
        "root_seed": spec.root_seed,
        "matched_world_ids": list(spec.world_ids),
        "evidence_status": "synthetic",
        "model_scope": spec.model_scope,
        "full_result_included": False,
        "replay_verification": "rerun full campaign and rebuild derived artifacts",
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


def _load_manifest(output_dir: Path) -> dict[str, Any]:
    try:
        return json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundedExportVerificationError("manifest.json is missing or invalid") from exc


def verify_bounded_export(output_dir: Path) -> CampaignResult:
    """Verify hashes, rerun the full campaign, and rebuild every derived byte."""

    output_dir = Path(output_dir)
    manifest = _load_manifest(output_dir)
    declared = manifest.get("artifacts", [])
    if [item.get("path") for item in declared] != list(_ARTIFACT_NAMES):
        raise BoundedExportVerificationError("manifest artifact list differs from contract")
    expected_paths = {"manifest.json", *_ARTIFACT_NAMES}
    actual_paths = {path.name for path in output_dir.iterdir() if path.is_file()}
    if actual_paths != expected_paths:
        raise BoundedExportVerificationError("export directory contains undeclared files")
    for artifact in declared:
        name = artifact["path"]
        content = (output_dir / name).read_bytes()
        if _sha256_bytes(content) != artifact.get("sha256"):
            raise BoundedExportVerificationError(f"sha256 mismatch: {name}")
    try:
        spec = CampaignSpec.model_validate_json(
            (output_dir / "campaign-config.json").read_text(encoding="utf-8")
        )
    except (ValueError, UnicodeDecodeError) as exc:
        raise BoundedExportVerificationError("campaign config parsing failed") from exc
    replayed = run_campaign(spec)
    expected = _derived_artifacts(spec, replayed)
    for name, content in expected.items():
        if (output_dir / name).read_bytes() != content:
            raise BoundedExportVerificationError(f"replayed artifact differs: {name}")
    return replayed
