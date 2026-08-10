import pytest

from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.integrated import integrated_smoke_campaign
from urban_field_dynamics.sweep import (
    PolicySweepSpec,
    build_policy_intensity_sweep,
    scale_policy,
    summarize_sweep,
)
from urban_field_dynamics.world import PolicySpec


def policy() -> PolicySpec:
    return PolicySpec(
        policy_id="target",
        intervention_year=2030,
        accessibility_delta=0.2,
        accessibility_delta_by_unit={"unit-aa": 0.4},
        transport_capacity_multiplier_by_edge={"edge-aa": 3.0},
        transport_time_multiplier_by_edge={"edge-aa": 0.5},
        green_fraction_delta_by_unit={"unit-aa": 0.3},
        service_quality_delta_by_location={"zone-aa": 0.2},
        service_capacity_multiplier_by_location={"zone-aa": 2.0},
    )


def test_policy_scaling_interpolates_multipliers_around_one() -> None:
    zero = scale_policy(policy(), intensity=0.0, policy_id="sweep-zero")
    half = scale_policy(policy(), intensity=0.5, policy_id="sweep-half")
    full = scale_policy(policy(), intensity=1.0, policy_id="sweep-full")

    assert zero.accessibility_delta == 0.0
    assert zero.transport_capacity_multiplier_by_edge == {"edge-aa": 1.0}
    assert zero.transport_time_multiplier_by_edge == {"edge-aa": 1.0}
    assert half.transport_capacity_multiplier_by_edge == {"edge-aa": 2.0}
    assert half.transport_time_multiplier_by_edge == {"edge-aa": 0.75}
    assert full.model_dump(exclude={"policy_id"}) == policy().model_dump(exclude={"policy_id"})


def test_matched_sweep_preserves_event_tapes_and_reports_ordered_response() -> None:
    base = integrated_smoke_campaign(world_count=1)
    sweep = build_policy_intensity_sweep(
        base,
        PolicySweepSpec(
            sweep_id="p3-intensity",
            source_arm_id="p3",
            intensities=(0.0, 0.5, 1.0),
        ),
    )
    result = run_campaign(sweep.campaign)

    worlds = [run.world for run in result.runs]
    assert len({str(world.development_shocks) for world in worlds}) == 1
    assert len({str(world.household_taste_shocks) for world in worlds}) == 1
    assert len({str(world.firm_taste_shocks) for world in worlds}) == 1
    response = summarize_sweep(sweep, result, metric="final_accessibility")
    assert response.levels == (0.0, 0.5, 1.0)
    assert len(response.responses) == 3
    assert len(set(response.responses)) > 1


def test_sweep_rejects_duplicate_intensities() -> None:
    with pytest.raises(ValueError, match="unique"):
        PolicySweepSpec(
            sweep_id="duplicate",
            source_arm_id="p3",
            intensities=(0.0, 0.0),
        )
