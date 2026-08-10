"""Weighted household and firm cohort location-choice reference model."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.event_tape import EventTapeSpec, generate_event_tape

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")]


class HouseholdCohortSpec(BaseModel):
    """One weighted household cohort; never an asserted real person record."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    cohort_id: Identifier
    population: PositiveFloat
    initial_unit_id: Identifier
    income: PositiveFloat
    housing_demand_per_person: PositiveFloat
    accessibility_weight: NonNegativeFloat
    jobs_weight: NonNegativeFloat
    environment_weight: NonNegativeFloat
    rent_burden_weight: NonNegativeFloat
    evidence_status: EvidenceStatus
    service_weight: NonNegativeFloat = 0.0

    @property
    def housing_demand(self) -> float:
        return self.population * self.housing_demand_per_person


class FirmCohortSpec(BaseModel):
    """One weighted firm cohort; never an asserted real establishment record."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    cohort_id: Identifier
    employees: PositiveFloat
    initial_unit_id: Identifier
    floor_demand_per_employee: PositiveFloat
    accessibility_weight: NonNegativeFloat
    agglomeration_weight: NonNegativeFloat
    rent_weight: NonNegativeFloat
    evidence_status: EvidenceStatus

    @property
    def floor_demand(self) -> float:
        return self.employees * self.floor_demand_per_employee


class LocationState(BaseModel):
    """Auditable annual location state consumed by cohort choice functions."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    unit_id: Identifier
    accessibility: UnitInterval
    rent: NonNegativeFloat
    jobs: NonNegativeFloat
    households: NonNegativeFloat
    housing_capacity: NonNegativeFloat
    employment_capacity: NonNegativeFloat
    environment_quality: UnitInterval
    evidence_status: EvidenceStatus
    service_quality: UnitInterval = 0.5
    service_capacity: NonNegativeFloat | None = None


class AgentAllocationResult(BaseModel):
    """Stable cohort assignments, consumed shocks, and resulting occupancy."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    assignments: dict[str, str]
    taste_shocks: dict[str, dict[str, float]]
    locations: tuple[LocationState, ...]


def household_utility(
    cohort: HouseholdCohortSpec,
    location: LocationState,
    *,
    taste_shock: float,
) -> float:
    """Evaluate bounded amenities and explicit rent burden for one cohort."""

    job_access = location.jobs / max(location.employment_capacity, 1.0)
    rent_burden = location.rent / cohort.income
    service_access = location.service_quality
    if location.service_capacity is not None:
        demand = location.households + cohort.housing_demand
        service_access *= min(1.0, location.service_capacity / max(demand, 1.0))
    return (
        cohort.accessibility_weight * location.accessibility
        + cohort.jobs_weight * job_access
        + cohort.environment_weight * location.environment_quality
        + cohort.service_weight * service_access
        - cohort.rent_burden_weight * rent_burden
        + taste_shock
    )


def firm_utility(
    cohort: FirmCohortSpec,
    location: LocationState,
    *,
    taste_shock: float,
) -> float:
    """Evaluate accessibility, agglomeration and occupancy-cost trade-offs."""

    agglomeration = location.jobs / max(location.employment_capacity, 1.0)
    return (
        cohort.accessibility_weight * location.accessibility
        + cohort.agglomeration_weight * agglomeration
        - cohort.rent_weight * location.rent / 100.0
        + taste_shock
    )


def _choose_location(
    locations: Sequence[LocationState],
    taste_shocks: Mapping[str, float],
    *,
    feasible: Callable[[LocationState], bool],
    utility: Callable[[LocationState, float], float],
) -> str:
    location_ids = [location.unit_id for location in locations]
    if len(location_ids) != len(set(location_ids)):
        raise ValueError("location unit_id values must be unique")
    if set(taste_shocks) != set(location_ids):
        raise ValueError("taste_shocks must match location IDs")

    candidates = [location for location in locations if feasible(location)]
    if not candidates:
        raise ValueError("no location has sufficient remaining capacity")
    return max(
        candidates,
        key=lambda location: (utility(location, taste_shocks[location.unit_id]), location.unit_id),
    ).unit_id


def choose_household_location(
    cohort: HouseholdCohortSpec,
    locations: Sequence[LocationState],
    *,
    taste_shocks: Mapping[str, float],
) -> str:
    """Choose the highest-utility location with enough housing capacity."""

    return _choose_location(
        locations,
        taste_shocks,
        feasible=lambda location: (
            location.housing_capacity - location.households >= cohort.housing_demand
        ),
        utility=lambda location, shock: household_utility(
            cohort,
            location,
            taste_shock=shock,
        ),
    )


def choose_firm_location(
    cohort: FirmCohortSpec,
    locations: Sequence[LocationState],
    *,
    taste_shocks: Mapping[str, float],
) -> str:
    """Choose the highest-utility location with enough employment capacity."""

    return _choose_location(
        locations,
        taste_shocks,
        feasible=lambda location: (
            location.employment_capacity - location.jobs >= cohort.floor_demand
        ),
        utility=lambda location, shock: firm_utility(
            cohort,
            location,
            taste_shock=shock,
        ),
    )


def _taste_shocks(
    *,
    cohort_ids: tuple[str, ...],
    location_ids: tuple[str, ...],
    root_seed: int,
    world_id: int,
    year: int,
    mechanism: str,
    scale: float,
) -> dict[str, dict[str, float]]:
    if scale < 0.0:
        raise ValueError("taste_shock_scale must be non-negative")
    tape = generate_event_tape(
        EventTapeSpec(
            root_seed=root_seed,
            world_id=world_id,
            year=year,
            mechanism=mechanism,
        ),
        shape=(len(cohort_ids), len(location_ids)),
    )
    return {
        cohort_id: {
            location_id: float((tape[row, column] - 0.5) * 2.0 * scale)
            for column, location_id in enumerate(location_ids)
        }
        for row, cohort_id in enumerate(cohort_ids)
    }


def allocate_households(
    cohorts: Sequence[HouseholdCohortSpec],
    locations: Sequence[LocationState],
    *,
    root_seed: int,
    world_id: int,
    year: int,
    taste_shock_scale: float,
) -> AgentAllocationResult:
    """Allocate weighted household cohorts in stable order against remaining capacity."""

    ordered_cohorts = tuple(sorted(cohorts, key=lambda cohort: cohort.cohort_id))
    ordered_locations = tuple(sorted(locations, key=lambda location: location.unit_id))
    cohort_ids = tuple(cohort.cohort_id for cohort in ordered_cohorts)
    location_ids = tuple(location.unit_id for location in ordered_locations)
    shocks = _taste_shocks(
        cohort_ids=cohort_ids,
        location_ids=location_ids,
        root_seed=root_seed,
        world_id=world_id,
        year=year,
        mechanism="household-location-taste",
        scale=taste_shock_scale,
    )
    current = {location.unit_id: location for location in ordered_locations}
    assignments: dict[str, str] = {}
    for cohort in ordered_cohorts:
        chosen = choose_household_location(
            cohort,
            tuple(current.values()),
            taste_shocks=shocks[cohort.cohort_id],
        )
        assignments[cohort.cohort_id] = chosen
        location = current[chosen]
        current[chosen] = location.model_copy(
            update={"households": location.households + cohort.housing_demand}
        )
    return AgentAllocationResult(
        assignments=assignments,
        taste_shocks=shocks,
        locations=tuple(current[unit_id] for unit_id in location_ids),
    )


def allocate_firms(
    cohorts: Sequence[FirmCohortSpec],
    locations: Sequence[LocationState],
    *,
    root_seed: int,
    world_id: int,
    year: int,
    taste_shock_scale: float,
) -> AgentAllocationResult:
    """Allocate weighted firm cohorts in stable order against remaining capacity."""

    ordered_cohorts = tuple(sorted(cohorts, key=lambda cohort: cohort.cohort_id))
    ordered_locations = tuple(sorted(locations, key=lambda location: location.unit_id))
    cohort_ids = tuple(cohort.cohort_id for cohort in ordered_cohorts)
    location_ids = tuple(location.unit_id for location in ordered_locations)
    shocks = _taste_shocks(
        cohort_ids=cohort_ids,
        location_ids=location_ids,
        root_seed=root_seed,
        world_id=world_id,
        year=year,
        mechanism="firm-location-taste",
        scale=taste_shock_scale,
    )
    current = {location.unit_id: location for location in ordered_locations}
    assignments: dict[str, str] = {}
    for cohort in ordered_cohorts:
        chosen = choose_firm_location(
            cohort,
            tuple(current.values()),
            taste_shocks=shocks[cohort.cohort_id],
        )
        assignments[cohort.cohort_id] = chosen
        location = current[chosen]
        current[chosen] = location.model_copy(update={"jobs": location.jobs + cohort.employees})
    return AgentAllocationResult(
        assignments=assignments,
        taste_shocks=shocks,
        locations=tuple(current[unit_id] for unit_id in location_ids),
    )
