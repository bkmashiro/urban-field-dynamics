from urban_field_dynamics.analysis import (
    CampaignMetric,
    ConvergencePoint,
    PairedConvergenceDiagnostic,
    integrated_qualification_diagnostics,
)
from urban_field_dynamics.campaign import run_campaign
from urban_field_dynamics.decision import (
    ArmObjectiveVector,
    ObjectiveDirection,
    ObjectiveSpec,
    campaign_decision_diagnostics,
    detect_threshold_crossings,
    pareto_front,
    summarize_tail_harm,
)
from urban_field_dynamics.equity import observe_campaign_equity
from urban_field_dynamics.integrated import integrated_smoke_campaign


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
