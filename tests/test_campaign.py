import pytest

from urban_field_dynamics.campaign import CampaignArm, CampaignSpec, run_campaign
from urban_field_dynamics.contracts import (
    EvidenceStatus,
    LandUse,
    PinKind,
    SpatialUnitSpec,
)
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import MechanismSwitches, PolicySpec


def unit() -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id="u-001",
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESEARCH,
        pin_kind=PinKind.SOFT,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=120.0,
        transition_cost=50.0,
        accessibility=0.2,
        accessibility_value_factor=40.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def spec() -> CampaignSpec:
    p0 = PolicySpec(
        policy_id="p0",
        intervention_year=2026,
        accessibility_delta=0.0,
    )
    p1 = PolicySpec(
        policy_id="p1",
        intervention_year=2026,
        accessibility_delta=0.4,
    )
    return CampaignSpec(
        campaign_id="smoke-v1",
        root_seed=20260809,
        world_ids=tuple(range(8)),
        schedule=ScheduleConfig(
            start_year=2026,
            end_year=2030,
            replan_years={2026},
        ),
        units=(unit(),),
        arms=(
            CampaignArm(arm_id="p0", policy=p0),
            CampaignArm(arm_id="p1", policy=p1),
            CampaignArm(
                arm_id="p0-no-inertia",
                policy=p0,
                transition_inertia_enabled=False,
            ),
        ),
        development_shock_scale=15.0,
    )


def test_campaign_runs_three_arms_over_eight_matched_worlds() -> None:
    result = run_campaign(spec())

    assert result.summary.run_count == 24
    assert len(result.runs) == 24
    assert result.summary.matched_world_ids == tuple(range(8))


def test_campaign_arms_share_development_tapes_by_world() -> None:
    result = run_campaign(spec())

    for world_id in range(8):
        traces = [
            run.world.development_shocks for run in result.runs if run.world.world_id == world_id
        ]
        assert len(traces) == 3
        assert traces[0] == traces[1] == traces[2]


def test_investment_and_no_inertia_do_not_underperform_synthetic_baseline() -> None:
    result = run_campaign(spec())
    summaries = result.summary.arms

    assert summaries["p1"].worlds_with_redevelopment >= summaries["p0"].worlds_with_redevelopment
    assert (
        summaries["p0-no-inertia"].worlds_with_redevelopment
        >= summaries["p0"].worlds_with_redevelopment
    )
    assert summaries["p1"].worlds_with_redevelopment > 0
    assert summaries["p0-no-inertia"].worlds_with_redevelopment == 8


def test_campaign_replay_is_exact() -> None:
    assert run_campaign(spec()) == run_campaign(spec())


def test_public_coordination_ablation_blocks_policy_but_preserves_policy_identity() -> None:
    campaign = spec().model_copy(
        update={
            "world_ids": (0,),
            "arms": (
                CampaignArm(
                    arm_id="p1",
                    policy=PolicySpec(
                        policy_id="p1",
                        intervention_year=2026,
                        accessibility_delta=0.4,
                    ),
                ),
                CampaignArm(
                    arm_id="p1-no-coordination",
                    policy=PolicySpec(
                        policy_id="p1",
                        intervention_year=2026,
                        accessibility_delta=0.4,
                    ),
                    mechanisms=MechanismSwitches(public_coordination_enabled=False),
                ),
            ),
        }
    )

    result = run_campaign(campaign)
    by_arm = {run.arm_id: run.world for run in result.runs}
    assert by_arm["p1"].final_accessibility["u-001"] == pytest.approx(0.6)
    assert by_arm["p1-no-coordination"].final_accessibility == {"u-001": 0.2}
    assert by_arm["p1"].development_shocks == by_arm["p1-no-coordination"].development_shocks
