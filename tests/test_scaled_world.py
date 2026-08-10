from urban_field_dynamics.morphology import observe_world_morphology
from urban_field_dynamics.schedule import ScheduleConfig
from urban_field_dynamics.spatial import FocusZoneSpec, StylizedGridSpec, generate_stylized_grid
from urban_field_dynamics.world import PolicySpec, WorldRunConfig, run_world


def grid():
    return generate_stylized_grid(
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


def run(policy: PolicySpec):
    spatial_grid = grid()
    result = run_world(
        WorldRunConfig(
            root_seed=20260810,
            world_id=3,
            schedule=ScheduleConfig(start_year=2026, end_year=2026, replan_years={2026}),
            units=tuple(unit.spec for unit in spatial_grid.units),
            policy=policy,
            development_shock_scale=8.0,
        )
    )
    return spatial_grid, result


def test_1200_unit_world_runs_with_matched_policy_tape_and_morphology() -> None:
    baseline_grid, baseline = run(PolicySpec(policy_id="p0", intervention_year=2026))
    investment_grid, investment = run(
        PolicySpec(
            policy_id="p1",
            intervention_year=2026,
            accessibility_delta=0.1,
        )
    )

    assert baseline_grid == investment_grid
    assert len(baseline.final_uses) == 1_200
    assert baseline.development_shocks == investment.development_shocks
    assert baseline.final_accessibility != investment.final_accessibility
    observation = observe_world_morphology(investment, investment_grid)
    assert 0.0 <= observation.redevelopment_share <= 1.0
    assert 0.0 <= observation.normalized_land_use_entropy <= 1.0
    assert 0.0 <= observation.adjacency_mixing_rate <= 1.0
