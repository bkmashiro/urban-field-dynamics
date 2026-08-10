import pytest

from urban_field_dynamics.contracts import EvidenceStatus, LandUse, PinKind, SpatialUnitSpec
from urban_field_dynamics.infrastructure import (
    BudgetExceededError,
    BudgetRationingMode,
    InfrastructureLedgerSpec,
)
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def config(mode: BudgetRationingMode) -> WorldRunConfig:
    unit = SpatialUnitSpec(
        unit_id="unit-aa",
        area_sqm=10_000.0,
        current_use=LandUse.MIXED,
        candidate_use=LandUse.MIXED,
        pin_kind=PinKind.HARD,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=100.0,
        candidate_base_npv=100.0,
        transition_cost=0.0,
        accessibility=0.2,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )
    return WorldRunConfig(
        root_seed=7,
        world_id=1,
        schedule=ScheduleConfig(start_year=2026, end_year=2027, replan_years={2026}),
        units=(unit,),
        policy=PolicySpec(
            policy_id="capital-policy",
            intervention_year=2026,
            accessibility_delta=0.4,
            public_capital_cost=100.0,
            annual_operating_cost=10.0,
        ),
        infrastructure_ledger=InfrastructureLedgerSpec(
            annual_budget=60.0,
            cumulative_budget=200.0,
            capital_rationing=mode,
        ),
    )


def test_world_rations_declared_capital_and_records_operating_cost() -> None:
    result = run_world(config(BudgetRationingMode.PROPORTIONAL))

    assert result.final_accessibility == {"unit-aa": pytest.approx(0.44)}
    assert result.infrastructure_traces[2026].capital_funded == 60.0
    assert result.infrastructure_traces[2026].capital_funding_fraction == 0.6
    assert result.infrastructure_traces[2026].operating_cost == 0.0
    assert result.infrastructure_traces[2027].operating_cost == 10.0
    assert result.infrastructure_traces[2027].cumulative_public_spend == 70.0


def test_world_fails_closed_when_capital_exceeds_budget_without_rationing() -> None:
    with pytest.raises(BudgetExceededError, match="requested=100"):
        run_world(config(BudgetRationingMode.FAIL_CLOSED))
