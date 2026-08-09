"""Frozen synthetic smoke campaign used for mechanism qualification."""

from urban_field_dynamics.campaign import CampaignArm, CampaignSpec
from urban_field_dynamics.contracts import (
    EvidenceStatus,
    LandUse,
    PinKind,
    SpatialUnitSpec,
)
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import PolicySpec


def smoke_campaign_spec() -> CampaignSpec:
    """Return the deterministic P0/P1/no-inertia eight-world smoke matrix."""

    units = (
        SpatialUnitSpec(
            unit_id="innovation-soft-pin",
            area_sqm=10_000.0,
            current_use=LandUse.RESIDENTIAL,
            candidate_use=LandUse.RESEARCH,
            pin_kind=PinKind.SOFT,
            asset_age_years=10,
            design_life_years=50,
            keep_npv=100.0,
            candidate_base_npv=115.0,
            transition_cost=50.0,
            accessibility=0.2,
            accessibility_value_factor=40.0,
            evidence_status=EvidenceStatus.SYNTHETIC,
        ),
        SpatialUnitSpec(
            unit_id="community-renewal",
            area_sqm=8_000.0,
            current_use=LandUse.RESIDENTIAL,
            candidate_use=LandUse.MIXED,
            pin_kind=PinKind.SOFT,
            asset_age_years=25,
            design_life_years=50,
            keep_npv=100.0,
            candidate_base_npv=99.0,
            transition_cost=40.0,
            accessibility=0.3,
            accessibility_value_factor=30.0,
            evidence_status=EvidenceStatus.SYNTHETIC,
        ),
        SpatialUnitSpec(
            unit_id="heritage-hard-pin",
            area_sqm=6_000.0,
            current_use=LandUse.GREEN,
            candidate_use=LandUse.PUBLIC_SERVICE,
            pin_kind=PinKind.HARD,
            asset_age_years=80,
            design_life_years=50,
            keep_npv=90.0,
            candidate_base_npv=180.0,
            transition_cost=0.0,
            accessibility=0.5,
            accessibility_value_factor=20.0,
            evidence_status=EvidenceStatus.SYNTHETIC,
        ),
    )
    baseline = PolicySpec(
        policy_id="p0",
        intervention_year=2026,
        accessibility_delta=0.0,
    )
    investment = PolicySpec(
        policy_id="p1",
        intervention_year=2026,
        accessibility_delta=0.35,
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
        units=units,
        arms=(
            CampaignArm(arm_id="p0", policy=baseline),
            CampaignArm(arm_id="p1", policy=investment),
            CampaignArm(
                arm_id="p0-no-inertia",
                policy=baseline,
                transition_inertia_enabled=False,
            ),
        ),
        development_shock_scale=12.0,
    )
