import pytest
from pydantic import ValidationError

from urban_field_dynamics.agents import LocationState
from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.market import MarketClearingError, MarketClearingSpec, clear_market


def location(
    unit_id: str,
    *,
    rent: float,
    households: float,
    jobs: float,
    capacity: float = 100.0,
) -> LocationState:
    return LocationState(
        unit_id=unit_id,
        accessibility=0.5,
        rent=rent,
        jobs=jobs,
        households=households,
        housing_capacity=capacity,
        employment_capacity=capacity,
        environment_quality=0.5,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def spec(**updates: object) -> MarketClearingSpec:
    values = {
        "target_occupancy": 0.7,
        "adjustment_rate": 0.2,
        "housing_pressure_weight": 0.6,
        "employment_pressure_weight": 0.4,
        "minimum_rent": 1.0,
        "maximum_rent": 100.0,
        "solver_relaxation": 0.5,
        "maximum_annual_rent_change": 1.0,
        "max_iterations": 200,
        "convergence_tolerance": 1e-6,
    }
    values.update(updates)
    return MarketClearingSpec(**values)


def test_market_clearing_raises_high_pressure_rent_and_lowers_low_pressure_rent() -> None:
    result = clear_market(
        (
            location("high", rent=10.0, households=90.0, jobs=90.0),
            location("low", rent=10.0, households=20.0, jobs=20.0),
        ),
        spec(),
    )
    by_id = {state.unit_id: state for state in result.locations}

    assert result.converged
    assert result.max_residual <= 1e-6
    assert by_id["high"].rent > 10.0
    assert by_id["low"].rent < 10.0


def test_market_clearing_keeps_rent_at_declared_floor() -> None:
    result = clear_market(
        (location("low", rent=1.0, households=0.0, jobs=0.0),),
        spec(adjustment_rate=1.0, minimum_rent=0.8),
    )

    assert result.locations[0].rent == 0.8
    assert result.converged


def test_market_pressure_weights_must_sum_to_one() -> None:
    with pytest.raises(ValidationError, match="pressure weights must sum to one"):
        spec(housing_pressure_weight=0.7, employment_pressure_weight=0.4)


def test_market_clearing_is_input_order_invariant() -> None:
    locations = (
        location("unit-aa", rent=10.0, households=80.0, jobs=40.0),
        location("unit-bb", rent=8.0, households=20.0, jobs=60.0),
    )

    assert clear_market(locations, spec()) == clear_market(tuple(reversed(locations)), spec())


def test_market_reports_non_convergence_and_can_fail_closed() -> None:
    locations = (location("high", rent=10.0, households=90.0, jobs=90.0),)
    diagnostic = clear_market(
        locations,
        spec(max_iterations=1, convergence_tolerance=1e-12),
    )

    assert not diagnostic.converged
    assert diagnostic.iterations == 1
    assert diagnostic.max_residual > 0.0

    with pytest.raises(MarketClearingError, match="did not converge"):
        clear_market(
            locations,
            spec(max_iterations=1, convergence_tolerance=1e-12, require_convergence=True),
        )
