"""Deterministic weighted-cohort labor matching and wage-pressure feedback."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveUnitInterval = Annotated[float, Field(gt=0.0, le=1.0)]


class LaborMatchingSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    max_commute_minutes: NonNegativeFloat
    commute_cost_per_minute: NonNegativeFloat
    wage_adjustment_rate: UnitInterval
    unemployment_wage_relief: UnitInterval = 0.5
    vacancy_retention_rate: PositiveUnitInterval = 1.0


class LaborMatchingResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    flows: dict[str, float]
    household_employed: dict[str, float]
    household_unemployed: dict[str, float]
    firm_filled: dict[str, float]
    firm_vacancies: dict[str, float]
    household_mean_wage: dict[str, float]
    household_mean_commute_minutes: dict[str, float]
    adjusted_firm_wages: dict[str, float]
    adjusted_firm_employees: dict[str, float]
    labor_force: float
    labor_demand: float
    unemployment_rate: float
    vacancy_rate: float
    mean_commute_minutes: float


def _compatible(household: HouseholdCohortSpec, firm: FirmCohortSpec) -> bool:
    return (
        household.skill_group == firm.skill_requirement
        or household.skill_group == "general"
        or firm.skill_requirement == "general"
    )


def match_labor(
    households: tuple[HouseholdCohortSpec, ...],
    firms: tuple[FirmCohortSpec, ...],
    *,
    household_locations: dict[str, str],
    firm_locations: dict[str, str],
    commute_costs: dict[str, float],
    spec: LaborMatchingSpec,
) -> LaborMatchingResult:
    """Match divisible cohort labor in stable net-wage order without hidden truncation."""

    household_ids = {cohort.cohort_id for cohort in households}
    firm_ids = {cohort.cohort_id for cohort in firms}
    if set(household_locations) != household_ids:
        raise ValueError("household_locations must match household cohort IDs")
    if set(firm_locations) != firm_ids:
        raise ValueError("firm_locations must match firm cohort IDs")
    if any(cost < 0.0 for cost in commute_costs.values()):
        raise ValueError("commute costs must be non-negative")

    supply = {
        cohort.cohort_id: cohort.population * cohort.labor_force_share for cohort in households
    }
    demand = {cohort.cohort_id: cohort.employees * cohort.labor_demand_share for cohort in firms}
    remaining_supply = dict(supply)
    remaining_demand = dict(demand)
    candidates: list[tuple[float, str, str, float]] = []
    for household in households:
        for firm in firms:
            if not _compatible(household, firm):
                continue
            if firm.offered_wage < household.reservation_wage:
                continue
            origin = household_locations[household.cohort_id]
            destination = firm_locations[firm.cohort_id]
            key = f"{origin}->{destination}"
            commute = 0.0 if origin == destination else commute_costs.get(key)
            if commute is None or commute > spec.max_commute_minutes:
                continue
            net_wage = firm.offered_wage - spec.commute_cost_per_minute * commute
            candidates.append((-net_wage, household.cohort_id, firm.cohort_id, commute))
    candidates.sort()

    flows: dict[str, float] = {}
    commute_total = 0.0
    household_commute_totals = dict.fromkeys(supply, 0.0)
    wage_totals = dict.fromkeys(supply, 0.0)
    firm_by_id = {cohort.cohort_id: cohort for cohort in firms}
    for _negative_net_wage, household_id, firm_id, commute in candidates:
        flow = min(remaining_supply[household_id], remaining_demand[firm_id])
        if flow <= 0.0:
            continue
        flows[f"{household_id}->{firm_id}"] = flow
        remaining_supply[household_id] -= flow
        remaining_demand[firm_id] -= flow
        commute_total += flow * commute
        household_commute_totals[household_id] += flow * commute
        wage_totals[household_id] += flow * firm_by_id[firm_id].offered_wage

    employed = {
        cohort_id: supply[cohort_id] - remaining
        for cohort_id, remaining in remaining_supply.items()
    }
    filled = {
        cohort_id: demand[cohort_id] - remaining
        for cohort_id, remaining in remaining_demand.items()
    }
    labor_force = sum(supply.values())
    labor_demand = sum(demand.values())
    total_employed = sum(employed.values())
    unemployment_rate = sum(remaining_supply.values()) / labor_force if labor_force else 0.0
    vacancy_rate = sum(remaining_demand.values()) / labor_demand if labor_demand else 0.0
    adjusted_wages = {}
    for firm in firms:
        firm_demand = demand[firm.cohort_id]
        firm_vacancy_rate = remaining_demand[firm.cohort_id] / firm_demand if firm_demand else 0.0
        pressure = firm_vacancy_rate - spec.unemployment_wage_relief * unemployment_rate
        multiplier = max(0.1, 1.0 + spec.wage_adjustment_rate * pressure)
        adjusted_wages[firm.cohort_id] = firm.offered_wage * multiplier
    adjusted_employees = {
        cohort.cohort_id: (cohort.employees - demand[cohort.cohort_id])
        + filled[cohort.cohort_id]
        + spec.vacancy_retention_rate * remaining_demand[cohort.cohort_id]
        for cohort in firms
    }

    return LaborMatchingResult(
        flows=flows,
        household_employed=employed,
        household_unemployed=remaining_supply,
        firm_filled=filled,
        firm_vacancies=remaining_demand,
        household_mean_wage={
            cohort_id: wage_totals[cohort_id] / employed[cohort_id] if employed[cohort_id] else 0.0
            for cohort_id in supply
        },
        household_mean_commute_minutes={
            cohort_id: household_commute_totals[cohort_id] / employed[cohort_id]
            if employed[cohort_id]
            else 0.0
            for cohort_id in supply
        },
        adjusted_firm_wages=adjusted_wages,
        adjusted_firm_employees=adjusted_employees,
        labor_force=labor_force,
        labor_demand=labor_demand,
        unemployment_rate=unemployment_rate,
        vacancy_rate=vacancy_rate,
        mean_commute_minutes=commute_total / total_employed if total_employed else 0.0,
    )
