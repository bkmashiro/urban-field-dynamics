"""Minimal auditable world runner for the first vertical slice."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from urban_field_dynamics.agents import (
    FirmCohortSpec,
    HouseholdCohortSpec,
    LocationState,
    allocate_firms,
    allocate_households,
)
from urban_field_dynamics.contracts import LandUse, SpatialUnitSpec
from urban_field_dynamics.dynamics import (
    FirmDynamicsSpec,
    HouseholdDynamicsSpec,
    evolve_firms,
    evolve_households,
)
from urban_field_dynamics.environment import (
    EnvironmentalUnitSpec,
    ExposureResult,
    ExposureWeights,
    SeasonalEnvironmentSpec,
    evaluate_exposure,
)
from urban_field_dynamics.event_tape import EventTapeSpec, generate_event_tape
from urban_field_dynamics.labor import LaborMatchingResult, LaborMatchingSpec, match_labor
from urban_field_dynamics.market import MarketClearingSpec, clear_market
from urban_field_dynamics.redevelopment import evaluate_redevelopment
from urban_field_dynamics.schedule import AnnualPhase, ScheduleConfig, Season, iter_schedule
from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentResult,
    TransportAssignmentSpec,
    TransportEdgeSpec,
    assign_transport,
    generalized_cost_skim,
    opportunity_accessibility,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
AccessibilityDelta = Annotated[float, Field(ge=-1.0, le=1.0)]


class MechanismSwitches(BaseModel):
    """Independent mechanism toggles used by matched-seed ablations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agglomeration_enabled: bool = True
    transport_attraction_enabled: bool = True
    seasonality_enabled: bool = True
    environmental_exposure_enabled: bool = True
    public_coordination_enabled: bool = True
    service_provision_enabled: bool = True
    cohort_dynamics_enabled: bool = True
    labor_matching_enabled: bool = True


class TriggerMetric(StrEnum):
    MEAN_RENT = "mean_rent"
    MEAN_ACCESSIBILITY = "mean_accessibility"
    MEAN_ENVIRONMENT_QUALITY = "mean_environment_quality"
    MAX_HOUSING_OCCUPANCY = "max_housing_occupancy"
    MAX_EMPLOYMENT_OCCUPANCY = "max_employment_occupancy"


class TriggerOperator(StrEnum):
    GE = "ge"
    LE = "le"


class TriggerMode(StrEnum):
    ANY = "any"
    ALL = "all"


class PolicyTriggerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    metric: TriggerMetric
    operator: TriggerOperator
    threshold: NonNegativeFloat


class PolicySpec(BaseModel):
    """One public intervention applied at an explicit replanning year."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    policy_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")]
    intervention_year: NonNegativeInt
    accessibility_delta: AccessibilityDelta = 0.0
    accessibility_delta_by_unit: dict[str, AccessibilityDelta] = Field(default_factory=dict)
    transport_capacity_multiplier_by_edge: dict[str, PositiveFloat] = Field(default_factory=dict)
    transport_time_multiplier_by_edge: dict[str, PositiveFloat] = Field(default_factory=dict)
    green_fraction_delta_by_unit: dict[str, AccessibilityDelta] = Field(default_factory=dict)
    service_quality_delta_by_location: dict[str, AccessibilityDelta] = Field(default_factory=dict)
    service_capacity_multiplier_by_location: dict[str, PositiveFloat] = Field(default_factory=dict)
    activation_triggers: tuple[PolicyTriggerSpec, ...] = ()
    trigger_mode: TriggerMode = TriggerMode.ALL


class WorldRunConfig(BaseModel):
    """Complete input identity for a small deterministic world run."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    root_seed: NonNegativeInt
    world_id: NonNegativeInt
    schedule: ScheduleConfig
    units: Annotated[tuple[SpatialUnitSpec, ...], Field(min_length=1)]
    policy: PolicySpec
    transition_inertia_enabled: bool = True
    development_shock_scale: NonNegativeFloat = 0.0
    locations: tuple[LocationState, ...] = ()
    location_members: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    households: tuple[HouseholdCohortSpec, ...] = ()
    firms: tuple[FirmCohortSpec, ...] = ()
    household_dynamics: HouseholdDynamicsSpec | None = None
    firm_dynamics: FirmDynamicsSpec | None = None
    labor_matching: LaborMatchingSpec | None = None
    market: MarketClearingSpec | None = None
    agent_taste_shock_scale: NonNegativeFloat = 0.0
    transport_edges: tuple[TransportEdgeSpec, ...] = ()
    transport_od: tuple[ODPair, ...] = ()
    transport_assignment: TransportAssignmentSpec | None = None
    accessibility_decay: NonNegativeFloat = 0.0
    environmental_units: tuple[EnvironmentalUnitSpec, ...] = ()
    seasonal_environment: tuple[SeasonalEnvironmentSpec, ...] = ()
    exposure_weights: ExposureWeights | None = None
    mechanisms: MechanismSwitches = MechanismSwitches()

    @model_validator(mode="after")
    def validate_policy_and_units(self) -> WorldRunConfig:
        if self.policy.intervention_year not in self.schedule.replan_years:
            raise ValueError("policy intervention_year must be a declared replan_year")
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("unit_id values must be unique")
        if not set(self.policy.accessibility_delta_by_unit).issubset(unit_ids):
            raise ValueError("policy accessibility unit IDs must exist in units")
        if self.locations or self.households or self.firms:
            location_ids = [location.unit_id for location in self.locations]
            if len(location_ids) != len(set(location_ids)):
                raise ValueError("location unit_id values must be unique")
            if self.location_members:
                if set(self.location_members) != set(location_ids):
                    raise ValueError("location_members keys must match location IDs")
                members = [
                    member_id
                    for location_id in location_ids
                    for member_id in self.location_members[location_id]
                ]
                if len(members) != len(set(members)) or set(members) != set(unit_ids):
                    raise ValueError("location_members must cover every spatial unit exactly once")
            elif set(location_ids) != set(unit_ids):
                raise ValueError("locations must match spatial unit IDs without location_members")
            if (self.households or self.firms) and self.market is None:
                raise ValueError("market is required when agent state is configured")
            known_locations = set(location_ids)
            if not set(self.policy.service_quality_delta_by_location).issubset(known_locations):
                raise ValueError("policy service-quality IDs must exist in locations")
            if not set(self.policy.service_capacity_multiplier_by_location).issubset(
                known_locations
            ):
                raise ValueError("policy service-capacity IDs must exist in locations")
            locations_by_id = {location.unit_id: location for location in self.locations}
            if any(
                locations_by_id[location_id].service_capacity is None
                for location_id in self.policy.service_capacity_multiplier_by_location
            ):
                raise ValueError("service-capacity policy requires explicit baseline capacity")
            cohort_ids = [cohort.cohort_id for cohort in (*self.households, *self.firms)]
            if len(cohort_ids) != len(set(cohort_ids)):
                raise ValueError("household and firm cohort IDs must be unique")
            if any(
                cohort.initial_unit_id not in known_locations
                for cohort in (*self.households, *self.firms)
            ):
                raise ValueError("cohort initial_unit_id must exist in locations")
            if self.firm_dynamics is not None and any(
                prototype.initial_unit_id not in known_locations
                for prototype in self.firm_dynamics.birth_prototypes
            ):
                raise ValueError("firm birth prototype initial_unit_id must exist in locations")
            if self.labor_matching is not None and not (self.households and self.firms):
                raise ValueError("labor matching requires household and firm cohorts")
        elif self.household_dynamics is not None or self.firm_dynamics is not None:
            raise ValueError("agent dynamics require configured locations and cohorts")

        transport_values = (
            bool(self.transport_edges),
            bool(self.transport_od),
            self.transport_assignment is not None,
        )
        if any(transport_values) and not all(transport_values):
            raise ValueError("transport edges, OD, and assignment must be configured together")
        edge_ids = [edge.edge_id for edge in self.transport_edges]
        if len(edge_ids) != len(set(edge_ids)):
            raise ValueError("transport edge IDs must be unique")
        if not set(self.policy.transport_capacity_multiplier_by_edge).issubset(edge_ids):
            raise ValueError("policy transport edge IDs must exist in transport_edges")
        if not set(self.policy.transport_time_multiplier_by_edge).issubset(edge_ids):
            raise ValueError("policy transport-time edge IDs must exist in transport_edges")

        environment_values = (
            bool(self.environmental_units),
            bool(self.seasonal_environment),
            self.exposure_weights is not None,
        )
        if any(environment_values) and not all(environment_values):
            raise ValueError("environment units, seasons, and weights must be configured together")
        if self.environmental_units:
            environmental_ids = [unit.unit_id for unit in self.environmental_units]
            expected_environment_ids = (
                {location.unit_id for location in self.locations}
                if self.locations
                else set(unit_ids)
            )
            if set(environmental_ids) != expected_environment_ids:
                raise ValueError("environmental units must match configured location IDs")
            if len(environmental_ids) != len(set(environmental_ids)):
                raise ValueError("environmental unit IDs must be unique")
            if not set(self.policy.green_fraction_delta_by_unit).issubset(environmental_ids):
                raise ValueError("policy green-fraction IDs must exist in environmental units")
            seasons = [profile.season for profile in self.seasonal_environment]
            if len(seasons) != len(set(seasons)) or set(seasons) != set(Season):
                raise ValueError("seasonal environment must define each season exactly once")
            referenced_edges = {
                edge_id for unit in self.environmental_units for edge_id in unit.transport_edge_ids
            }
            if not referenced_edges.issubset(edge_ids):
                raise ValueError("environment transport edge IDs must exist in transport_edges")
        elif self.policy.green_fraction_delta_by_unit:
            raise ValueError("green-fraction policy requires environmental units")
        if (
            self.policy.service_quality_delta_by_location
            or self.policy.service_capacity_multiplier_by_location
        ) and not self.locations:
            raise ValueError("service-quality policy requires locations")
        return self


class WorldResult(BaseModel):
    """Small, JSON-safe trace and terminal state for one world-policy run."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    root_seed: int
    world_id: int
    policy_id: str
    policy_activation_year: int | None = None
    transition_inertia_enabled: bool
    redevelopment_years: dict[str, int | None]
    final_accessibility: dict[str, float]
    final_uses: dict[str, LandUse]
    development_shocks: dict[int, dict[str, float]]
    household_locations: dict[str, str] = Field(default_factory=dict)
    firm_locations: dict[str, str] = Field(default_factory=dict)
    final_households: dict[str, float] = Field(default_factory=dict)
    final_jobs: dict[str, float] = Field(default_factory=dict)
    final_rents: dict[str, float] = Field(default_factory=dict)
    household_taste_shocks: dict[int, dict[str, dict[str, float]]] = Field(default_factory=dict)
    firm_taste_shocks: dict[int, dict[str, dict[str, float]]] = Field(default_factory=dict)
    final_household_populations: dict[str, float] = Field(default_factory=dict)
    final_firm_employees: dict[str, float] = Field(default_factory=dict)
    household_growth_shocks: dict[int, dict[str, float]] = Field(default_factory=dict)
    firm_death_shocks: dict[int, dict[str, float]] = Field(default_factory=dict)
    firm_expansion_shocks: dict[int, dict[str, float]] = Field(default_factory=dict)
    firm_birth_shocks: dict[int, dict[str, float]] = Field(default_factory=dict)
    firm_births: dict[int, tuple[str, ...]] = Field(default_factory=dict)
    firm_deaths: dict[int, tuple[str, ...]] = Field(default_factory=dict)
    labor_traces: dict[int, LaborMatchingResult] = Field(default_factory=dict)
    final_firm_wages: dict[str, float] = Field(default_factory=dict)
    transport_traces: dict[int, dict[str, TransportAssignmentResult]] = Field(default_factory=dict)
    environment_traces: dict[int, dict[str, dict[str, ExposureResult]]] = Field(
        default_factory=dict
    )
    final_environment_quality: dict[str, float] = Field(default_factory=dict)
    final_service_quality: dict[str, float] = Field(default_factory=dict)
    final_service_capacity: dict[str, float | None] = Field(default_factory=dict)
    mechanisms: MechanismSwitches = MechanismSwitches()

    @property
    def redevelopment_count(self) -> int:
        return sum(year is not None for year in self.redevelopment_years.values())


def _trigger_value(
    metric: TriggerMetric,
    *,
    accessibility: dict[str, float],
    locations: dict[str, LocationState],
) -> float:
    if metric is TriggerMetric.MEAN_ACCESSIBILITY:
        return sum(accessibility.values()) / len(accessibility)
    if metric is TriggerMetric.MEAN_RENT:
        return sum(location.rent for location in locations.values()) / max(len(locations), 1)
    if metric is TriggerMetric.MEAN_ENVIRONMENT_QUALITY:
        return sum(location.environment_quality for location in locations.values()) / max(
            len(locations), 1
        )
    if metric is TriggerMetric.MAX_HOUSING_OCCUPANCY:
        return max(
            (
                location.households / max(location.housing_capacity, 1.0)
                for location in locations.values()
            ),
            default=0.0,
        )
    if metric is TriggerMetric.MAX_EMPLOYMENT_OCCUPANCY:
        return max(
            (
                location.jobs / max(location.employment_capacity, 1.0)
                for location in locations.values()
            ),
            default=0.0,
        )
    raise AssertionError(f"unsupported trigger metric: {metric}")


def _policy_should_activate(
    policy: PolicySpec,
    *,
    year: int,
    accessibility: dict[str, float],
    locations: dict[str, LocationState],
) -> bool:
    if year < policy.intervention_year:
        return False
    if not policy.activation_triggers:
        return year == policy.intervention_year
    evaluations = []
    for trigger in policy.activation_triggers:
        value = _trigger_value(trigger.metric, accessibility=accessibility, locations=locations)
        evaluations.append(
            value >= trigger.threshold
            if trigger.operator is TriggerOperator.GE
            else value <= trigger.threshold
        )
    return any(evaluations) if policy.trigger_mode is TriggerMode.ANY else all(evaluations)


def run_world(config: WorldRunConfig) -> WorldResult:
    """Run the qualified redevelopment-only vertical slice."""

    unit_ids = tuple(unit.unit_id for unit in config.units)
    initial_by_id = {unit.unit_id: unit for unit in config.units}
    accessibility = {unit.unit_id: unit.accessibility for unit in config.units}
    asset_age = {unit.unit_id: unit.asset_age_years for unit in config.units}
    current_use = {unit.unit_id: unit.current_use for unit in config.units}
    redevelopment_years: dict[str, int | None] = {unit.unit_id: None for unit in config.units}
    development_shocks: dict[int, dict[str, float]] = {}
    locations = {location.unit_id: location for location in config.locations}
    current_households = config.households
    current_firms = config.firms
    household_locations = {
        cohort.cohort_id: cohort.initial_unit_id for cohort in current_households
    }
    firm_locations = {cohort.cohort_id: cohort.initial_unit_id for cohort in current_firms}
    household_taste_shocks: dict[int, dict[str, dict[str, float]]] = {}
    firm_taste_shocks: dict[int, dict[str, dict[str, float]]] = {}
    household_growth_shocks: dict[int, dict[str, float]] = {}
    firm_death_shocks: dict[int, dict[str, float]] = {}
    firm_expansion_shocks: dict[int, dict[str, float]] = {}
    firm_birth_shocks: dict[int, dict[str, float]] = {}
    firm_births: dict[int, tuple[str, ...]] = {}
    firm_deaths: dict[int, tuple[str, ...]] = {}
    labor_traces: dict[int, LaborMatchingResult] = {}
    transport_edges = {edge.edge_id: edge for edge in config.transport_edges}
    transport_traces: dict[int, dict[str, TransportAssignmentResult]] = {}
    environmental_units = {unit.unit_id: unit for unit in config.environmental_units}
    seasonal_environment = {profile.season: profile for profile in config.seasonal_environment}
    environment_traces: dict[int, dict[str, dict[str, ExposureResult]]] = {}
    environment_quality_samples: dict[int, dict[str, list[float]]] = {}
    policy_activation_year: int | None = None

    for step in iter_schedule(config.schedule):
        if (
            step.phase is AnnualPhase.PUBLIC_POLICY
            and config.mechanisms.public_coordination_enabled
        ):
            if policy_activation_year is None and _policy_should_activate(
                config.policy,
                year=step.year,
                accessibility=accessibility,
                locations=locations,
            ):
                policy_activation_year = step.year
                for unit_id in unit_ids:
                    delta = (
                        config.policy.accessibility_delta
                        + config.policy.accessibility_delta_by_unit.get(unit_id, 0.0)
                    )
                    accessibility[unit_id] = min(
                        1.0,
                        max(
                            0.0,
                            accessibility[unit_id] + delta,
                        ),
                    )
                    if unit_id in locations:
                        locations[unit_id] = locations[unit_id].model_copy(
                            update={"accessibility": accessibility[unit_id]}
                        )
                for (
                    edge_id,
                    multiplier,
                ) in config.policy.transport_capacity_multiplier_by_edge.items():
                    edge = transport_edges[edge_id]
                    transport_edges[edge_id] = edge.model_copy(
                        update={"capacity": edge.capacity * multiplier}
                    )
                for edge_id, multiplier in config.policy.transport_time_multiplier_by_edge.items():
                    edge = transport_edges[edge_id]
                    transport_edges[edge_id] = edge.model_copy(
                        update={
                            "free_flow_minutes": edge.free_flow_minutes * multiplier,
                            "generalized_penalty_minutes": (
                                edge.generalized_penalty_minutes * multiplier
                            ),
                        }
                    )
                for unit_id, delta in config.policy.green_fraction_delta_by_unit.items():
                    environmental = environmental_units[unit_id]
                    environmental_units[unit_id] = environmental.model_copy(
                        update={
                            "green_fraction": min(
                                1.0, max(0.0, environmental.green_fraction + delta)
                            )
                        }
                    )
                for location_id, location in locations.items():
                    member_ids = config.location_members.get(location_id, (location_id,))
                    locations[location_id] = location.model_copy(
                        update={
                            "accessibility": sum(accessibility[item] for item in member_ids)
                            / len(member_ids)
                        }
                    )
                for location_id, delta in (
                    config.policy.service_quality_delta_by_location.items()
                    if config.mechanisms.service_provision_enabled
                    else ()
                ):
                    location = locations[location_id]
                    locations[location_id] = location.model_copy(
                        update={
                            "service_quality": min(1.0, max(0.0, location.service_quality + delta))
                        }
                    )
                for (
                    location_id,
                    multiplier,
                ) in (
                    config.policy.service_capacity_multiplier_by_location.items()
                    if config.mechanisms.service_provision_enabled
                    else ()
                ):
                    location = locations[location_id]
                    if location.service_capacity is None:
                        raise AssertionError("validated service capacity cannot be absent")
                    locations[location_id] = location.model_copy(
                        update={"service_capacity": location.service_capacity * multiplier}
                    )

        elif step.phase is AnnualPhase.SEASONAL_OPERATIONS:
            if step.season is None:
                raise AssertionError("seasonal step must declare a season")
            assignment: TransportAssignmentResult | None = None
            if config.transport_assignment is not None:
                assignment = assign_transport(
                    tuple(transport_edges.values()),
                    config.transport_od,
                    config.transport_assignment,
                )
                transport_traces.setdefault(step.year, {})[step.season.value] = assignment
                opportunities = {unit_id: location.jobs for unit_id, location in locations.items()}
                if (
                    sum(opportunities.values()) > 0.0
                    and config.mechanisms.transport_attraction_enabled
                ):
                    generalized_costs = {
                        od_key: min(mode_costs.values())
                        for od_key, mode_costs in assignment.od_mode_costs.items()
                    }
                    skim = opportunity_accessibility(
                        costs=generalized_costs,
                        opportunities=opportunities,
                        decay=config.accessibility_decay,
                    )
                    for location_id, value in skim.items():
                        if location_id in locations:
                            locations[location_id] = locations[location_id].model_copy(
                                update={"accessibility": value}
                            )
                            for member_id in config.location_members.get(
                                location_id, (location_id,)
                            ):
                                accessibility[member_id] = value

            if config.exposure_weights is not None:
                seasonal_results: dict[str, ExposureResult] = {}
                for unit_id, environmental in environmental_units.items():
                    traffic_pressure = 0.0
                    if assignment is not None:
                        traffic_pressure = sum(
                            assignment.edge_flows[edge_id] / transport_edges[edge_id].capacity
                            for edge_id in environmental.transport_edge_ids
                        )
                    seasonal_profile = seasonal_environment[step.season]
                    if not config.mechanisms.seasonality_enabled:
                        count = len(seasonal_environment)
                        seasonal_profile = SeasonalEnvironmentSpec(
                            season=step.season,
                            air_background=sum(
                                profile.air_background for profile in seasonal_environment.values()
                            )
                            / count,
                            noise_background_db=sum(
                                profile.noise_background_db
                                for profile in seasonal_environment.values()
                            )
                            / count,
                            heat_stress=sum(
                                profile.heat_stress for profile in seasonal_environment.values()
                            )
                            / count,
                            night_length_factor=sum(
                                profile.night_length_factor
                                for profile in seasonal_environment.values()
                            )
                            / count,
                            green_cooling_strength=sum(
                                profile.green_cooling_strength
                                for profile in seasonal_environment.values()
                            )
                            / count,
                            activity_heat_factor=sum(
                                profile.activity_heat_factor
                                for profile in seasonal_environment.values()
                            )
                            / count,
                        )
                    exposure = evaluate_exposure(
                        environmental,
                        seasonal_profile,
                        traffic_pressure=traffic_pressure,
                        weights=config.exposure_weights,
                    )
                    seasonal_results[unit_id] = exposure
                    samples = environment_quality_samples.setdefault(step.year, {}).setdefault(
                        unit_id, []
                    )
                    samples.append(exposure.environment_quality)
                    if unit_id in locations and config.mechanisms.environmental_exposure_enabled:
                        locations[unit_id] = locations[unit_id].model_copy(
                            update={"environment_quality": sum(samples) / len(samples)}
                        )
                environment_traces.setdefault(step.year, {})[step.season.value] = seasonal_results

        elif step.phase is AnnualPhase.HOUSEHOLD_RELOCATION and current_households:
            for cohort in current_households:
                unit_id = household_locations[cohort.cohort_id]
                location = locations[unit_id]
                remaining = location.households - cohort.housing_demand
                if remaining < -1e-9:
                    raise ValueError("initial household occupancy is below cohort demand")
                locations[unit_id] = location.model_copy(update={"households": max(0.0, remaining)})
            if config.household_dynamics is not None and config.mechanisms.cohort_dynamics_enabled:
                dynamics = evolve_households(
                    current_households,
                    config.household_dynamics,
                    root_seed=config.root_seed,
                    world_id=config.world_id,
                    year=step.year,
                )
                current_households = dynamics.cohorts
                household_growth_shocks[step.year] = dynamics.growth_shocks
            allocation = allocate_households(
                current_households,
                tuple(locations.values()),
                root_seed=config.root_seed,
                world_id=config.world_id,
                year=step.year,
                taste_shock_scale=config.agent_taste_shock_scale,
            )
            household_locations = allocation.assignments
            locations = {location.unit_id: location for location in allocation.locations}
            household_taste_shocks[step.year] = allocation.taste_shocks

        elif step.phase is AnnualPhase.FIRM_DYNAMICS and (
            current_firms or config.firm_dynamics is not None
        ):
            for cohort in current_firms:
                unit_id = firm_locations[cohort.cohort_id]
                location = locations[unit_id]
                remaining = location.jobs - cohort.employees
                if remaining < -1e-9:
                    raise ValueError("initial employment is below cohort employment")
                locations[unit_id] = location.model_copy(update={"jobs": max(0.0, remaining)})
            if config.firm_dynamics is not None and config.mechanisms.cohort_dynamics_enabled:
                dynamics = evolve_firms(
                    current_firms,
                    config.firm_dynamics,
                    root_seed=config.root_seed,
                    world_id=config.world_id,
                    year=step.year,
                )
                current_firms = dynamics.cohorts
                firm_death_shocks[step.year] = dynamics.death_shocks
                firm_expansion_shocks[step.year] = dynamics.expansion_shocks
                firm_birth_shocks[step.year] = dynamics.birth_shocks
                firm_births[step.year] = dynamics.births
                firm_deaths[step.year] = dynamics.deaths
            firm_cohorts = current_firms
            if not config.mechanisms.agglomeration_enabled:
                firm_cohorts = tuple(
                    cohort.model_copy(update={"agglomeration_weight": 0.0})
                    for cohort in current_firms
                )
            if not firm_cohorts:
                firm_locations = {}
                firm_taste_shocks[step.year] = {}
                continue
            allocation = allocate_firms(
                firm_cohorts,
                tuple(locations.values()),
                root_seed=config.root_seed,
                world_id=config.world_id,
                year=step.year,
                taste_shock_scale=config.agent_taste_shock_scale,
            )
            firm_locations = allocation.assignments
            locations = {location.unit_id: location for location in allocation.locations}
            firm_taste_shocks[step.year] = allocation.taste_shocks

        elif (
            step.phase is AnnualPhase.LABOR_MATCHING
            and config.labor_matching is not None
            and config.mechanisms.labor_matching_enabled
        ):
            seasonal_transport = transport_traces.get(step.year, {})
            latest_assignment = seasonal_transport.get(Season.WINTER.value)
            commute_costs = (
                generalized_cost_skim(
                    tuple(transport_edges.values()),
                    latest_assignment.edge_travel_minutes,
                    nodes=tuple(locations),
                )
                if latest_assignment is not None
                else {}
            )
            labor = match_labor(
                current_households,
                current_firms,
                household_locations=household_locations,
                firm_locations=firm_locations,
                commute_costs=commute_costs,
                spec=config.labor_matching,
            )
            labor_traces[step.year] = labor
            adjusted_firms: list[FirmCohortSpec] = []
            for cohort in current_firms:
                adjusted_employees = labor.adjusted_firm_employees[cohort.cohort_id]
                unit_id = firm_locations[cohort.cohort_id]
                location = locations[unit_id]
                adjusted_jobs = location.jobs - cohort.employees + adjusted_employees
                if adjusted_jobs < -1e-9:
                    raise ValueError("labor adjustment would make location jobs negative")
                locations[unit_id] = location.model_copy(update={"jobs": max(0.0, adjusted_jobs)})
                adjusted_firms.append(
                    cohort.model_copy(
                        update={
                            "employees": adjusted_employees,
                            "offered_wage": labor.adjusted_firm_wages[cohort.cohort_id],
                        }
                    )
                )
            current_firms = tuple(adjusted_firms)

        elif step.phase is AnnualPhase.MARKET_CLEARING and config.market is not None:
            locations = {
                location.unit_id: location
                for location in clear_market(tuple(locations.values()), config.market)
            }

        elif step.phase is AnnualPhase.DEVELOPMENT:
            tape = generate_event_tape(
                EventTapeSpec(
                    root_seed=config.root_seed,
                    world_id=config.world_id,
                    year=step.year,
                    mechanism="development-shock",
                ),
                shape=(len(unit_ids),),
            )
            year_shocks = {
                unit_id: float((tape[index] - 0.5) * 2.0 * config.development_shock_scale)
                for index, unit_id in enumerate(unit_ids)
            }
            development_shocks[step.year] = year_shocks

            for unit_id in unit_ids:
                if redevelopment_years[unit_id] is not None:
                    continue
                initial = initial_by_id[unit_id]
                current = initial.model_copy(
                    update={
                        "asset_age_years": asset_age[unit_id],
                        "accessibility": accessibility[unit_id],
                        "current_use": current_use[unit_id],
                    }
                )
                decision = evaluate_redevelopment(
                    current,
                    candidate_shock=year_shocks[unit_id],
                    transition_inertia_enabled=config.transition_inertia_enabled,
                )
                if decision.should_redevelop:
                    redevelopment_years[unit_id] = step.year
                    current_use[unit_id] = initial.candidate_use
                    asset_age[unit_id] = 0

        elif step.phase is AnnualPhase.INFRASTRUCTURE_AGING:
            for unit_id in unit_ids:
                if redevelopment_years[unit_id] != step.year:
                    asset_age[unit_id] += 1

    return WorldResult(
        root_seed=config.root_seed,
        world_id=config.world_id,
        policy_id=config.policy.policy_id,
        policy_activation_year=policy_activation_year,
        transition_inertia_enabled=config.transition_inertia_enabled,
        redevelopment_years=redevelopment_years,
        final_accessibility=accessibility,
        final_uses=current_use,
        development_shocks=development_shocks,
        household_locations=household_locations,
        firm_locations=firm_locations,
        final_households={unit_id: location.households for unit_id, location in locations.items()},
        final_jobs={unit_id: location.jobs for unit_id, location in locations.items()},
        final_rents={unit_id: location.rent for unit_id, location in locations.items()},
        household_taste_shocks=household_taste_shocks,
        firm_taste_shocks=firm_taste_shocks,
        final_household_populations={
            cohort.cohort_id: cohort.population for cohort in current_households
        },
        final_firm_employees={cohort.cohort_id: cohort.employees for cohort in current_firms},
        household_growth_shocks=household_growth_shocks,
        firm_death_shocks=firm_death_shocks,
        firm_expansion_shocks=firm_expansion_shocks,
        firm_birth_shocks=firm_birth_shocks,
        firm_births=firm_births,
        firm_deaths=firm_deaths,
        labor_traces=labor_traces,
        final_firm_wages={cohort.cohort_id: cohort.offered_wage for cohort in current_firms},
        transport_traces=transport_traces,
        environment_traces=environment_traces,
        final_environment_quality={
            unit_id: location.environment_quality for unit_id, location in locations.items()
        },
        final_service_quality={
            unit_id: location.service_quality for unit_id, location in locations.items()
        },
        final_service_capacity={
            unit_id: location.service_capacity for unit_id, location in locations.items()
        },
        mechanisms=config.mechanisms,
    )
