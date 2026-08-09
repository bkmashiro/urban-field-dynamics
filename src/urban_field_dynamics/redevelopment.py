"""Redevelopment decision with explicit site value and transition inertia."""

from dataclasses import dataclass

from urban_field_dynamics.contracts import PinKind, SpatialUnitSpec


@dataclass(frozen=True, slots=True)
class RedevelopmentDecision:
    """Auditable result of evaluating one redevelopment candidate."""

    should_redevelop: bool
    candidate_npv: float
    keep_npv: float
    effective_transition_cost: float | None
    reason: str


def evaluate_redevelopment(
    unit: SpatialUnitSpec,
    *,
    candidate_shock: float = 0.0,
    transition_inertia_enabled: bool = True,
) -> RedevelopmentDecision:
    """Evaluate a candidate without weakening hard legal or physical pins."""

    candidate_npv = (
        unit.candidate_base_npv
        + unit.accessibility * unit.accessibility_value_factor
        + candidate_shock
    )

    if unit.pin_kind is PinKind.HARD:
        return RedevelopmentDecision(
            should_redevelop=False,
            candidate_npv=candidate_npv,
            keep_npv=unit.keep_npv,
            effective_transition_cost=None,
            reason="hard_pin",
        )

    if unit.pin_kind is PinKind.FREE or not transition_inertia_enabled:
        effective_transition_cost = 0.0
    else:
        remaining_asset_fraction = max(
            0.0,
            1.0 - unit.asset_age_years / unit.design_life_years,
        )
        effective_transition_cost = unit.transition_cost * remaining_asset_fraction

    should_redevelop = candidate_npv > unit.keep_npv + effective_transition_cost
    return RedevelopmentDecision(
        should_redevelop=should_redevelop,
        candidate_npv=candidate_npv,
        keep_npv=unit.keep_npv,
        effective_transition_cost=effective_transition_cost,
        reason="eligible" if should_redevelop else "insufficient_value_gap",
    )
