from urban_field_dynamics.analysis import integrated_qualification_diagnostics
from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.scaled_integrated import scaled_integrated_campaign
from urban_field_dynamics.transport import TransportMode


def test_scaled_integrated_contract_has_1200_cells_and_48_explicit_zones() -> None:
    spec = scaled_integrated_campaign(world_count=1)

    assert len(spec.units) == 1_200
    assert len(spec.locations) == 48
    assert len(spec.location_members) == 48
    assert {member for members in spec.location_members.values() for member in members} == {
        unit.unit_id for unit in spec.units
    }
    assert len(spec.households) == 6
    assert len(spec.firms) == 6
    assert len(spec.arms) == 13
    p3 = next(arm for arm in spec.arms if arm.arm_id == "p3")
    assert len(p3.policy.service_quality_delta_by_location) == 48
    assert len(p3.policy.service_capacity_multiplier_by_location) == 48
    assert scaled_integrated_campaign(world_count=32).campaign_id == (
        "scaled-integrated-qualification-32"
    )
    full_horizon = scaled_integrated_campaign(world_count=8, end_year=2050)
    assert full_horizon.campaign_id == "scaled-integrated-2050-canary-8"
    assert full_horizon.schedule.replan_years == {2026, 2030, 2035, 2040, 2045}
    assert {edge.mode for edge in spec.transport_edges} == set(TransportMode)


def test_scaled_integrated_one_world_executes_all_matched_arms() -> None:
    result = run_campaign(scaled_integrated_campaign(world_count=1))

    assert result.summary.run_count == 13
    worlds = [run.world for run in result.runs]
    assert all(len(world.final_uses) == 1_200 for world in worlds)
    assert all(len(world.final_rents) == 48 for world in worlds)
    assert len({str(world.development_shocks) for world in worlds}) == 1
    assert len({str(world.household_taste_shocks) for world in worlds}) == 1
    by_arm = {run.arm_id: run.world for run in result.runs}
    dynamic_worlds = [
        world for arm_id, world in by_arm.items() if arm_id != "p3-no-cohort-dynamics"
    ]
    assert len({str(world.firm_taste_shocks) for world in dynamic_worlds}) == 1
    p3 = by_arm["p3"]
    no_dynamics = by_arm["p3-no-cohort-dynamics"]
    shared_comparisons = 0
    for year, cohort_shocks in no_dynamics.firm_taste_shocks.items():
        shared_ids = set(cohort_shocks) & set(p3.firm_taste_shocks[year])
        for cohort_id in shared_ids:
            assert p3.firm_taste_shocks[year][cohort_id] == cohort_shocks[cohort_id]
            shared_comparisons += 1
    assert shared_comparisons > 0
    summaries = result.summary.arms
    assert summaries["p1"].mean_final_accessibility > summaries["p0"].mean_final_accessibility
    assert (
        summaries["p2"].mean_final_environment_quality
        > summaries["p0"].mean_final_environment_quality
    )
    diagnostics = integrated_qualification_diagnostics(result, checkpoints=(1,))
    assert diagnostics.comparisons["service-provision-effect"].checkpoints[-1].mean_delta > 0.0
    assert diagnostics.comparisons["cohort-dynamics-population-effect"].deltas[0] > 0.0
    assert "cohort-dynamics-employment-effect" in diagnostics.comparisons
    assert "labor-matching-rent-effect" in diagnostics.comparisons
    assert summaries["p3"].mean_final_unemployment_rate is not None
    assert 0.0 <= summaries["p3"].mean_final_unemployment_rate <= 1.0
    assert summaries["p3-no-labor-matching"].mean_final_unemployment_rate is None
