import json

import pytest

from urban_field_dynamics.bounded_export import (
    BoundedExportVerificationError,
    export_bounded_campaign,
    verify_bounded_export,
)
from urban_field_dynamics.integrated import integrated_smoke_campaign


def test_bounded_export_replays_without_full_campaign_result(tmp_path) -> None:
    output = export_bounded_campaign(
        integrated_smoke_campaign(world_count=2),
        tmp_path,
        source_revision="04effa1a5c4c3426366ae910612af28d5d534735",
    )
    verified = verify_bounded_export(output)

    provenance = json.loads((tmp_path / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["source_revision"] == "04effa1a5c4c3426366ae910612af28d5d534735"

    assert verified.campaign_id == "integrated-qualification-2"
    assert not (tmp_path / "campaign-result.json").exists()
    assert (tmp_path / "decision-classifications.json").is_file()
    assert (tmp_path / "representative-worlds.json").is_file()


def test_bounded_export_is_byte_deterministic(tmp_path) -> None:
    first = export_bounded_campaign(
        integrated_smoke_campaign(world_count=2),
        tmp_path / "first",
    )
    second = export_bounded_campaign(
        integrated_smoke_campaign(world_count=2),
        tmp_path / "second",
    )

    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }


def test_bounded_verifier_fails_closed_after_tampering(tmp_path) -> None:
    export_bounded_campaign(integrated_smoke_campaign(world_count=2), tmp_path)
    summary_path = tmp_path / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["run_count"] = 999
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    with pytest.raises(BoundedExportVerificationError, match="sha256 mismatch"):
        verify_bounded_export(tmp_path)
