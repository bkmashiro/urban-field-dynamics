import pytest

from urban_field_dynamics.contracts import EvidenceStatus
from urban_field_dynamics.environment import (
    EnvironmentalUnitSpec,
    ExposureWeights,
    SeasonalEnvironmentSpec,
    evaluate_exposure,
)
from urban_field_dynamics.schedule import Season


def unit(*, green_fraction: float = 0.2) -> EnvironmentalUnitSpec:
    return EnvironmentalUnitSpec(
        unit_id="unit-aa",
        green_fraction=green_fraction,
        traffic_exposure_factor=0.5,
        activity_intensity=0.4,
        night_light_intensity=0.6,
        transport_edge_ids=("road-aa",),
        evidence_status=EvidenceStatus.SYNTHETIC,
    )


def season(name: Season) -> SeasonalEnvironmentSpec:
    return SeasonalEnvironmentSpec(
        season=name,
        air_background=0.2,
        noise_background_db=45.0,
        heat_stress=0.8 if name is Season.SUMMER else 0.2,
        night_length_factor=0.5 if name is Season.SUMMER else 1.0,
        green_cooling_strength=0.5,
        activity_heat_factor=0.1,
    )


def weights() -> ExposureWeights:
    return ExposureWeights(air=0.25, noise=0.25, light=0.25, heat=0.25)


def test_summer_heat_exposure_exceeds_winter_for_same_unit() -> None:
    summer = evaluate_exposure(
        unit(), season(Season.SUMMER), traffic_pressure=0.0, weights=weights()
    )
    winter = evaluate_exposure(
        unit(), season(Season.WINTER), traffic_pressure=0.0, weights=weights()
    )

    assert summer.heat > winter.heat


def test_green_fraction_reduces_heat_and_improves_environment_quality() -> None:
    sparse = evaluate_exposure(
        unit(green_fraction=0.0),
        season(Season.SUMMER),
        traffic_pressure=0.5,
        weights=weights(),
    )
    green = evaluate_exposure(
        unit(green_fraction=0.8),
        season(Season.SUMMER),
        traffic_pressure=0.5,
        weights=weights(),
    )

    assert green.heat < sparse.heat
    assert green.environment_quality > sparse.environment_quality


def test_traffic_pressure_raises_air_and_noise_exposure() -> None:
    quiet = evaluate_exposure(
        unit(), season(Season.SPRING), traffic_pressure=0.0, weights=weights()
    )
    busy = evaluate_exposure(unit(), season(Season.SPRING), traffic_pressure=2.0, weights=weights())

    assert busy.air > quiet.air
    assert busy.noise_db > quiet.noise_db
    assert busy.environment_quality < quiet.environment_quality


def test_noise_uses_logarithmic_not_linear_addition() -> None:
    one = evaluate_exposure(unit(), season(Season.SPRING), traffic_pressure=1.0, weights=weights())
    two = evaluate_exposure(unit(), season(Season.SPRING), traffic_pressure=2.0, weights=weights())
    background = season(Season.SPRING).noise_background_db

    assert two.noise_db - background < 2.0 * (one.noise_db - background)
    assert 0.0 <= two.environment_quality <= 1.0


def test_exposure_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="exposure weights must sum to one"):
        ExposureWeights(air=0.5, noise=0.5, light=0.5, heat=0.5)
