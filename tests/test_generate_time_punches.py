"""Tests for raw time-punch generation."""

from datetime import datetime
import random

import pandas as pd
import pytest

from config.settings import (
    MAXIMUM_ARRIVAL_OFFSET_MINUTES,
    MAXIMUM_DEPARTURE_OFFSET_MINUTES,
    MINIMUM_ARRIVAL_OFFSET_MINUTES,
    MINIMUM_DEPARTURE_OFFSET_MINUTES,
    RANDOM_SEED,
)
from src.generation.generate_employees import (
    generate_employees,
)
from src.generation.generate_shifts import (
    generate_shifts,
)
from src.generation.generate_time_punches import (
    build_actual_punch_times,
    build_punch_id,
    clip_value,
    generate_time_punches,
    validate_time_punches,
)


def build_test_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Generate the standard employee and shift test data."""
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    return employees_df, shifts_df


def test_build_punch_id_formats_number() -> None:
    assert build_punch_id(1) == "PCH0000001"
    assert build_punch_id(42) == "PCH0000042"


def test_build_punch_id_rejects_zero() -> None:
    with pytest.raises(
        ValueError,
        match="Punch number must be at least 1",
    ):
        build_punch_id(0)


def test_clip_value_preserves_in_range_value() -> None:
    assert clip_value(
        value=5,
        minimum=0,
        maximum=10,
    ) == 5


def test_clip_value_applies_minimum() -> None:
    assert clip_value(
        value=-5,
        minimum=0,
        maximum=10,
    ) == 0


def test_clip_value_applies_maximum() -> None:
    assert clip_value(
        value=15,
        minimum=0,
        maximum=10,
    ) == 10


def test_clip_value_rejects_invalid_range() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Minimum clip value cannot exceed maximum"
        ),
    ):
        clip_value(
            value=5,
            minimum=10,
            maximum=0,
        )


def test_actual_clock_out_occurs_after_clock_in() -> None:
    rng = random.Random(RANDOM_SEED)

    clock_in, clock_out = build_actual_punch_times(
        scheduled_start=datetime(
            2026,
            1,
            5,
            9,
            0,
        ),
        scheduled_end=datetime(
            2026,
            1,
            5,
            17,
            0,
        ),
        rng=rng,
    )

    assert clock_out > clock_in


def test_generate_time_punches_is_reproducible() -> None:
    _, shifts_df = build_test_data()

    first_df = generate_time_punches(
        shifts_df
    )

    second_df = generate_time_punches(
        shifts_df
    )

    pd.testing.assert_frame_equal(
        first_df,
        second_df,
    )


def test_all_punches_reference_valid_shifts() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    valid_shift_ids = set(
        shifts_df["shift_id"]
    )

    actual_shift_ids = set(
        punches_df["shift_id"]
    )

    assert actual_shift_ids.issubset(
        valid_shift_ids
    )


def test_punch_ids_are_unique() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    assert not punches_df[
        "punch_id"
    ].duplicated().any()


def test_every_shift_has_at_least_one_punch() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    shift_ids = set(
        shifts_df["shift_id"]
    )

    punched_shift_ids = set(
        punches_df["shift_id"]
    )

    assert shift_ids.issubset(
        punched_shift_ids
    )


def test_generation_contains_missing_clock_outs() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    assert punches_df[
        "clock_out"
    ].isna().any()


def test_generation_contains_duplicate_statuses() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    assert (
        punches_df["punch_status"]
        == "duplicate"
    ).any()


def test_arrival_offsets_stay_within_bounds() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    merged_df = punches_df.merge(
        shifts_df[
            [
                "shift_id",
                "scheduled_start",
            ]
        ],
        on="shift_id",
        how="left",
    )

    clock_in = pd.to_datetime(
        merged_df["clock_in"]
    )

    scheduled_start = pd.to_datetime(
        merged_df["scheduled_start"]
    )

    arrival_minutes = (
        clock_in - scheduled_start
    ).dt.total_seconds() / 60

    assert (
        arrival_minutes
        >= MINIMUM_ARRIVAL_OFFSET_MINUTES
    ).all()

    assert (
        arrival_minutes
        <= MAXIMUM_ARRIVAL_OFFSET_MINUTES
    ).all()


def test_departure_offsets_stay_within_bounds() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    complete_df = punches_df[
        punches_df["clock_out"].notna()
    ].copy()

    merged_df = complete_df.merge(
        shifts_df[
            [
                "shift_id",
                "scheduled_end",
            ]
        ],
        on="shift_id",
        how="left",
    )

    clock_out = pd.to_datetime(
        merged_df["clock_out"]
    )

    scheduled_end = pd.to_datetime(
        merged_df["scheduled_end"]
    )

    departure_minutes = (
        clock_out - scheduled_end
    ).dt.total_seconds() / 60

    assert (
        departure_minutes
        >= MINIMUM_DEPARTURE_OFFSET_MINUTES
    ).all()

    assert (
        departure_minutes
        <= MAXIMUM_DEPARTURE_OFFSET_MINUTES
    ).all()


def test_validation_rejects_unknown_shift() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    punches_df.loc[
        0,
        "shift_id",
    ] = "SFT9999999"

    with pytest.raises(
        ValueError,
        match="Punches reference unknown shifts",
    ):
        validate_time_punches(
            punches_df,
            shifts_df,
        )


def test_validation_rejects_employee_mismatch() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    original_employee = punches_df.loc[
        0,
        "employee_id",
    ]

    replacement_employee = next(
        employee_id
        for employee_id in shifts_df[
            "employee_id"
        ].unique()
        if employee_id != original_employee
    )

    punches_df.loc[
        0,
        "employee_id",
    ] = replacement_employee

    with pytest.raises(
        ValueError,
        match=(
            "Punch employee IDs must match shift employees"
        ),
    ):
        validate_time_punches(
            punches_df,
            shifts_df,
        )


def test_validation_rejects_end_before_start() -> None:
    _, shifts_df = build_test_data()

    punches_df = generate_time_punches(
        shifts_df
    )

    complete_index = punches_df[
        punches_df["clock_out"].notna()
    ].index[0]

    punches_df.loc[
        complete_index,
        "clock_out",
    ] = punches_df.loc[
        complete_index,
        "clock_in",
    ]

    with pytest.raises(
        ValueError,
        match="Clock-out must occur after clock-in",
    ):
        validate_time_punches(
            punches_df,
            shifts_df,
        )