from urban_field_dynamics.spatial import (
    FocusZoneSpec,
    StylizedGridSpec,
    StylizedZoningSpec,
    generate_stylized_grid,
    generate_stylized_zoning,
)


def grid_spec(
    *,
    focus_zones: tuple[FocusZoneSpec, ...] | None = None,
    root_seed: int = 20260810,
) -> StylizedGridSpec:
    return StylizedGridSpec(
        root_seed=root_seed,
        rows=40,
        columns=30,
        cell_size_m=100.0,
        corridor_center_column=15,
        corridor_half_width_cells=2,
        focus_zones=(
            focus_zones
            if focus_zones is not None
            else (
                FocusZoneSpec(zone_id="focus-north", center_row=8, center_column=8, radius_cells=3),
                FocusZoneSpec(
                    zone_id="focus-central",
                    center_row=20,
                    center_column=15,
                    radius_cells=3,
                ),
                FocusZoneSpec(
                    zone_id="focus-south", center_row=32, center_column=22, radius_cells=3
                ),
            )
        ),
    )


def test_grid_generates_1200_unique_units_with_symmetric_four_neighbour_graph() -> None:
    grid = generate_stylized_grid(grid_spec())

    assert len(grid.units) == 1_200
    assert len({unit.spec.unit_id for unit in grid.units}) == 1_200
    by_id = {unit.spec.unit_id: unit for unit in grid.units}
    assert len(by_id["cell-r00-c00"].neighbor_ids) == 2
    assert len(by_id["cell-r20-c15"].neighbor_ids) == 4
    for unit in grid.units:
        for neighbor_id in unit.neighbor_ids:
            assert unit.spec.unit_id in by_id[neighbor_id].neighbor_ids


def test_focus_zones_are_disjoint_observer_labels() -> None:
    grid = generate_stylized_grid(grid_spec())
    labels = [unit.focus_zone_id for unit in grid.units if unit.focus_zone_id is not None]

    assert set(labels) == {"focus-north", "focus-central", "focus-south"}
    assert all(labels.count(zone_id) > 0 for zone_id in set(labels))
    assert sum(unit.is_corridor_observer for unit in grid.units) == 40 * 5


def test_observer_labels_do_not_change_initial_physical_or_economic_state() -> None:
    labelled = generate_stylized_grid(grid_spec())
    unlabelled = generate_stylized_grid(grid_spec(focus_zones=()))

    assert tuple(unit.spec for unit in labelled.units) == tuple(
        unit.spec for unit in unlabelled.units
    )
    assert tuple(unit.neighbor_ids for unit in labelled.units) == tuple(
        unit.neighbor_ids for unit in unlabelled.units
    )


def test_spatial_bootstrap_replays_exactly_and_seed_changes_only_initial_state() -> None:
    first = generate_stylized_grid(grid_spec())
    replay = generate_stylized_grid(grid_spec())
    alternative = generate_stylized_grid(grid_spec(root_seed=20260811))

    assert first == replay
    assert tuple(unit.spec.unit_id for unit in first.units) == tuple(
        unit.spec.unit_id for unit in alternative.units
    )
    assert tuple(unit.neighbor_ids for unit in first.units) == tuple(
        unit.neighbor_ids for unit in alternative.units
    )
    assert tuple(unit.spec for unit in first.units) != tuple(
        unit.spec for unit in alternative.units
    )


def test_1200_cells_aggregate_to_48_complete_symmetric_zones() -> None:
    spatial_grid = generate_stylized_grid(grid_spec())
    zoning = generate_stylized_zoning(
        spatial_grid,
        StylizedZoningSpec(block_rows=5, block_columns=5),
    )

    assert len(zoning.zones) == 48
    assert sum(len(zone.member_unit_ids) for zone in zoning.zones) == 1_200
    assert len({item for zone in zoning.zones for item in zone.member_unit_ids}) == 1_200
    by_id = {zone.zone_id: zone for zone in zoning.zones}
    assert len(by_id["zone-r00-c00"].neighbor_zone_ids) == 2
    assert len(by_id["zone-r04-c03"].neighbor_zone_ids) == 4
    for zone in zoning.zones:
        for neighbor_id in zone.neighbor_zone_ids:
            assert zone.zone_id in by_id[neighbor_id].neighbor_zone_ids
    assert any(zone.focus_zone_ids for zone in zoning.zones)
    assert any(zone.is_corridor_observer for zone in zoning.zones)
