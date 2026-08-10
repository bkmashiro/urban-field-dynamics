"""Policy-independent weighted household and firm cohort dynamics."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec
from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.event_tape import EventTapeSpec, generate_event_tape

NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")]


class HouseholdDynamicsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    mean_growth_rate: float = 0.0
    growth_volatility: NonNegativeFloat = 0.0
    minimum_population: PositiveFloat = 1e-6


class FirmBirthPrototype(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    prototype_id: Identifier
    annual_birth_probability: UnitInterval
    employees: PositiveFloat
    initial_unit_id: Identifier
    floor_demand_per_employee: PositiveFloat
    accessibility_weight: NonNegativeFloat
    agglomeration_weight: NonNegativeFloat
    rent_weight: NonNegativeFloat
    evidence_status: EvidenceStatus


class FirmDynamicsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    annual_death_probability: UnitInterval = 0.0
    mean_employee_growth_rate: float = 0.0
    employee_growth_volatility: NonNegativeFloat = 0.0
    minimum_employees: PositiveFloat = 1e-6
    birth_prototypes: tuple[FirmBirthPrototype, ...] = ()

    @model_validator(mode="after")
    def unique_prototypes(self) -> FirmDynamicsSpec:
        ids = [prototype.prototype_id for prototype in self.birth_prototypes]
        if len(ids) != len(set(ids)):
            raise ValueError("firm birth prototype IDs must be unique")
        return self


class HouseholdDynamicsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    cohorts: tuple[HouseholdCohortSpec, ...]
    growth_shocks: dict[str, float]


class FirmDynamicsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    cohorts: tuple[FirmCohortSpec, ...]
    births: tuple[str, ...]
    deaths: tuple[str, ...]
    death_shocks: dict[str, float]
    expansion_shocks: dict[str, float]
    birth_shocks: dict[str, float]


def _uniforms(
    ids: tuple[str, ...],
    *,
    root_seed: int,
    world_id: int,
    year: int,
    mechanism: str,
) -> dict[str, float]:
    if not ids:
        return {}
    return {
        item_id: float(
            generate_event_tape(
                EventTapeSpec(
                    root_seed=root_seed,
                    world_id=world_id,
                    year=year,
                    mechanism=mechanism,
                    entity_id=item_id,
                ),
                shape=(1,),
            )[0]
        )
        for item_id in ids
    }


def evolve_households(
    cohorts: tuple[HouseholdCohortSpec, ...],
    spec: HouseholdDynamicsSpec,
    *,
    root_seed: int,
    world_id: int,
    year: int,
) -> HouseholdDynamicsResult:
    ordered = tuple(sorted(cohorts, key=lambda cohort: cohort.cohort_id))
    ids = tuple(cohort.cohort_id for cohort in ordered)
    uniforms = _uniforms(
        ids,
        root_seed=root_seed,
        world_id=world_id,
        year=year,
        mechanism="household-growth",
    )
    shocks = {
        cohort_id: (2.0 * uniforms[cohort_id] - 1.0) * spec.growth_volatility for cohort_id in ids
    }
    evolved = tuple(
        cohort.model_copy(
            update={
                "population": max(
                    spec.minimum_population,
                    cohort.population * (1.0 + spec.mean_growth_rate + shocks[cohort.cohort_id]),
                )
            }
        )
        for cohort in ordered
    )
    return HouseholdDynamicsResult(cohorts=evolved, growth_shocks=shocks)


def evolve_firms(
    cohorts: tuple[FirmCohortSpec, ...],
    spec: FirmDynamicsSpec,
    *,
    root_seed: int,
    world_id: int,
    year: int,
) -> FirmDynamicsResult:
    ordered = tuple(sorted(cohorts, key=lambda cohort: cohort.cohort_id))
    ids = tuple(cohort.cohort_id for cohort in ordered)
    death_shocks = _uniforms(
        ids,
        root_seed=root_seed,
        world_id=world_id,
        year=year,
        mechanism="firm-death",
    )
    expansion_uniforms = _uniforms(
        ids,
        root_seed=root_seed,
        world_id=world_id,
        year=year,
        mechanism="firm-expansion",
    )
    expansion_shocks = {
        cohort_id: (2.0 * expansion_uniforms[cohort_id] - 1.0) * spec.employee_growth_volatility
        for cohort_id in ids
    }
    survivors: list[FirmCohortSpec] = []
    deaths: list[str] = []
    for cohort in ordered:
        if death_shocks[cohort.cohort_id] < spec.annual_death_probability:
            deaths.append(cohort.cohort_id)
            continue
        survivors.append(
            cohort.model_copy(
                update={
                    "employees": max(
                        spec.minimum_employees,
                        cohort.employees
                        * (
                            1.0
                            + spec.mean_employee_growth_rate
                            + expansion_shocks[cohort.cohort_id]
                        ),
                    )
                }
            )
        )

    prototypes = tuple(sorted(spec.birth_prototypes, key=lambda item: item.prototype_id))
    prototype_ids = tuple(item.prototype_id for item in prototypes)
    birth_shocks = _uniforms(
        prototype_ids,
        root_seed=root_seed,
        world_id=world_id,
        year=year,
        mechanism="firm-birth",
    )
    existing_ids = {cohort.cohort_id for cohort in survivors}
    births: list[str] = []
    for prototype in prototypes:
        if birth_shocks[prototype.prototype_id] >= prototype.annual_birth_probability:
            continue
        cohort_id = f"{prototype.prototype_id}-{year}"
        if cohort_id in existing_ids:
            raise ValueError(f"firm birth cohort ID collision: {cohort_id}")
        survivors.append(
            FirmCohortSpec(
                cohort_id=cohort_id,
                employees=prototype.employees,
                initial_unit_id=prototype.initial_unit_id,
                floor_demand_per_employee=prototype.floor_demand_per_employee,
                accessibility_weight=prototype.accessibility_weight,
                agglomeration_weight=prototype.agglomeration_weight,
                rent_weight=prototype.rent_weight,
                evidence_status=prototype.evidence_status,
            )
        )
        existing_ids.add(cohort_id)
        births.append(cohort_id)

    return FirmDynamicsResult(
        cohorts=tuple(sorted(survivors, key=lambda cohort: cohort.cohort_id)),
        births=tuple(births),
        deaths=tuple(deaths),
        death_shocks=death_shocks,
        expansion_shocks=expansion_shocks,
        birth_shocks=birth_shocks,
    )
