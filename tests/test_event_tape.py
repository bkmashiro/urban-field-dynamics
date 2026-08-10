import numpy as np
import pytest

from urban_field_dynamics.event_tape import EventTapeSpec, generate_event_tape


def test_event_tape_replays_exactly_for_same_identity() -> None:
    spec = EventTapeSpec(root_seed=20260809, world_id=7, year=2030, mechanism="weather")

    first = generate_event_tape(spec, shape=(4, 3))
    second = generate_event_tape(spec, shape=(4, 3))

    np.testing.assert_array_equal(first, second)


def test_event_tape_changes_between_worlds() -> None:
    first = generate_event_tape(
        EventTapeSpec(root_seed=20260809, world_id=7, year=2030, mechanism="weather"),
        shape=(16,),
    )
    second = generate_event_tape(
        EventTapeSpec(root_seed=20260809, world_id=8, year=2030, mechanism="weather"),
        shape=(16,),
    )

    assert not np.array_equal(first, second)


def test_event_tape_changes_between_mechanisms() -> None:
    weather = generate_event_tape(
        EventTapeSpec(root_seed=20260809, world_id=7, year=2030, mechanism="weather"),
        shape=(16,),
    )
    relocation = generate_event_tape(
        EventTapeSpec(root_seed=20260809, world_id=7, year=2030, mechanism="relocation"),
        shape=(16,),
    )

    assert not np.array_equal(weather, relocation)


def test_entity_scoped_tape_is_independent_of_other_entity_membership() -> None:
    first = generate_event_tape(
        EventTapeSpec(
            root_seed=20260809,
            world_id=7,
            year=2030,
            mechanism="firm-expansion",
            entity_id="firm-aa",
        ),
        shape=(16,),
    )
    second = generate_event_tape(
        EventTapeSpec(
            root_seed=20260809,
            world_id=7,
            year=2030,
            mechanism="firm-expansion",
            entity_id="firm-bb",
        ),
        shape=(16,),
    )

    assert not np.array_equal(first, second)


def test_event_tape_spec_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError):
        EventTapeSpec(
            root_seed=1,
            world_id=0,
            year=2026,
            mechanism="weather",
            policy="P0",
        )


def test_event_tape_rejects_empty_or_non_positive_shape() -> None:
    spec = EventTapeSpec(root_seed=1, world_id=0, year=2026, mechanism="weather")

    with pytest.raises(ValueError, match="shape"):
        generate_event_tape(spec, shape=())
    with pytest.raises(ValueError, match="shape"):
        generate_event_tape(spec, shape=(4, 0))
