import pytest

from urban_field_dynamics.infrastructure import (
    BudgetExceededError,
    BudgetRationingMode,
    InfrastructureLedgerSpec,
    allocate_budget,
)


def ledger(mode: BudgetRationingMode) -> InfrastructureLedgerSpec:
    return InfrastructureLedgerSpec(
        annual_budget=100.0,
        cumulative_budget=150.0,
        capital_rationing=mode,
        redevelopment_public_cost_per_transition=2.0,
    )


def test_budget_allocation_respects_annual_and_cumulative_limits() -> None:
    allocation = allocate_budget(
        ledger(BudgetRationingMode.FAIL_CLOSED),
        requested=40.0,
        annual_spent=30.0,
        cumulative_spent=80.0,
        allow_capital_rationing=False,
    )

    assert allocation.funded == 40.0
    assert allocation.funding_fraction == 1.0
    assert allocation.annual_spent_after == 70.0
    assert allocation.cumulative_spent_after == 120.0


def test_budget_fails_closed_without_declared_rationing() -> None:
    with pytest.raises(BudgetExceededError, match="requested=80"):
        allocate_budget(
            ledger(BudgetRationingMode.FAIL_CLOSED),
            requested=80.0,
            annual_spent=30.0,
            cumulative_spent=80.0,
            allow_capital_rationing=True,
        )


def test_proportional_capital_rationing_uses_only_available_budget() -> None:
    allocation = allocate_budget(
        ledger(BudgetRationingMode.PROPORTIONAL),
        requested=80.0,
        annual_spent=30.0,
        cumulative_spent=80.0,
        allow_capital_rationing=True,
    )

    assert allocation.funded == 70.0
    assert allocation.unfunded == 10.0
    assert allocation.funding_fraction == pytest.approx(0.875)
    assert allocation.annual_spent_after == 100.0
    assert allocation.cumulative_spent_after == 150.0


def test_zero_request_has_full_fraction_without_spending() -> None:
    allocation = allocate_budget(
        ledger(BudgetRationingMode.PROPORTIONAL),
        requested=0.0,
        annual_spent=30.0,
        cumulative_spent=80.0,
        allow_capital_rationing=True,
    )

    assert allocation.funding_fraction == 1.0
    assert allocation.annual_spent_after == 30.0
    assert allocation.cumulative_spent_after == 80.0
