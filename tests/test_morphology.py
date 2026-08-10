import math

import pytest

from urban_field_dynamics.campaign import CampaignResult, CampaignRun, CampaignSummary
from urban_field_dynamics.contracts import LandUse
from urban_field_dynamics.morphology import (
    DecisionCategory,
    DecisionClassificationSpec,
    classify_decision_categories,
    observe_world_morphology,
)
from urban_field_dynamics.spatial import FocusZoneSpec, StylizedGridSpec, generate_stylized_grid
from urban_field_dynamics.world import WorldResult


def world(
    *,
    world_id: int,
    policy_id: str,
    redevelopment: dict[str, int | None],
    final_uses: dict[str, LandUse] | None = None,
) -> WorldResult:
    return WorldResult(
        root_seed=1,
        world_id=world_id,
        policy_id=policy_id,
        transition_inertia_enabled=True,
        redevelopment_years=redevelopment,
        final_accessibility={unit_id: 0.5 for unit_id in redevelopment},
        final_uses=(
            final_uses
            if final_uses is not None
            else {unit_id: LandUse.RESIDENTIAL for unit_id in redevelopment}
        ),
        development_shocks={},
    )


def campaign() -> CampaignResult:
    runs = []
    for world_id in range(10):
        runs.extend(
            (
                CampaignRun(
                    arm_id="p0",
                    world=world(
                        world_id=world_id,
                        policy_id="p0",
                        redevelopment={"u-keep": None, "u-change": 2026, "u-trigger": None},
                    ),
                ),
                CampaignRun(
                    arm_id="p1",
                    world=world(
                        world_id=world_id,
                        policy_id="p1",
                        redevelopment={"u-keep": None, "u-change": 2026, "u-trigger": 2027},
                    ),
                ),
            )
        )
    return CampaignResult(
        campaign_id="classification-test",
        runs=tuple(runs),
        summary=CampaignSummary(run_count=20, matched_world_ids=tuple(range(10)), arms={}),
    )


def test_decision_categories_distinguish_robust_keep_transition_and_policy_trigger() -> None:
    result = classify_decision_categories(
        campaign(),
        DecisionClassificationSpec(
            arm_ids=("p0", "p1"),
            commitment_probability=0.8,
            trigger_probability_range=0.4,
        ),
    )
    by_id = {item.unit_id: item for item in result.units}

    assert by_id["u-keep"].category is DecisionCategory.COMMITMENT
    assert by_id["u-keep"].commitment_outcome == "keep"
    assert by_id["u-change"].category is DecisionCategory.COMMITMENT
    assert by_id["u-change"].commitment_outcome == "transition"
    assert by_id["u-trigger"].category is DecisionCategory.TRIGGER
    assert by_id["u-trigger"].transition_probability_by_arm == {"p0": 0.0, "p1": 1.0}


def test_morphology_observer_reports_entropy_mixing_and_label_subsets() -> None:
    grid = generate_stylized_grid(
        StylizedGridSpec(
            root_seed=1,
            rows=2,
            columns=2,
            cell_size_m=100.0,
            corridor_center_column=0,
            corridor_half_width_cells=0,
            focus_zones=(
                FocusZoneSpec(
                    zone_id="focus-aa",
                    center_row=0,
                    center_column=0,
                    radius_cells=1,
                ),
            ),
        )
    )
    uses = {
        "cell-r00-c00": LandUse.RESIDENTIAL,
        "cell-r00-c01": LandUse.RESEARCH,
        "cell-r01-c00": LandUse.RESEARCH,
        "cell-r01-c01": LandUse.RESIDENTIAL,
    }
    observation = observe_world_morphology(
        world(
            world_id=0,
            policy_id="p0",
            redevelopment={
                "cell-r00-c00": 2026,
                "cell-r00-c01": None,
                "cell-r01-c00": 2027,
                "cell-r01-c01": None,
            },
            final_uses=uses,
        ),
        grid,
    )

    assert observation.redevelopment_share == pytest.approx(0.5)
    assert observation.normalized_land_use_entropy == pytest.approx(math.log(2) / math.log(6))
    assert observation.adjacency_mixing_rate == pytest.approx(1.0)
    assert observation.corridor_redevelopment_share == pytest.approx(1.0)
    assert 0.0 <= observation.focus_zone_redevelopment_share["focus-aa"] <= 1.0
