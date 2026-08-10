import pytest

from urban_field_dynamics.campaign import run_campaign, run_campaign_parallel
from urban_field_dynamics.integrated import integrated_smoke_campaign


def test_world_parallel_campaign_matches_scalar_reference_exactly() -> None:
    spec = integrated_smoke_campaign(world_count=2)

    assert run_campaign_parallel(spec, max_workers=2) == run_campaign(spec)


def test_world_parallel_campaign_rejects_non_positive_worker_count() -> None:
    with pytest.raises(ValueError, match="max_workers must be positive"):
        run_campaign_parallel(integrated_smoke_campaign(world_count=1), max_workers=0)
