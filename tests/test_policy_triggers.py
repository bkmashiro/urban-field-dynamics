import pytest

from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import (
    PolicySpec,
    PolicyTriggerSpec,
    TriggerMetric,
    TriggerOperator,
    WorldRunConfig,
    run_world,
)


def unit() -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id="unit-aa",
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.MIXED,
        pin_kind=PinKind.HARD,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=100.0,
        transition_cost=50.0,
        accessibility=0.4,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def run(policy: PolicySpec):
    return run_world(
        WorldRunConfig(
            root_seed=1,
            world_id=0,
            schedule=ScheduleConfig(
                start_year=2026,
                end_year=2030,
                replan_years={2026, 2030},
            ),
            units=(unit(),),
            policy=policy,
        )
    )


def test_legacy_policy_activates_at_fixed_intervention_year() -> None:
    result = run(PolicySpec(policy_id="fixed", intervention_year=2026, accessibility_delta=0.2))

    assert result.policy_activation_year == 2026
    assert result.final_accessibility["unit-aa"] == pytest.approx(0.6)


def test_trigger_policy_activates_only_when_condition_is_met() -> None:
    result = run(
        PolicySpec(
            policy_id="triggered",
            intervention_year=2026,
            accessibility_delta=0.2,
            activation_triggers=(
                PolicyTriggerSpec(
                    metric=TriggerMetric.MEAN_ACCESSIBILITY,
                    operator=TriggerOperator.LE,
                    threshold=0.5,
                ),
            ),
        )
    )

    assert result.policy_activation_year == 2026
    assert result.final_accessibility["unit-aa"] == pytest.approx(0.6)


def test_unmet_trigger_leaves_policy_inactive_across_replans() -> None:
    result = run(
        PolicySpec(
            policy_id="inactive",
            intervention_year=2026,
            accessibility_delta=0.2,
            activation_triggers=(
                PolicyTriggerSpec(
                    metric=TriggerMetric.MEAN_ACCESSIBILITY,
                    operator=TriggerOperator.LE,
                    threshold=0.3,
                ),
            ),
        )
    )

    assert result.policy_activation_year is None
    assert result.final_accessibility["unit-aa"] == 0.4
