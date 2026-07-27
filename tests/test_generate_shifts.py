"""Tests for scheduled-shift generation."""

from datetime import date

import pandas as pd
import pytest

from config.settings import STANDARD_SHIFT_HOURS
from src.generation.generate_employees import (
    generate_employees,
)
from src.generation.generate_shifts import (
    build_shift_datetimes,
    build_shift_id,
    generate_date_range,
    generate_shifts,
    is_eligible_shift_date,
    validate_shifts,
)


def test_build_shift_id_formats_number() -> None:
    assert build_shift_id(1) == "SFT0000001"
    assert build_shift_id(42) == "SFT0000042"


def test_build_shift_id_rejects_zero() -> None:
    with pytest.raises(
        ValueError,
        match="Shift number must be at least 1",
    ):
        build_shift_id(0)


def test_generate_date_range_is_inclusive() -> None:
    result = generate_date_range(
        date(2026, 1, 1),
        date(2026, 1, 3),
    )

    assert result == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]


def test_generate_date_range_rejects_reverse_range() -> None:
    with pytest.raises(
        ValueError,
        match="Shift end date cannot be before shift start date",
    ):
        generate_date_range(
            date(2026, 1, 3),
            date(2026, 1, 1),
        )


def test_weekday_schedule_accepts_monday() -> None:
    monday = date(2026, 1, 5)

    assert is_eligible_shift_date(
        monday,
        "Weekdays",
    )


def test_weekday_schedule_rejects_saturday() -> None:
    saturday = date(2026, 1, 3)

    assert not is_eligible_shift_date(
        saturday,
        "Weekdays",
    )


def test_twenty_four_seven_accepts_saturday() -> None:
    saturday = date(2026, 1, 3)

    assert is_eligible_shift_date(
        saturday,
        "24/7",
    )


def test_build_shift_datetimes_handles_overnight_shift() -> None:
    scheduled_start, scheduled_end = (
        build_shift_datetimes(
            date(2026, 1, 3),
            16,
        )
    )

    assert scheduled_start.isoformat() == (
        "2026-01-03T16:00:00"
    )

    assert scheduled_end.isoformat() == (
        "2026-01-04T00:00:00"
    )


def test_generate_shifts_is_reproducible() -> None:
    employees_df = generate_employees()

    first_df = generate_shifts(employees_df)
    second_df = generate_shifts(employees_df)

    pd.testing.assert_frame_equal(
        first_df,
        second_df,
    )


def test_all_shifts_reference_valid_employees() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    valid_employee_ids = set(
        employees_df["employee_id"]
    )

    actual_employee_ids = set(
        shifts_df["employee_id"]
    )

    assert actual_employee_ids.issubset(
        valid_employee_ids
    )


def test_inactive_employees_receive_no_shifts() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    inactive_employee_ids = set(
        employees_df.loc[
            employees_df["employment_status"] != "active",
            "employee_id",
        ]
    )

    scheduled_employee_ids = set(
        shifts_df["employee_id"]
    )

    assert inactive_employee_ids.isdisjoint(
        scheduled_employee_ids
    )


def test_weekday_shifts_do_not_start_on_weekends() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    weekday_shifts = shifts_df[
        shifts_df["shift_type"] == "Weekdays"
    ].copy()

    start_times = pd.to_datetime(
        weekday_shifts["scheduled_start"]
    )

    assert (start_times.dt.weekday < 5).all()


def test_shift_duration_matches_configuration() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    start_times = pd.to_datetime(
        shifts_df["scheduled_start"]
    )

    end_times = pd.to_datetime(
        shifts_df["scheduled_end"]
    )

    durations = (
        end_times - start_times
    ).dt.total_seconds() / 3600

    assert (
        durations == STANDARD_SHIFT_HOURS
    ).all()


def test_validation_rejects_unknown_employee() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    shifts_df.loc[
        0,
        "employee_id",
    ] = "EMP99999"

    with pytest.raises(
        ValueError,
        match="Shifts reference unknown employees",
    ):
        validate_shifts(
            shifts_df,
            employees_df,
        )


def test_validation_rejects_end_before_start() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    shifts_df.loc[
        0,
        "scheduled_end",
    ] = shifts_df.loc[
        0,
        "scheduled_start",
    ]

    with pytest.raises(
        ValueError,
        match="Scheduled end must occur after scheduled start",
    ):
        validate_shifts(
            shifts_df,
            employees_df,
        )