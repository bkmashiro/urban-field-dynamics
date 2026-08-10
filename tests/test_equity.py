from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.equity import observe_campaign_equity
from urban_field_dynamics.scaled_integrated import scaled_integrated_campaign


def test_scaled_equity_observer_reports_declared_groups_and_disparities() -> None:
    spec = scaled_integrated_campaign(world_count=1)
    result = run_campaign(spec)

    equity = observe_campaign_equity(spec, result)
    p3 = equity.arms["p3"]

    assert set(p3.groups) == {
        "students",
        "research-talent",
        "service-workers",
        "older-adults",
        "families",
        "accessibility-needs",
    }
    assert all(group.mean_population > 0.0 for group in p3.groups.values())
    assert all(0.0 <= group.mean_relocation_rate <= 1.0 for group in p3.groups.values())
    assert p3.accessibility_gap >= 0.0
    assert p3.environment_quality_gap >= 0.0
    assert p3.service_access_gap >= 0.0
    assert p3.rent_burden_gap >= 0.0


def test_equity_observer_distinguishes_policy_arms_without_claiming_direction() -> None:
    spec = scaled_integrated_campaign(world_count=1)
    result = run_campaign(spec)
    equity = observe_campaign_equity(spec, result)

    p0 = equity.arms["p0"]
    p3 = equity.arms["p3"]
    assert (
        p0.accessibility_gap,
        p0.environment_quality_gap,
        p0.service_access_gap,
        p0.rent_burden_gap,
    ) != (
        p3.accessibility_gap,
        p3.environment_quality_gap,
        p3.service_access_gap,
        p3.rent_burden_gap,
    )
