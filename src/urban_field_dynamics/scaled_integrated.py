"""Scaled 1,200-cell / 48-zone integrated synthetic campaign fixture."""

from __future__ import annotations

from collections import defaultdict

from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec, LocationState
from urban_field_dynamics.campaign import CampaignArm, CampaignSpec
from urban_field_dynamics.contracts import EvidenceStatus, LandUse
from urban_field_dynamics.dynamics import (
    FirmBirthPrototype,
    FirmDynamicsSpec,
    HouseholdDynamicsSpec,
)
from urban_field_dynamics.environment import (
    EnvironmentalUnitSpec,
    ExposureWeights,
    SeasonalEnvironmentSpec,
)
from urban_field_dynamics.infrastructure import (
    BudgetRationingMode,
    InfrastructureLedgerSpec,
)
from urban_field_dynamics.labor import LaborMatchingSpec
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig, Season
from urban_field_dynamics.spatial import (
    FocusZoneSpec,
    StylizedGrid,
    StylizedGridSpec,
    StylizedZoning,
    StylizedZoningSpec,
    generate_stylized_grid,
    generate_stylized_zoning,
)
from urban_field_dynamics.stress import (
    StressEvidenceSpec,
    StressMatrixSpec,
    StressMetric,
    StressScenario,
)
from urban_field_dynamics.transport import (
    ODPair,
    TransportAssignmentSpec,
    TransportEdgeSpec,
    TransportMode,
)
from urban_field_dynamics.world import MechanismSwitches, PolicySpec

SYNTHETIC = EvidenceStatus.SYNTHETIC


def _substrate() -> tuple[StylizedGrid, StylizedZoning]:
    grid = generate_stylized_grid(
        StylizedGridSpec(
            root_seed=20260810,
            rows=40,
            columns=30,
            cell_size_m=100.0,
            corridor_center_column=15,
            corridor_half_width_cells=2,
            focus_zones=(
                FocusZoneSpec(
                    zone_id="focus-north",
                    center_row=8,
                    center_column=8,
                    radius_cells=3,
                ),
                FocusZoneSpec(
                    zone_id="focus-central",
                    center_row=20,
                    center_column=15,
                    radius_cells=3,
                ),
                FocusZoneSpec(
                    zone_id="focus-south",
                    center_row=32,
                    center_column=22,
                    radius_cells=3,
                ),
            ),
        )
    )
    zoning = generate_stylized_zoning(
        grid,
        StylizedZoningSpec(block_rows=5, block_columns=5),
    )
    return grid, zoning


def _anchors(zoning: StylizedZoning) -> dict[str, str]:
    anchors: dict[str, str] = {}
    for focus_id in ("focus-north", "focus-central", "focus-south"):
        anchors[focus_id] = next(
            zone.zone_id for zone in zoning.zones if focus_id in zone.focus_zone_ids
        )
    anchors["corridor"] = next(zone.zone_id for zone in zoning.zones if zone.is_corridor_observer)
    return anchors


def _households(anchors: dict[str, str]) -> tuple[HouseholdCohortSpec, ...]:
    rows = (
        ("students", 40.0, "focus-north", 80.0, 1.4, 1.0, 0.8, 1.2, 1.0),
        ("research-talent", 40.0, "focus-central", 160.0, 1.3, 1.4, 0.6, 0.6, 0.7),
        ("service-workers", 40.0, "focus-south", 90.0, 0.8, 1.5, 0.5, 1.5, 0.8),
        ("older-adults", 35.0, "corridor", 100.0, 0.8, 0.5, 1.8, 1.0, 1.8),
        (
            "families-with-children",
            45.0,
            "focus-central",
            140.0,
            0.9,
            0.9,
            1.5,
            0.8,
            1.8,
        ),
        ("accessibility-needs", 30.0, "focus-south", 95.0, 1.0, 0.6, 1.7, 1.2, 1.7),
    )
    return tuple(
        HouseholdCohortSpec(
            cohort_id=cohort_id,
            population=population,
            initial_unit_id=anchors[anchor],
            income=income,
            housing_demand_per_person=1.0,
            accessibility_weight=accessibility_weight,
            jobs_weight=jobs_weight,
            environment_weight=environment_weight,
            rent_burden_weight=rent_weight,
            service_weight=service_weight,
            equity_group={
                "students": "students",
                "research-talent": "research-talent",
                "service-workers": "service-workers",
                "older-adults": "older-adults",
                "families-with-children": "families",
                "accessibility-needs": "accessibility-needs",
            }[cohort_id],
            labor_force_share={
                "students": 0.40,
                "research-talent": 0.80,
                "service-workers": 0.85,
                "older-adults": 0.15,
                "families-with-children": 0.65,
                "accessibility-needs": 0.50,
            }[cohort_id],
            skill_group={
                "students": "general",
                "research-talent": "knowledge",
                "service-workers": "service",
                "older-adults": "general",
                "families-with-children": "general",
                "accessibility-needs": "service",
            }[cohort_id],
            reservation_wage={
                "students": 65.0,
                "research-talent": 130.0,
                "service-workers": 75.0,
                "older-adults": 70.0,
                "families-with-children": 100.0,
                "accessibility-needs": 75.0,
            }[cohort_id],
            evidence_status=SYNTHETIC,
        )
        for (
            cohort_id,
            population,
            anchor,
            income,
            accessibility_weight,
            jobs_weight,
            environment_weight,
            rent_weight,
            service_weight,
        ) in rows
    )


def _firms(anchors: dict[str, str]) -> tuple[FirmCohortSpec, ...]:
    rows = (
        ("ai-research", 35.0, "focus-central", 1.5, 2.0, 0.5),
        ("technology-services", 30.0, "focus-north", 1.2, 1.7, 0.6),
        ("daily-commerce", 30.0, "focus-south", 0.9, 1.0, 1.0),
        ("logistics-operations", 25.0, "corridor", 1.1, 0.7, 1.2),
        ("cultural-activity", 25.0, "focus-south", 1.0, 1.1, 0.8),
        ("public-education", 35.0, "focus-central", 0.8, 0.8, 0.4),
    )
    return tuple(
        FirmCohortSpec(
            cohort_id=cohort_id,
            employees=employees,
            initial_unit_id=anchors[anchor],
            floor_demand_per_employee=1.0,
            accessibility_weight=accessibility_weight,
            agglomeration_weight=agglomeration_weight,
            rent_weight=rent_weight,
            skill_requirement={
                "ai-research": "knowledge",
                "technology-services": "knowledge",
                "daily-commerce": "service",
                "logistics-operations": "service",
                "cultural-activity": "service",
                "public-education": "knowledge",
            }[cohort_id],
            offered_wage={
                "ai-research": 165.0,
                "technology-services": 145.0,
                "daily-commerce": 90.0,
                "logistics-operations": 100.0,
                "cultural-activity": 110.0,
                "public-education": 125.0,
            }[cohort_id],
            evidence_status=SYNTHETIC,
        )
        for (
            cohort_id,
            employees,
            anchor,
            accessibility_weight,
            agglomeration_weight,
            rent_weight,
        ) in rows
    )


def _locations(
    grid: StylizedGrid,
    zoning: StylizedZoning,
    households: tuple[HouseholdCohortSpec, ...],
    firms: tuple[FirmCohortSpec, ...],
) -> tuple[LocationState, ...]:
    units = {unit.spec.unit_id: unit.spec for unit in grid.units}
    household_counts: defaultdict[str, float] = defaultdict(float)
    job_counts: defaultdict[str, float] = defaultdict(float)
    for cohort in households:
        household_counts[cohort.initial_unit_id] += cohort.housing_demand
    for cohort in firms:
        job_counts[cohort.initial_unit_id] += cohort.employees
    return tuple(
        LocationState(
            unit_id=zone.zone_id,
            accessibility=sum(units[item].accessibility for item in zone.member_unit_ids)
            / len(zone.member_unit_ids),
            rent=15.0
            + sum(units[item].keep_npv for item in zone.member_unit_ids)
            / len(zone.member_unit_ids)
            / 10.0,
            jobs=job_counts[zone.zone_id],
            households=household_counts[zone.zone_id],
            housing_capacity=500.0,
            employment_capacity=500.0,
            environment_quality=0.5,
            service_quality=0.3
            + 0.6
            * sum(
                units[item].current_use is LandUse.PUBLIC_SERVICE for item in zone.member_unit_ids
            )
            / len(zone.member_unit_ids),
            service_capacity=20.0
            + 150.0
            * sum(
                units[item].current_use is LandUse.PUBLIC_SERVICE for item in zone.member_unit_ids
            )
            / len(zone.member_unit_ids),
            evidence_status=SYNTHETIC,
        )
        for zone in zoning.zones
    )


def _environment(
    grid: StylizedGrid,
    zoning: StylizedZoning,
    road_edges_by_origin: dict[str, tuple[str, ...]],
) -> tuple[EnvironmentalUnitSpec, ...]:
    units = {unit.spec.unit_id: unit.spec for unit in grid.units}
    active_uses = {LandUse.RESEARCH, LandUse.COMMERCIAL, LandUse.MIXED}
    return tuple(
        EnvironmentalUnitSpec(
            unit_id=zone.zone_id,
            green_fraction=sum(
                units[item].current_use is LandUse.GREEN for item in zone.member_unit_ids
            )
            / len(zone.member_unit_ids),
            traffic_exposure_factor=0.18,
            activity_intensity=sum(
                units[item].current_use in active_uses for item in zone.member_unit_ids
            )
            / len(zone.member_unit_ids),
            night_light_intensity=0.25
            + 0.5
            * sum(units[item].current_use in active_uses for item in zone.member_unit_ids)
            / len(zone.member_unit_ids),
            transport_edge_ids=road_edges_by_origin.get(zone.zone_id, ()),
            evidence_status=SYNTHETIC,
        )
        for zone in zoning.zones
    )


def _seasons() -> tuple[SeasonalEnvironmentSpec, ...]:
    values = {
        Season.SPRING: (0.20, 45.0, 0.25, 0.50),
        Season.SUMMER: (0.35, 48.0, 0.90, 0.35),
        Season.AUTUMN: (0.25, 46.0, 0.35, 0.55),
        Season.WINTER: (0.45, 50.0, 0.20, 0.90),
    }
    return tuple(
        SeasonalEnvironmentSpec(
            season=season,
            air_background=air,
            noise_background_db=noise,
            heat_stress=heat,
            night_length_factor=night,
            green_cooling_strength=0.65,
            activity_heat_factor=0.1,
        )
        for season, (air, noise, heat, night) in values.items()
    )


def _transport(
    zoning: StylizedZoning,
) -> tuple[tuple[TransportEdgeSpec, ...], dict[str, tuple[str, ...]]]:
    by_id = {zone.zone_id: zone for zone in zoning.zones}
    edge_rows: list[tuple[str, str, TransportMode, float, float]] = []
    mode_values = {
        TransportMode.WALK: (6.0, 1_000.0),
        TransportMode.CYCLE: (2.0, 20.0),
        TransportMode.ROAD: (1.5, 30.0),
        TransportMode.BUS: (3.0, 15.0),
    }
    for zone in zoning.zones:
        for neighbor_id in zone.neighbor_zone_ids:
            for mode, (minutes, capacity) in mode_values.items():
                edge_rows.append((zone.zone_id, neighbor_id, mode, minutes, capacity))
            if zone.is_corridor_observer and by_id[neighbor_id].is_corridor_observer:
                edge_rows.append((zone.zone_id, neighbor_id, TransportMode.RAIL, 1.2, 30.0))
    edges = tuple(
        TransportEdgeSpec(
            edge_id=f"{mode.value}-{origin}-{destination}",
            from_node=origin,
            to_node=destination,
            mode=mode,
            free_flow_minutes=minutes,
            capacity=capacity,
            generalized_penalty_minutes=(1.0 if mode is TransportMode.BUS else 0.0),
        )
        for origin, destination, mode, minutes, capacity in edge_rows
    )
    road_edges: defaultdict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.mode is TransportMode.ROAD:
            road_edges[edge.from_node].append(edge.edge_id)
    return edges, {origin: tuple(sorted(edge_ids)) for origin, edge_ids in road_edges.items()}


def _od(
    households: tuple[HouseholdCohortSpec, ...],
    firms: tuple[FirmCohortSpec, ...],
) -> tuple[ODPair, ...]:
    demand: defaultdict[tuple[str, str], float] = defaultdict(float)
    for household in households:
        for firm in firms:
            demand[(household.initial_unit_id, firm.initial_unit_id)] += household.population / len(
                firms
            )
    return tuple(
        ODPair(origin=origin, destination=destination, demand=value)
        for (origin, destination), value in sorted(demand.items())
    )


def _arms(
    edges: tuple[TransportEdgeSpec, ...],
    zoning: StylizedZoning,
) -> tuple[CampaignArm, ...]:
    transit_multipliers = {
        edge.edge_id: 4.0
        for edge in edges
        if edge.mode in {TransportMode.CYCLE, TransportMode.BUS, TransportMode.RAIL}
    }
    transit_time_multipliers = {
        edge.edge_id: 0.65
        for edge in edges
        if edge.mode in {TransportMode.CYCLE, TransportMode.BUS, TransportMode.RAIL}
    }
    green_delta = {zone.zone_id: (0.25 if zone.focus_zone_ids else 0.15) for zone in zoning.zones}
    service_delta = {zone.zone_id: (0.25 if zone.focus_zone_ids else 0.10) for zone in zoning.zones}
    service_capacity_multiplier = {
        zone.zone_id: (2.0 if zone.focus_zone_ids else 1.5) for zone in zoning.zones
    }
    p0 = PolicySpec(policy_id="p0", intervention_year=2026)
    p1 = PolicySpec(
        policy_id="p1",
        intervention_year=2026,
        public_capital_cost=120.0,
        annual_operating_cost=4.0,
        transport_capacity_multiplier_by_edge=transit_multipliers,
        transport_time_multiplier_by_edge=transit_time_multipliers,
    )
    p2 = PolicySpec(
        policy_id="p2",
        intervention_year=2026,
        public_capital_cost=90.0,
        annual_operating_cost=3.0,
        green_fraction_delta_by_unit=green_delta,
    )
    p3 = PolicySpec(
        policy_id="p3",
        intervention_year=2026,
        public_capital_cost=240.0,
        annual_operating_cost=8.0,
        transport_capacity_multiplier_by_edge=transit_multipliers,
        transport_time_multiplier_by_edge=transit_time_multipliers,
        green_fraction_delta_by_unit=green_delta,
        service_quality_delta_by_location=service_delta,
        service_capacity_multiplier_by_location=service_capacity_multiplier,
    )
    return (
        CampaignArm(arm_id="p0", policy=p0),
        CampaignArm(arm_id="p1", policy=p1),
        CampaignArm(arm_id="p2", policy=p2),
        CampaignArm(arm_id="p3", policy=p3),
        CampaignArm(arm_id="p3-no-inertia", policy=p3, transition_inertia_enabled=False),
        CampaignArm(
            arm_id="p3-no-agglomeration",
            policy=p3,
            mechanisms=MechanismSwitches(agglomeration_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-transport-attraction",
            policy=p3,
            mechanisms=MechanismSwitches(transport_attraction_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-seasonality",
            policy=p3,
            mechanisms=MechanismSwitches(seasonality_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-environmental-exposure",
            policy=p3,
            mechanisms=MechanismSwitches(environmental_exposure_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-service-provision",
            policy=p3,
            mechanisms=MechanismSwitches(service_provision_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-cohort-dynamics",
            policy=p3,
            mechanisms=MechanismSwitches(cohort_dynamics_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-labor-matching",
            policy=p3,
            mechanisms=MechanismSwitches(labor_matching_enabled=False),
        ),
        CampaignArm(
            arm_id="p3-no-public-coordination",
            policy=p3,
            mechanisms=MechanismSwitches(public_coordination_enabled=False),
        ),
    )


def _firm_dynamics(anchors: dict[str, str]) -> FirmDynamicsSpec:
    shared = {
        "annual_birth_probability": 0.05,
        "employees": 8.0,
        "floor_demand_per_employee": 1.0,
        "accessibility_weight": 0.8,
        "agglomeration_weight": 0.5,
        "rent_weight": 0.3,
        "evidence_status": SYNTHETIC,
    }
    return FirmDynamicsSpec(
        annual_death_probability=0.01,
        mean_employee_growth_rate=0.01,
        employee_growth_volatility=0.02,
        birth_prototypes=(
            FirmBirthPrototype(
                prototype_id="startup-north",
                initial_unit_id=anchors["focus-north"],
                skill_requirement="knowledge",
                offered_wage=125.0,
                **shared,
            ),
            FirmBirthPrototype(
                prototype_id="startup-south",
                initial_unit_id=anchors["focus-south"],
                skill_requirement="service",
                offered_wage=95.0,
                **shared,
            ),
        ),
    )


def scaled_integrated_campaign(
    *,
    world_count: int = 1,
    end_year: int = 2028,
) -> CampaignSpec:
    """Build the scaled synthetic campaign without asserting empirical calibration."""

    grid, zoning = _substrate()
    anchors = _anchors(zoning)
    households = _households(anchors)
    firms = _firms(anchors)
    edges, road_edges = _transport(zoning)
    stage = "canary" if world_count < 32 else "qualification"
    campaign_id = f"scaled-integrated-{stage}-{world_count}"
    if end_year != 2028:
        campaign_id = f"scaled-integrated-{end_year}-{stage}-{world_count}"
    return CampaignSpec(
        campaign_id=campaign_id,
        model_scope="1,200-cell and 48-zone integrated synthetic qualification slice",
        root_seed=20260810,
        world_ids=tuple(range(world_count)),
        schedule=ScheduleConfig(
            start_year=2026,
            end_year=end_year,
            replan_years={year for year in (2026, 2030, 2035, 2040, 2045) if year <= end_year},
        ),
        units=tuple(unit.spec for unit in grid.units),
        arms=_arms(edges, zoning),
        development_shock_scale=12.0,
        locations=_locations(grid, zoning, households, firms),
        location_members={zone.zone_id: zone.member_unit_ids for zone in zoning.zones},
        households=households,
        firms=firms,
        household_dynamics=HouseholdDynamicsSpec(
            mean_growth_rate=0.002,
            growth_volatility=0.002,
        ),
        firm_dynamics=_firm_dynamics(anchors),
        labor_matching=LaborMatchingSpec(
            max_commute_minutes=75.0,
            commute_cost_per_minute=0.8,
            wage_adjustment_rate=0.08,
            unemployment_wage_relief=0.5,
            vacancy_retention_rate=0.95,
        ),
        infrastructure_ledger=InfrastructureLedgerSpec(
            annual_budget=300.0,
            cumulative_budget=5_000.0,
            capital_rationing=BudgetRationingMode.FAIL_CLOSED,
            redevelopment_public_cost_per_transition=0.02,
        ),
        market=MarketClearingSpec(
            target_occupancy=0.65,
            adjustment_rate=0.15,
            housing_pressure_weight=0.6,
            employment_pressure_weight=0.4,
            minimum_rent=5.0,
            maximum_rent=1_000.0,
            solver_relaxation=0.5,
            maximum_annual_rent_change=1.0,
            max_iterations=64,
            convergence_tolerance=1e-5,
            require_convergence=True,
        ),
        agent_taste_shock_scale=0.12,
        transport_edges=edges,
        transport_od=_od(households, firms),
        transport_assignment=TransportAssignmentSpec(
            bpr_alpha=0.15,
            bpr_beta=4.0,
            logit_theta=0.25,
            iterations=10,
        ),
        accessibility_decay=0.08,
        environmental_units=_environment(grid, zoning, road_edges),
        seasonal_environment=_seasons(),
        exposure_weights=ExposureWeights(air=0.3, noise=0.2, light=0.15, heat=0.35),
    )


def scaled_stress_evidence_spec(
    *,
    world_count: int = 8,
    end_year: int = 2050,
) -> StressEvidenceSpec:
    """Return the standard synthetic one-at-a-time stress matrix."""

    full = scaled_integrated_campaign(world_count=world_count, end_year=end_year)
    values = full.model_dump(mode="python")
    values["arms"] = tuple(arm for arm in full.arms if arm.arm_id in {"p0", "p1", "p2", "p3"})
    base = CampaignSpec.model_validate(values)
    return StressEvidenceSpec(
        matrix=StressMatrixSpec(
            matrix_id=f"scaled-stress-{end_year}-{world_count}",
            base_campaign=base,
            scenarios=(
                StressScenario(scenario_id="baseline"),
                StressScenario(
                    scenario_id="growth-pressure",
                    household_growth_rate_delta=0.01,
                ),
                StressScenario(
                    scenario_id="firm-contraction",
                    firm_growth_rate_delta=-0.02,
                    firm_death_probability_delta=0.02,
                    firm_birth_probability_multiplier=0.7,
                ),
                StressScenario(
                    scenario_id="transport-disruption",
                    transport_capacity_multiplier=0.7,
                ),
                StressScenario(
                    scenario_id="heat-stress",
                    heat_stress_delta=0.15,
                ),
                StressScenario(
                    scenario_id="service-constraint",
                    service_capacity_multiplier=0.8,
                ),
            ),
        ),
        metrics=(
            StressMetric.FINAL_ACCESSIBILITY,
            StressMetric.FINAL_ENVIRONMENT_QUALITY,
            StressMetric.FINAL_RENT,
            StressMetric.FINAL_POPULATION,
            StressMetric.FINAL_EMPLOYMENT,
            StressMetric.FINAL_UNEMPLOYMENT,
            StressMetric.FINAL_SERVICE_UNMET,
            StressMetric.CUMULATIVE_PUBLIC_SPEND,
        ),
    )
