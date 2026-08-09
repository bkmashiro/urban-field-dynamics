import pytest
from pydantic import ValidationError

from urban_field_dynamics.contracts import (
    EvidenceStatus,
    LandUse,
    PinKind,
    SpatialUnitSpec,
)


def test_spatial_unit_contract_records_evidence_and_transition_inputs() -> None:
    unit = SpatialUnitSpec(
        unit_id="u-001",
        area_sqm=10_000.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESEARCH,
        pin_kind=PinKind.SOFT,
        asset_age_years=10,
        design_life_years=50,
        keep_npv=120.0,
        candidate_base_npv=145.0,
        transition_cost=40.0,
        accessibility=0.4,
        accessibility_value_factor=30.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )

    assert unit.asset_age_years < unit.design_life_years
    assert unit.evidence_status is EvidenceStatus.SYNTHETIC


def test_spatial_unit_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SpatialUnitSpec.model_validate(
            {
                "unit_id": "u-001",
                "area_sqm": 100.0,
                "current_use": "residential",
                "candidate_use": "research",
                "pin_kind": "free",
                "asset_age_years": 1,
                "design_life_years": 50,
                "keep_npv": 1.0,
                "candidate_base_npv": 2.0,
                "transition_cost": 0.0,
                "accessibility": 0.0,
                "accessibility_value_factor": 0.0,
                "evidence_status": "synthetic",
                "invented": True,
            }
        )


def test_spatial_unit_contract_allows_renewal_ready_age_beyond_design_life() -> None:
    unit = SpatialUnitSpec(
        unit_id="u-001",
        area_sqm=100.0,
        current_use=LandUse.RESIDENTIAL,
        candidate_use=LandUse.RESEARCH,
        pin_kind=PinKind.SOFT,
        asset_age_years=51,
        design_life_years=50,
        keep_npv=1.0,
        candidate_base_npv=2.0,
        transition_cost=1.0,
        accessibility=0.0,
        accessibility_value_factor=0.0,
        evidence_status=EvidenceStatus.SYNTHETIC,
    )

    assert unit.asset_age_years > unit.design_life_years


def test_spatial_unit_contract_rejects_negative_age() -> None:
    with pytest.raises(ValidationError):
        SpatialUnitSpec(
            unit_id="u-001",
            area_sqm=100.0,
            current_use=LandUse.RESIDENTIAL,
            candidate_use=LandUse.RESEARCH,
            pin_kind=PinKind.SOFT,
            asset_age_years=-1,
            design_life_years=50,
            keep_npv=1.0,
            candidate_base_npv=2.0,
            transition_cost=1.0,
            accessibility=0.0,
            accessibility_value_factor=0.0,
            evidence_status=EvidenceStatus.SYNTHETIC,
        )
