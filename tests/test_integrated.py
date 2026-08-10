from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.integrated import integrated_smoke_campaign


def test_integrated_smoke_has_four_policies_and_six_matched_ablations() -> None:
    spec = integrated_smoke_campaign(world_count=8)

    assert spec.world_ids == tuple(range(8))
    assert {arm.arm_id for arm in spec.arms} == {
        "p0",
        "p1",
        "p2",
        "p3",
        "p3-no-inertia",
        "p3-no-agglomeration",
        "p3-no-transport-attraction",
        "p3-no-seasonality",
        "p3-no-environmental-exposure",
        "p3-no-public-coordination",
    }


def test_larger_integrated_campaign_is_not_labelled_as_smoke() -> None:
    assert integrated_smoke_campaign(world_count=64).campaign_id == "integrated-qualification-64"


def test_integrated_smoke_runs_all_arms_and_preserves_event_tapes() -> None:
    result = run_campaign(integrated_smoke_campaign(world_count=2))

    assert result.summary.run_count == 20
    for world_id in range(2):
        worlds = [run.world for run in result.runs if run.world.world_id == world_id]
        assert len(worlds) == 10
        assert len({str(world.development_shocks) for world in worlds}) == 1
        assert len({str(world.household_taste_shocks) for world in worlds}) == 1
        assert len({str(world.firm_taste_shocks) for world in worlds}) == 1


def test_integrated_policy_and_mechanism_effects_are_observable_in_smoke() -> None:
    result = run_campaign(integrated_smoke_campaign(world_count=2))
    summaries = result.summary.arms

    assert summaries["p1"].mean_final_accessibility != summaries["p0"].mean_final_accessibility
    assert (
        summaries["p2"].mean_final_environment_quality
        > summaries["p0"].mean_final_environment_quality
    )
    assert (
        summaries["p3-no-transport-attraction"].mean_final_accessibility
        < summaries["p3"].mean_final_accessibility
    )
    assert (
        summaries["p3-no-environmental-exposure"].mean_final_environment_quality
        != summaries["p3"].mean_final_environment_quality
    )
    assert summaries["p3-no-inertia"].mean_redevelopments > summaries["p3"].mean_redevelopments
    assert summaries["p3"].mean_seasonal_heat_range > 0.0
    assert summaries["p3-no-seasonality"].mean_seasonal_heat_range == 0.0
    assert (
        summaries["p3-no-agglomeration"].mean_firm_relocations,
        summaries["p3-no-agglomeration"].mean_final_accessibility,
        summaries["p3-no-agglomeration"].mean_final_rent,
    ) != (
        summaries["p3"].mean_firm_relocations,
        summaries["p3"].mean_final_accessibility,
        summaries["p3"].mean_final_rent,
    )
