from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.scaled_integrated import scaled_integrated_campaign
from urban_field_dynamics.stress import (
    StressEvidenceSpec,
    StressMatrixSpec,
    StressMetric,
    StressScenario,
    apply_stress,
    export_stress_matrix,
    verify_stress_export,
)


def test_stress_transform_changes_only_declared_exogenous_inputs() -> None:
    base = scaled_integrated_campaign(world_count=1, end_year=2028)
    scenario = StressScenario(
        scenario_id="combined",
        household_growth_rate_delta=0.01,
        firm_growth_rate_delta=-0.02,
        firm_death_probability_delta=0.03,
        firm_birth_probability_multiplier=0.5,
        transport_capacity_multiplier=0.7,
        heat_stress_delta=0.1,
        service_capacity_multiplier=0.8,
        annual_budget_multiplier=0.9,
        cumulative_budget_multiplier=0.8,
    )

    stressed = apply_stress(base, scenario)

    assert stressed.world_ids == base.world_ids
    assert stressed.root_seed == base.root_seed
    assert stressed.arms == base.arms
    assert (
        stressed.household_dynamics.mean_growth_rate
        == base.household_dynamics.mean_growth_rate + 0.01
    )
    assert (
        stressed.firm_dynamics.mean_employee_growth_rate
        == base.firm_dynamics.mean_employee_growth_rate - 0.02
    )
    assert (
        stressed.firm_dynamics.annual_death_probability
        == base.firm_dynamics.annual_death_probability + 0.03
    )
    assert stressed.transport_edges[0].capacity == base.transport_edges[0].capacity * 0.7
    assert stressed.seasonal_environment[0].heat_stress == min(
        1.0, base.seasonal_environment[0].heat_stress + 0.1
    )
    assert (
        stressed.infrastructure_ledger.annual_budget
        == base.infrastructure_ledger.annual_budget * 0.9
    )

    baseline_result = run_campaign(base)
    stressed_result = run_campaign(stressed)
    for baseline_run, stressed_run in zip(baseline_result.runs, stressed_result.runs, strict=True):
        assert baseline_run.arm_id == stressed_run.arm_id
        assert baseline_run.world.development_shocks == stressed_run.world.development_shocks
        assert (
            baseline_run.world.household_growth_shocks == stressed_run.world.household_growth_shocks
        )
        for year, baseline_shocks in baseline_run.world.firm_death_shocks.items():
            stressed_shocks = stressed_run.world.firm_death_shocks[year]
            common = set(baseline_shocks) & set(stressed_shocks)
            assert {key: baseline_shocks[key] for key in common} == {
                key: stressed_shocks[key] for key in common
            }
        assert baseline_run.world.firm_birth_shocks == stressed_run.world.firm_birth_shocks


def test_stress_matrix_export_is_bounded_and_replay_verifiable(tmp_path) -> None:
    base = scaled_integrated_campaign(world_count=1, end_year=2028)
    evidence_spec = StressEvidenceSpec(
        matrix=StressMatrixSpec(
            matrix_id="stress-test",
            base_campaign=base,
            scenarios=(
                StressScenario(scenario_id="baseline"),
                StressScenario(
                    scenario_id="transport-disruption",
                    transport_capacity_multiplier=0.8,
                ),
            ),
        ),
        metrics=(
            StressMetric.FINAL_ACCESSIBILITY,
            StressMetric.FINAL_EMPLOYMENT,
            StressMetric.CUMULATIVE_PUBLIC_SPEND,
        ),
    )
    target = tmp_path / "stress"

    exported = export_stress_matrix(
        evidence_spec,
        target,
        source_revision="04effa1a5c4c3426366ae910612af28d5d534735",
    )
    verified = verify_stress_export(target)

    assert exported == verified
    assert exported.scenario_shifts
    assert exported.policy_effects
    assert {path.name for path in target.iterdir()} == {
        "manifest.json",
        "provenance.json",
        "stress-config.json",
        "stress-evidence.json",
    }
