"""Deterministic campaign export and full replay verification."""

from __future__ import annotations

import json
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Any

from urban_field_dynamics.campaign import (
    CampaignResult,
    CampaignSpec,
    run_campaign,
)

_ARTIFACT_NAMES = (
    "campaign-config.json",
    "campaign-result.json",
    "summary.json",
)


class ExportVerificationError(RuntimeError):
    """Raised when an exported campaign fails integrity or replay checks."""


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_canonical_json(value))


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def export_campaign(spec: CampaignSpec, output_dir: Path) -> Path:
    """Run and export a campaign to a new or empty directory."""

    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"export destination is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_campaign(spec)
    _write_json(
        output_dir / "campaign-config.json",
        spec.model_dump(mode="json"),
    )
    _write_json(
        output_dir / "campaign-result.json",
        result.model_dump(mode="json"),
    )
    _write_json(
        output_dir / "summary.json",
        result.summary.model_dump(mode="json"),
    )

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
        "model_scope": "redevelopment-only qualification slice",
        "artifacts": [
            {
                "path": name,
                "sha256": _sha256(output_dir / name),
                "media_type": "application/json",
            }
            for name in _ARTIFACT_NAMES
        ],
    }
    _write_json(output_dir / "manifest.json", manifest)
    return output_dir


def verify_export(output_dir: Path) -> CampaignResult:
    """Verify artifact integrity, parse contracts, and replay the full campaign."""

    output_dir = Path(output_dir)
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ExportVerificationError("manifest.json is missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ExportVerificationError("manifest.json is invalid") from exc

    expected_paths = {"manifest.json"}
    for artifact in manifest.get("artifacts", []):
        relative_path = artifact.get("path")
        expected_hash = artifact.get("sha256")
        if relative_path not in _ARTIFACT_NAMES:
            raise ExportVerificationError(f"unexpected artifact path: {relative_path}")
        artifact_path = output_dir / relative_path
        expected_paths.add(relative_path)
        if not artifact_path.is_file():
            raise ExportVerificationError(f"artifact is missing: {relative_path}")
        if _sha256(artifact_path) != expected_hash:
            raise ExportVerificationError(f"sha256 mismatch: {relative_path}")

    actual_paths = {path.name for path in output_dir.iterdir() if path.is_file()}
    if actual_paths != expected_paths:
        raise ExportVerificationError("export directory contains undeclared files")

    try:
        spec = CampaignSpec.model_validate_json(
            (output_dir / "campaign-config.json").read_text(encoding="utf-8")
        )
        recorded = CampaignResult.model_validate_json(
            (output_dir / "campaign-result.json").read_text(encoding="utf-8")
        )
        summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ExportVerificationError("export contract parsing failed") from exc

    replayed = run_campaign(spec)
    if replayed != recorded:
        raise ExportVerificationError("campaign replay differs from recorded result")
    if recorded.summary.model_dump(mode="json") != summary:
        raise ExportVerificationError("summary differs from campaign result")
    return recorded
