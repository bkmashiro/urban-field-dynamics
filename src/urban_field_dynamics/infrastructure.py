"""Fail-closed public budget and infrastructure-capacity ledgers."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonNegativeFloat = Annotated[float, Field(ge=0.0)]


class BudgetRationingMode(StrEnum):
    FAIL_CLOSED = "fail-closed"
    PROPORTIONAL = "proportional"


class BudgetExceededError(RuntimeError):
    """Raised when a declared annual or cumulative public budget is exceeded."""


class InfrastructureLedgerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    annual_budget: NonNegativeFloat
    cumulative_budget: NonNegativeFloat
    capital_rationing: BudgetRationingMode = BudgetRationingMode.FAIL_CLOSED
    redevelopment_public_cost_per_transition: NonNegativeFloat = 0.0


class BudgetAllocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    requested: NonNegativeFloat
    funded: NonNegativeFloat
    unfunded: NonNegativeFloat
    funding_fraction: Annotated[float, Field(ge=0.0, le=1.0)]
    annual_spent_after: NonNegativeFloat
    cumulative_spent_after: NonNegativeFloat


class InfrastructureAnnualTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    year: int
    capital_requested: NonNegativeFloat = 0.0
    capital_funded: NonNegativeFloat = 0.0
    capital_funding_fraction: Annotated[float, Field(ge=0.0, le=1.0)] = 1.0
    operating_cost: NonNegativeFloat = 0.0
    redevelopment_public_cost: NonNegativeFloat = 0.0
    annual_public_spend: NonNegativeFloat = 0.0
    cumulative_public_spend: NonNegativeFloat = 0.0
    annual_budget_remaining: NonNegativeFloat = 0.0
    cumulative_budget_remaining: NonNegativeFloat = 0.0
    transport_utilization_by_edge: dict[str, NonNegativeFloat] = Field(default_factory=dict)
    transport_overloaded_edges: tuple[str, ...] = ()
    service_utilization_by_location: dict[str, NonNegativeFloat] = Field(default_factory=dict)
    service_unmet_demand_by_location: dict[str, NonNegativeFloat] = Field(default_factory=dict)


def allocate_budget(
    spec: InfrastructureLedgerSpec,
    *,
    requested: float,
    annual_spent: float,
    cumulative_spent: float,
    allow_capital_rationing: bool,
) -> BudgetAllocation:
    """Allocate one declared cost against both ledgers, rationing only divisible capital."""

    if min(requested, annual_spent, cumulative_spent) < 0.0:
        raise ValueError("budget inputs must be non-negative")
    available = max(
        0.0,
        min(spec.annual_budget - annual_spent, spec.cumulative_budget - cumulative_spent),
    )
    if requested == 0.0:
        funded = 0.0
        fraction = 1.0
    elif available + 1e-12 >= requested:
        funded = requested
        fraction = 1.0
    elif allow_capital_rationing and spec.capital_rationing is BudgetRationingMode.PROPORTIONAL:
        funded = available
        fraction = funded / requested
    else:
        raise BudgetExceededError(
            "public budget exceeded: "
            f"requested={requested:g} available={available:g} "
            f"annual_spent={annual_spent:g} cumulative_spent={cumulative_spent:g}"
        )
    return BudgetAllocation(
        requested=requested,
        funded=funded,
        unfunded=requested - funded,
        funding_fraction=fraction,
        annual_spent_after=annual_spent + funded,
        cumulative_spent_after=cumulative_spent + funded,
    )
