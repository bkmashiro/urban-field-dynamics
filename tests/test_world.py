import pytest

from urban_field_dynamics.contracts import (
    EvidenceStatus,
    LandUse,
    PinKind,
    SpatialUnitSpec,
)
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def make_unit(*, pin_kind: PinKind = PinKind.SOFT) -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id="u-001",
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESEARCH,
        pin_kind=pin_kind,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=120.0,
        transition_cost=50.0,
        accessibility=0.2,
        accessibility_value_factor=40.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def run(
    *,
    policy: PolicySpec,
    pin_kind: PinKind = PinKind.SOFT,
    transition_inertia_enabled: bool = True,
    shock_scale: float = 0.0,
):
    return run_world(
        WorldRunConfig(
            root_seed=20260809,
            world_id=3,
            schedule=ScheduleConfig(
                start_year=2026,
                end_year=2030,
                replan_years={2026},
            ),
            units=(make_unit(pin_kind=pin_kind),),
            policy=policy,
            transition_inertia_enabled=transition_inertia_enabled,
            development_shock_scale=shock_scale,
        )
    )


def test_accessibility_policy_triggers_redevelopment_while_baseline_does_not() -> None:
    baseline = run(
        policy=PolicySpec(
            policy_id="p0",
            intervention_year=2026,
            accessibility_delta=0.0,
        )
    )
    investment = run(
        policy=PolicySpec(
            policy_id="p1",
            intervention_year=2026,
            accessibility_delta=0.4,
        )
    )

    assert baseline.redevelopment_years == {"u-001": None}
    assert investment.redevelopment_years == {"u-001": 2026}
    assert baseline.final_accessibility == {"u-001": 0.2}
    assert investment.final_accessibility["u-001"] == pytest.approx(0.6)


def test_no_inertia_ablation_changes_baseline_redevelopment() -> None:
    result = run(
        policy=PolicySpec(
            policy_id="p0-no-inertia",
            intervention_year=2026,
            accessibility_delta=0.0,
        ),
        transition_inertia_enabled=False,
    )

    assert result.redevelopment_years == {"u-001": 2026}


def test_hard_pin_survives_policy_and_no_inertia_ablation() -> None:
    result = run(
        policy=PolicySpec(
            policy_id="p1-no-inertia",
            intervention_year=2026,
            accessibility_delta=0.8,
        ),
        pin_kind=PinKind.HARD,
        transition_inertia_enabled=False,
    )

    assert result.redevelopment_years == {"u-001": None}
    assert result.final_uses == {"u-001": LandUse.RESIDENTIAL}


def test_matched_policy_runs_consume_the_same_development_event_tape() -> None:
    baseline = run(
        policy=PolicySpec(
            policy_id="p0",
            intervention_year=2026,
            accessibility_delta=0.0,
        ),
        shock_scale=5.0,
    )
    investment = run(
        policy=PolicySpec(
            policy_id="p1",
            intervention_year=2026,
            accessibility_delta=0.4,
        ),
        shock_scale=5.0,
    )

    assert baseline.development_shocks == investment.development_shocks


def test_world_replay_is_exact() -> None:
    policy = PolicySpec(
        policy_id="p1",
        intervention_year=2026,
        accessibility_delta=0.4,
    )

    assert run(policy=policy, shock_scale=5.0) == run(policy=policy, shock_scale=5.0)
