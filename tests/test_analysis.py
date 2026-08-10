import pytest

from urban_field_dynamics.analysis import (
    CampaignMetric,
    integrated_qualification_diagnostics,
    paired_convergence,
)
from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.integrated import integrated_smoke_campaign


@pytest.fixture(scope="module")
def result():
    return run_campaign(integrated_smoke_campaign(world_count=8))


def test_paired_accessibility_delta_uses_matched_world_order(result) -> None:
    diagnostic = paired_convergence(
        result,
        baseline_arm="p0",
        comparator_arm="p1",
        metric=CampaignMetric.FINAL_ACCESSIBILITY,
        checkpoints=(2, 4, 8),
    )

    assert diagnostic.world_ids == tuple(range(8))
    assert len(diagnostic.deltas) == 8
    assert diagnostic.checkpoints[-1].mean_delta == pytest.approx(
        sum(diagnostic.deltas) / len(diagnostic.deltas)
    )
    assert any(delta != 0.0 for delta in diagnostic.deltas)
    assert diagnostic.harmed_world_count == sum(delta < 0.0 for delta in diagnostic.deltas)


def test_paired_redevelopment_diagnostic_detects_inertia_effect(result) -> None:
    diagnostic = paired_convergence(
        result,
        baseline_arm="p3",
        comparator_arm="p3-no-inertia",
        metric=CampaignMetric.REDEVELOPMENTS,
        checkpoints=(8,),
    )

    assert diagnostic.checkpoints[-1].mean_delta > 0.0
    assert diagnostic.checkpoints[-1].ci95_lower <= diagnostic.checkpoints[-1].mean_delta
    assert diagnostic.checkpoints[-1].mean_delta <= diagnostic.checkpoints[-1].ci95_upper


def test_paired_convergence_rejects_unknown_arm(result) -> None:
    with pytest.raises(ValueError, match="campaign arm not found"):
        paired_convergence(
            result,
            baseline_arm="missing",
            comparator_arm="p1",
            metric=CampaignMetric.FINAL_RENT,
            checkpoints=(8,),
        )


def test_integrated_diagnostic_bundle_covers_declared_mechanisms(result) -> None:
    bundle = integrated_qualification_diagnostics(result, checkpoints=(4, 8))

    assert bundle.world_count == 8
    assert set(bundle.comparisons) == {
        "p1-vs-p0-accessibility",
        "p2-vs-p0-environment",
        "p3-vs-p0-rent",
        "inertia-effect",
        "agglomeration-effect",
        "transport-attraction-effect",
        "seasonality-effect",
        "environmental-exposure-effect",
        "public-coordination-effect",
    }
