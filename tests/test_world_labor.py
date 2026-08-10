from urban_field_dynamics.agents import FirmCohortSpec, HouseholdCohortSpec, LocationState
from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.labor import LaborMatchingSpec
from urban_field_dynamics.market import MarketClearingSpec
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import MechanismSwitches, PolicySpec, WorldRunConfig, run_world

SYNTHETIC = EvidenceStatus.SYNTHETIC


def config(*, labor_enabled: bool) -> WorldRunConfig:
    return WorldRunConfig(
        root_seed=7,
        world_id=2,
        schedule=ScheduleConfig(start_year=2026, end_year=2027, replan_years={2026}),
        units=(
            SpatialUnitSpec(
                unit_id="zone-aa",
                area_sqm=10_000.0,
                current_use=LandUse.MIXED,
                candidate_use=LandUse.MIXED,
                pin_kind=PinKind.HARD,
                asset_age_years=10,
                design_life_years=50,
                keep_npv=100.0,
                candidate_base_npv=100.0,
                transition_cost=0.0,
                accessibility=0.5,
                accessibility_value_factor=0.0,
                evidence_status=SYNTHETIC,
            ),
        ),
        policy=PolicySpec(policy_id="p0", intervention_year=2026),
        locations=(
            LocationState(
                unit_id="zone-aa",
                accessibility=0.5,
                rent=10.0,
                jobs=5.0,
                households=10.0,
                housing_capacity=100.0,
                employment_capacity=100.0,
                environment_quality=0.5,
                evidence_status=SYNTHETIC,
            ),
        ),
        households=(
            HouseholdCohortSpec(
                cohort_id="workers",
                population=10.0,
                initial_unit_id="zone-aa",
                income=100.0,
                housing_demand_per_person=1.0,
                accessibility_weight=1.0,
                jobs_weight=1.0,
                environment_weight=1.0,
                rent_burden_weight=1.0,
                labor_force_share=1.0,
                skill_group="general",
                reservation_wage=50.0,
                evidence_status=SYNTHETIC,
            ),
        ),
        firms=(
            FirmCohortSpec(
                cohort_id="employer",
                employees=5.0,
                initial_unit_id="zone-aa",
                floor_demand_per_employee=1.0,
                accessibility_weight=1.0,
                agglomeration_weight=1.0,
                rent_weight=1.0,
                labor_demand_share=1.0,
                skill_requirement="general",
                offered_wage=100.0,
                evidence_status=SYNTHETIC,
            ),
        ),
        labor_matching=LaborMatchingSpec(
            max_commute_minutes=45.0,
            commute_cost_per_minute=1.0,
            wage_adjustment_rate=0.1,
        ),
        market=MarketClearingSpec(
            target_occupancy=0.5,
            adjustment_rate=0.0,
            housing_pressure_weight=0.5,
            employment_pressure_weight=0.5,
            minimum_rent=0.0,
        ),
        mechanisms=MechanismSwitches(labor_matching_enabled=labor_enabled),
    )


def test_world_records_labor_mismatch_and_carries_wage_feedback() -> None:
    result = run_world(config(labor_enabled=True))

    assert tuple(result.labor_traces) == (2026, 2027)
    assert result.labor_traces[2026].unemployment_rate == 0.5
    assert result.labor_traces[2026].vacancy_rate == 0.0
    assert result.final_firm_wages["employer"] < 100.0


def test_world_labor_ablation_disables_matching_and_wage_feedback() -> None:
    result = run_world(config(labor_enabled=False))

    assert result.labor_traces == {}
    assert result.final_firm_wages == {"employer": 100.0}


def test_world_carries_unfilled_job_attrition_into_firm_and_location_state() -> None:
    base = config(labor_enabled=True)
    household = base.households[0].model_copy(update={"population": 3.0})
    location = base.locations[0].model_copy(update={"households": 3.0})
    adjusted = base.model_copy(
        update={
            "schedule": ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
            "households": (household,),
            "locations": (location,),
            "labor_matching": LaborMatchingSpec(
                max_commute_minutes=45.0,
                commute_cost_per_minute=1.0,
                wage_adjustment_rate=0.1,
                vacancy_retention_rate=0.5,
            ),
        }
    )

    result = run_world(adjusted)

    assert result.labor_traces[2026].firm_vacancies == {"employer": 2.0}
    assert result.final_firm_employees == {"employer": 4.0}
    assert result.final_jobs == {"zone-aa": 4.0}
