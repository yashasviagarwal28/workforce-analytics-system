"""Generate raw employee time-punch records."""

from datetime import datetime, timedelta
from pathlib import Path

import random

import pandas as pd

from config.settings import (
    ARRIVAL_MEAN_MINUTES,
    ARRIVAL_STANDARD_DEVIATION_MINUTES,
    DEPARTURE_MEAN_MINUTES,
    DEPARTURE_STANDARD_DEVIATION_MINUTES,
    DUPLICATE_PUNCH_PROBABILITY,
    MAXIMUM_ARRIVAL_OFFSET_MINUTES,
    MAXIMUM_DEPARTURE_OFFSET_MINUTES,
    MINIMUM_ARRIVAL_OFFSET_MINUTES,
    MINIMUM_DEPARTURE_OFFSET_MINUTES,
    MISSING_CLOCK_OUT_PROBABILITY,
    RANDOM_SEED,
)
from src.generation.generate_employees import generate_employees
from src.generation.generate_shifts import generate_shifts


PUNCH_COLUMNS = [
    "punch_id",
    "shift_id",
    "employee_id",
    "department_id",
    "clock_in",
    "clock_out",
    "punch_status",
]


def build_punch_id(punch_number: int) -> str:
    """Create a stable, readable punch identifier.

    Args:
        punch_number: Positive punch sequence number.

    Returns:
        An identifier such as PCH0000001.

    Raises:
        ValueError: If punch_number is not positive.
    """
    if punch_number < 1:
        raise ValueError("Punch number must be at least 1.")

    return f"PCH{punch_number:07d}"


def clip_value(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Restrict a numeric value to an inclusive range.

    Args:
        value: Original numeric value.
        minimum: Lowest allowed value.
        maximum: Highest allowed value.

    Returns:
        The clipped value.

    Raises:
        ValueError: If minimum is greater than maximum.
    """
    if minimum > maximum:
        raise ValueError(
            "Minimum clip value cannot exceed maximum."
        )

    return max(
        minimum,
        min(value, maximum),
    )


def generate_arrival_offset(
    rng: random.Random,
) -> int:
    """Generate a realistic arrival offset in minutes."""
    raw_offset = rng.gauss(
        ARRIVAL_MEAN_MINUTES,
        ARRIVAL_STANDARD_DEVIATION_MINUTES,
    )

    clipped_offset = clip_value(
        raw_offset,
        MINIMUM_ARRIVAL_OFFSET_MINUTES,
        MAXIMUM_ARRIVAL_OFFSET_MINUTES,
    )

    return round(clipped_offset)


def generate_departure_offset(
    rng: random.Random,
) -> int:
    """Generate a realistic departure offset in minutes."""
    raw_offset = rng.gauss(
        DEPARTURE_MEAN_MINUTES,
        DEPARTURE_STANDARD_DEVIATION_MINUTES,
    )

    clipped_offset = clip_value(
        raw_offset,
        MINIMUM_DEPARTURE_OFFSET_MINUTES,
        MAXIMUM_DEPARTURE_OFFSET_MINUTES,
    )

    return round(clipped_offset)


def build_actual_punch_times(
    scheduled_start: datetime,
    scheduled_end: datetime,
    rng: random.Random,
) -> tuple[datetime, datetime]:
    """Generate actual clock-in and clock-out timestamps.

    Args:
        scheduled_start: Expected shift start.
        scheduled_end: Expected shift end.
        rng: Controlled random generator.

    Returns:
        Actual clock-in and clock-out timestamps.
    """
    arrival_offset = generate_arrival_offset(rng)
    departure_offset = generate_departure_offset(rng)

    clock_in = scheduled_start + timedelta(
        minutes=arrival_offset
    )

    clock_out = scheduled_end + timedelta(
        minutes=departure_offset
    )

    if clock_out <= clock_in:
        clock_out = clock_in + timedelta(minutes=1)

    return clock_in, clock_out


def generate_time_punches(
    shifts_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate reproducible raw time-punch data.

    Args:
        shifts_df: Scheduled shifts used as punch foundations.

    Returns:
        A DataFrame containing raw time-punch records.
    """
    rng = random.Random(RANDOM_SEED + 2)

    punches: list[dict[str, object]] = []
    punch_number = 1

    for shift in shifts_df.itertuples(index=False):
        scheduled_start = datetime.fromisoformat(
            shift.scheduled_start
        )

        scheduled_end = datetime.fromisoformat(
            shift.scheduled_end
        )

        clock_in, clock_out = build_actual_punch_times(
            scheduled_start,
            scheduled_end,
            rng,
        )

        is_missing_clock_out = (
            rng.random()
            < MISSING_CLOCK_OUT_PROBABILITY
        )

        punch_status = "complete"
        clock_out_value: str | None

        if is_missing_clock_out:
            clock_out_value = None
            punch_status = "missing_clock_out"
        else:
            clock_out_value = clock_out.isoformat()

        punch = {
            "punch_id": build_punch_id(punch_number),
            "shift_id": shift.shift_id,
            "employee_id": shift.employee_id,
            "department_id": shift.department_id,
            "clock_in": clock_in.isoformat(),
            "clock_out": clock_out_value,
            "punch_status": punch_status,
        }

        punches.append(punch)
        punch_number += 1

        should_duplicate = (
            rng.random()
            < DUPLICATE_PUNCH_PROBABILITY
        )

        if should_duplicate:
            duplicate_punch = punch.copy()

            duplicate_punch["punch_id"] = build_punch_id(
                punch_number
            )

            duplicate_punch["punch_status"] = "duplicate"

            punches.append(duplicate_punch)
            punch_number += 1

    return pd.DataFrame(
        punches,
        columns=PUNCH_COLUMNS,
    )


def validate_time_punches(
    punches_df: pd.DataFrame,
    shifts_df: pd.DataFrame,
) -> None:
    """Validate raw time-punch schema and relationships.

    Raw validation permits missing clock-out values and duplicated
    shift references because these are deliberately generated noise.

    Args:
        punches_df: Raw punch records.
        shifts_df: Valid shift records.

    Raises:
        ValueError: If a structural rule is violated.
    """
    required_columns = set(PUNCH_COLUMNS)

    missing_columns = (
        required_columns - set(punches_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required punch columns: "
            f"{sorted(missing_columns)}"
        )

    if punches_df.empty:
        raise ValueError(
            "Time-punch table cannot be empty."
        )

    if punches_df["punch_id"].isna().any():
        raise ValueError(
            "Punch IDs cannot be null."
        )

    if punches_df["punch_id"].duplicated().any():
        raise ValueError(
            "Punch IDs must be unique."
        )

    valid_shift_ids = set(
        shifts_df["shift_id"]
    )

    referenced_shift_ids = set(
        punches_df["shift_id"]
    )

    unknown_shift_ids = (
        referenced_shift_ids - valid_shift_ids
    )

    if unknown_shift_ids:
        raise ValueError(
            "Punches reference unknown shifts: "
            f"{sorted(unknown_shift_ids)}"
        )

    valid_employee_ids = set(
        shifts_df["employee_id"]
    )

    referenced_employee_ids = set(
        punches_df["employee_id"]
    )

    unknown_employee_ids = (
        referenced_employee_ids - valid_employee_ids
    )

    if unknown_employee_ids:
        raise ValueError(
            "Punches reference unknown employees: "
            f"{sorted(unknown_employee_ids)}"
        )

    shift_employee_map = dict(
        zip(
            shifts_df["shift_id"],
            shifts_df["employee_id"],
        )
    )

    employee_mismatches = punches_df[
        punches_df.apply(
            lambda row: shift_employee_map[
                row["shift_id"]
            ] != row["employee_id"],
            axis=1,
        )
    ]

    if not employee_mismatches.empty:
        raise ValueError(
            "Punch employee IDs must match shift employees."
        )

    shift_department_map = dict(
        zip(
            shifts_df["shift_id"],
            shifts_df["department_id"],
        )
    )

    department_mismatches = punches_df[
        punches_df.apply(
            lambda row: shift_department_map[
                row["shift_id"]
            ] != row["department_id"],
            axis=1,
        )
    ]

    if not department_mismatches.empty:
        raise ValueError(
            "Punch department IDs must match shift departments."
        )

    parsed_clock_in = pd.to_datetime(
        punches_df["clock_in"],
        errors="coerce",
    )

    if parsed_clock_in.isna().any():
        raise ValueError(
            "Clock-in values must be valid timestamps."
        )

    non_null_clock_out = punches_df[
        punches_df["clock_out"].notna()
    ].copy()

    parsed_clock_out = pd.to_datetime(
        non_null_clock_out["clock_out"],
        errors="coerce",
    )

    if parsed_clock_out.isna().any():
        raise ValueError(
            "Non-null clock-out values must be valid timestamps."
        )

    matching_clock_in = pd.to_datetime(
        non_null_clock_out["clock_in"],
        errors="coerce",
    )

    if (
        parsed_clock_out <= matching_clock_in
    ).any():
        raise ValueError(
            "Clock-out must occur after clock-in."
        )

    valid_statuses = {
        "complete",
        "missing_clock_out",
        "duplicate",
    }

    unknown_statuses = (
        set(punches_df["punch_status"])
        - valid_statuses
    )

    if unknown_statuses:
        raise ValueError(
            "Unknown punch statuses: "
            f"{sorted(unknown_statuses)}"
        )


def save_time_punches(
    punches_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save raw time-punch data to CSV."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    punches_df.to_csv(
        output_path,
        index=False,
    )


def main() -> None:
    """Generate, validate, and save time-punch data."""
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)

    punches_df = generate_time_punches(
        shifts_df
    )

    validate_time_punches(
        punches_df,
        shifts_df,
    )

    output_path = Path(
        "data/raw/time_punches.csv"
    )

    save_time_punches(
        punches_df,
        output_path,
    )

    print(
        f"Generated {len(punches_df)} time punches."
    )

    missing_count = (
        punches_df["clock_out"].isna().sum()
    )

    duplicate_count = (
        punches_df["punch_status"]
        .eq("duplicate")
        .sum()
    )

    print(
        f"Missing clock-outs: {missing_count}"
    )

    print(
        f"Duplicate records: {duplicate_count}"
    )

    print(
        f"Saved time-punch data to {output_path}"
    )


if __name__ == "__main__":
    main()