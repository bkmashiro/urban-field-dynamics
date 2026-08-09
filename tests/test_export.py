import json

import pytest

from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.export import (
    ExportVerificationError,
    export_campaign,
    verify_export,
)
from urban_field_dynamics.smoke import smoke_campaign_spec


def test_export_is_deterministic_and_replay_verifiable(tmp_path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    export_campaign(smoke_campaign_spec(), first)
    export_campaign(smoke_campaign_spec(), second)

    assert verify_export(first).campaign_id == "smoke-v1"
    assert verify_export(second).campaign_id == "smoke-v1"
    for name in (
        "campaign-config.json",
        "campaign-result.json",
        "summary.json",
        "manifest.json",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_manifest_marks_smoke_evidence_as_synthetic(tmp_path) -> None:
    export_campaign(smoke_campaign_spec(), tmp_path)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["evidence_status"] == "synthetic"
    assert manifest["model_scope"] == "redevelopment-only qualification slice"
    assert "generated_at" not in manifest


def test_verifier_fails_closed_after_artifact_tampering(tmp_path) -> None:
    export_campaign(smoke_campaign_spec(), tmp_path)
    result_path = tmp_path / "campaign-result.json"
    result_path.write_text(result_path.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(ExportVerificationError, match="sha256 mismatch"):
        verify_export(tmp_path)


def test_smoke_fixture_discriminates_policy_and_inertia() -> None:
    summary = run_campaign(smoke_campaign_spec()).summary.arms

    assert summary["p1"].total_redevelopments > summary["p0"].total_redevelopments
    assert summary["p0-no-inertia"].total_redevelopments > summary["p0"].total_redevelopments


def test_export_refuses_nonempty_destination(tmp_path) -> None:
    (tmp_path / "unrelated.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        export_campaign(smoke_campaign_spec(), tmp_path)
