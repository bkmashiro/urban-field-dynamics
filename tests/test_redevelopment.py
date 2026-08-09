import pytest

from urban_field_dynamics.contracts import (
    EvidenceStatus,
    LandUse,
    PinKind,
    SpatialUnitSpec,
)
from urban_field_dynamics.redevelopment import evaluate_redevelopment


def make_unit(
    *,
    pin_kind: PinKind = PinKind.SOFT,
    asset_age_years: int = 10,
    transition_cost: float = 50.0,
) -> SpatialUnitSpec:
    return SpatialUnitSpec(
        unit_id="u-001",
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESEARCH,
        pin_kind=pin_kind,
        asset_age_years=asset_age_years,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=130.0,
        transition_cost=transition_cost,
        accessibility=0.5,
        accessibility_value_factor=20.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def test_hard_pin_never_redevelops() -> None:
    decision = evaluate_redevelopment(
        make_unit(pin_kind=PinKind.HARD, transition_cost=0.0),
        candidate_shock=10_000.0,
    )

    assert decision.should_redevelop is False
    assert decision.effective_transition_cost is None
    assert decision.reason == "hard_pin"


def test_young_soft_pinned_asset_is_blocked_by_remaining_value() -> None:
    decision = evaluate_redevelopment(make_unit(asset_age_years=10))

    assert decision.candidate_npv == 140.0
    assert decision.effective_transition_cost == 40.0
    assert decision.should_redevelop is False


def test_older_asset_enters_redevelopment_window() -> None:
    decision = evaluate_redevelopment(make_unit(asset_age_years=40))

    assert decision.effective_transition_cost == pytest.approx(10.0)
    assert decision.should_redevelop is True


def test_no_inertia_ablation_removes_soft_transition_cost() -> None:
    decision = evaluate_redevelopment(
        make_unit(asset_age_years=10),
        transition_inertia_enabled=False,
    )

    assert decision.effective_transition_cost == 0.0
    assert decision.should_redevelop is True


def test_free_unit_has_no_transition_inertia() -> None:
    decision = evaluate_redevelopment(make_unit(pin_kind=PinKind.FREE))

    assert decision.effective_transition_cost == 0.0
    assert decision.should_redevelop is True
