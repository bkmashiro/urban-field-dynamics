import json

import pytest

from urban_field_dynamics.scaled_integrated import scaled_integrated_campaign
from urban_field_dynamics.sweep import PolicySweepSpec, SweepMetric, build_policy_intensity_sweep
from urban_field_dynamics.sweep_export import (
    SweepExportVerificationError,
    SweepThresholdSpec,
    export_bounded_sweep,
    verify_bounded_sweep,
)


def sweep_fixture():
    return build_policy_intensity_sweep(
        scaled_integrated_campaign(world_count=2, end_year=2028),
        PolicySweepSpec(
            sweep_id="scaled-p3-sweep-test",
            source_arm_id="p3",
            intensities=(0.0, 0.5, 1.0),
        ),
    )


def test_bounded_sweep_replays_world_responses_and_threshold_brackets(tmp_path) -> None:
    output = export_bounded_sweep(
        sweep_fixture(),
        tmp_path,
        metrics=(SweepMetric.FINAL_ACCESSIBILITY, SweepMetric.FINAL_RENT),
        thresholds=(
            SweepThresholdSpec(
                metric=SweepMetric.FINAL_ACCESSIBILITY,
                threshold=0.523,
                threshold_status="synthetic-engineering-demo",
            ),
        ),
    )
    verified = verify_bounded_sweep(output)

    evidence = json.loads((output / "sweep-evidence.json").read_text())
    assert verified.sweep_id == "scaled-p3-sweep-test"
    assert len(evidence["metrics"]["final_accessibility"]["world_responses"]) == 2
    assert evidence["thresholds"]["final_accessibility"]["threshold_status"] == (
        "synthetic-engineering-demo"
    )


def test_bounded_sweep_fails_closed_after_tampering(tmp_path) -> None:
    output = export_bounded_sweep(
        sweep_fixture(),
        tmp_path,
        metrics=(SweepMetric.FINAL_ACCESSIBILITY,),
    )
    evidence_path = output / "sweep-evidence.json"
    evidence_path.write_text("{}\n")

    with pytest.raises(SweepExportVerificationError, match="sha256 mismatch"):
        verify_bounded_sweep(output)
