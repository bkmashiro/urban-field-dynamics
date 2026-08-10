from urban_field_dynamics.analysis import (
    CampaignMetric,
    ConvergencePoint,
    PairedConvergenceDiagnostic,
    integrated_qualification_diagnostics,
)
from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.decision import (
    ArmObjectiveVector,
    LeverageStatus,
    ObjectiveDirection,
    ObjectiveSpec,
    campaign_decision_diagnostics,
    detect_threshold_crossings,
    pareto_front,
    summarize_tail_harm,
)
from urban_field_dynamics.equity import observe_campaign_equity
from urban_field_dynamics.integrated import integrated_smoke_campaign
from urban_field_dynamics.scaled_integrated import scaled_integrated_campaign


def test_pareto_front_preserves_tradeoffs_and_dominates_strictly_worse_arm() -> None:
    objectives = (
        ObjectiveSpec(objective_id="access", direction=ObjectiveDirection.MAXIMIZE),
        ObjectiveSpec(objective_id="rent", direction=ObjectiveDirection.MINIMIZE),
    )
    outcomes = (
        ArmObjectiveVector(arm_id="aa", values={"access": 1.0, "rent": 2.0}),
        ArmObjectiveVector(arm_id="bb", values={"access": 2.0, "rent": 3.0}),
        ArmObjectiveVector(arm_id="cc", values={"access": 0.5, "rent": 4.0}),
    )

    result = pareto_front(outcomes, objectives)

    assert result.nondominated_arm_ids == ("aa", "bb")
    assert result.dominated_by == {"cc": ("aa", "bb")}


def test_threshold_crossings_return_brackets_without_interpolation() -> None:
    result = detect_threshold_crossings(
        levels=(0.0, 0.5, 1.0, 1.5),
        responses=(0.1, 0.4, 0.7, 0.6),
        threshold=0.5,
    )

    assert len(result.crossings) == 1
    assert result.crossings[0].lower_level == 0.5
    assert result.crossings[0].upper_level == 1.0


def test_tail_harm_uses_welfare_direction() -> None:
    diagnostic = PairedConvergenceDiagnostic(
        baseline_arm="aa",
        comparator_arm="bb",
        metric=CampaignMetric.FINAL_RENT,
        higher_is_better=False,
        world_ids=(0, 1, 2),
        deltas=(-1.0, 0.5, 2.0),
        harmed_world_count=2,
        checkpoints=(
            ConvergencePoint(
                world_count=3,
                mean_delta=0.5,
                median_delta=0.5,
                q10_delta=-0.7,
                q90_delta=1.7,
                standard_error=0.1,
                ci95_lower=0.3,
                ci95_upper=0.7,
            ),
        ),
    )

    result = summarize_tail_harm(diagnostic)

    assert result.harmed_fraction == 2 / 3
    assert result.worst_harm == 2.0
    assert result.q90_harm > 0.0


def test_campaign_decision_bundle_keeps_pareto_and_tail_harm_separate() -> None:
    spec = integrated_smoke_campaign(world_count=2)
    result = run_campaign(spec)
    equity = observe_campaign_equity(spec, result)
    qualification = integrated_qualification_diagnostics(result, checkpoints=(2,))

    decision = campaign_decision_diagnostics(result, equity, qualification)

    assert decision.pareto.nondominated_arm_ids
    assert set(decision.pareto.nondominated_arm_ids).issubset({"p0", "p1", "p2", "p3"})
    assert set(decision.tail_harm) == set(qualification.comparisons)


def test_scaled_decision_reports_cost_leverage_and_group_tail_harm() -> None:
    spec = scaled_integrated_campaign(world_count=2, end_year=2028)
    result = run_campaign(spec)
    equity = observe_campaign_equity(spec, result)
    qualification = integrated_qualification_diagnostics(result, checkpoints=(2,))

    decision = campaign_decision_diagnostics(
        result,
        equity,
        qualification,
        spec=spec,
    )

    leverage = decision.leverage["p3:accessibility"]
    assert leverage.incremental_public_cost > 0.0
    assert leverage.denominator_provenance
    assert leverage.ratio_per_cost_unit is not None
    assert leverage.status is LeverageStatus.AVAILABLE
    assert decision.group_tail_harm
    assert all(item.world_count == 2 for item in decision.group_tail_harm.values())

    baseline_cost = result.summary.arms["p0"].mean_cumulative_public_spend
    p1 = result.summary.arms["p1"].model_copy(
        update={"mean_cumulative_public_spend": baseline_cost}
    )
    arms = {**result.summary.arms, "p1": p1}
    zero_cost_result = result.model_copy(
        update={"summary": result.summary.model_copy(update={"arms": arms})}
    )
    zero_cost = campaign_decision_diagnostics(
        zero_cost_result,
        equity,
        qualification,
    ).leverage["p1:accessibility"]
    assert zero_cost.status is LeverageStatus.NON_POSITIVE_INCREMENTAL_COST
    assert zero_cost.ratio_per_cost_unit is None
