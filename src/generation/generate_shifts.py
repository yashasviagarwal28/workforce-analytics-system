"""Generate scheduled employee shifts for the workforce system."""

from datetime import date, datetime, time, timedelta
from pathlib import Path
import random

import pandas as pd

from config.settings import (
    DEPARTMENTS,
    OPERATIONS_SHIFT_START_HOURS,
    RANDOM_SEED,
    SHIFT_END_DATE,
    SHIFT_GENERATION_PROBABILITY,
    SHIFT_START_DATE,
    STANDARD_SHIFT_HOURS,
    WEEKDAY_SHIFT_START_HOURS,
)
from src.generation.generate_employees import generate_employees


def build_shift_id(shift_number: int) -> str:
    """Create a stable, readable shift identifier.

    Args:
        shift_number: Positive shift sequence number.

    Returns:
        An identifier such as SFT0000001.

    Raises:
        ValueError: If the shift number is not positive.
    """
    if shift_number < 1:
        raise ValueError("Shift number must be at least 1.")

    return f"SFT{shift_number:07d}"


def generate_date_range(
    start_date: date,
    end_date: date,
) -> list[date]:
    """Create an inclusive list of dates.

    Args:
        start_date: First date in the range.
        end_date: Final date in the range.

    Returns:
        Every date from start_date through end_date.

    Raises:
        ValueError: If the end date is before the start date.
    """
    if end_date < start_date:
        raise ValueError(
            "Shift end date cannot be before shift start date."
        )

    dates: list[date] = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates


def get_department_schedule_map() -> dict[str, str]:
    """Map department IDs to their operating schedules."""
    return {
        department["department_id"]: department["operating_schedule"]
        for department in DEPARTMENTS
    }


def is_eligible_shift_date(
    shift_date: date,
    operating_schedule: str,
) -> bool:
    """Determine whether a department may schedule a shift on a date.

    Args:
        shift_date: Candidate shift date.
        operating_schedule: Department schedule category.

    Returns:
        True when the date is eligible.
    """
    if operating_schedule == "24/7":
        return True

    if operating_schedule == "Weekdays":
        return shift_date.weekday() < 5

    raise ValueError(
        f"Unknown operating schedule: {operating_schedule}"
    )


def choose_shift_start_hour(
    operating_schedule: str,
    rng: random.Random,
) -> int:
    """Choose a valid shift-start hour for a department schedule."""
    if operating_schedule == "24/7":
        return rng.choice(OPERATIONS_SHIFT_START_HOURS)

    if operating_schedule == "Weekdays":
        return rng.choice(WEEKDAY_SHIFT_START_HOURS)

    raise ValueError(
        f"Unknown operating schedule: {operating_schedule}"
    )


def build_shift_datetimes(
    shift_date: date,
    start_hour: int,
) -> tuple[datetime, datetime]:
    """Create start and end datetimes for a standard shift.

    Args:
        shift_date: Calendar date on which the shift starts.
        start_hour: Hour at which the shift begins.

    Returns:
        Scheduled start and scheduled end datetimes.
    """
    scheduled_start = datetime.combine(
        shift_date,
        time(hour=start_hour),
    )

    scheduled_end = scheduled_start + timedelta(
        hours=STANDARD_SHIFT_HOURS
    )

    return scheduled_start, scheduled_end


def generate_shifts(
    employees_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate reproducible scheduled shifts for active employees.

    Args:
        employees_df: Employee records used to create shifts.

    Returns:
        A DataFrame containing scheduled shifts.
    """
    rng = random.Random(RANDOM_SEED + 1)

    start_date = date.fromisoformat(SHIFT_START_DATE)
    end_date = date.fromisoformat(SHIFT_END_DATE)

    shift_dates = generate_date_range(
        start_date,
        end_date,
    )

    department_schedule_map = get_department_schedule_map()

    shifts: list[dict[str, object]] = []
    shift_number = 1

    active_employees_df = employees_df[
        employees_df["employment_status"] == "active"
    ]

    for employee in active_employees_df.itertuples(index=False):
        operating_schedule = department_schedule_map[
            employee.department_id
        ]

        generation_probability = (
            SHIFT_GENERATION_PROBABILITY[operating_schedule]
        )

        for shift_date in shift_dates:
            if not is_eligible_shift_date(
                shift_date,
                operating_schedule,
            ):
                continue

            should_generate_shift = (
                rng.random() < generation_probability
            )

            if not should_generate_shift:
                continue

            start_hour = choose_shift_start_hour(
                operating_schedule,
                rng,
            )

            scheduled_start, scheduled_end = (
                build_shift_datetimes(
                    shift_date,
                    start_hour,
                )
            )

            shift = {
                "shift_id": build_shift_id(shift_number),
                "employee_id": employee.employee_id,
                "department_id": employee.department_id,
                "scheduled_start": scheduled_start.isoformat(),
                "scheduled_end": scheduled_end.isoformat(),
                "shift_type": operating_schedule,
            }

            shifts.append(shift)
            shift_number += 1

    return pd.DataFrame(shifts)


def validate_shifts(
    shifts_df: pd.DataFrame,
    employees_df: pd.DataFrame,
) -> None:
    """Validate shift schema and business rules.

    Args:
        shifts_df: Generated shift records.
        employees_df: Employee records referenced by shifts.

    Raises:
        ValueError: If any shift rule is violated.
    """
    required_columns = {
        "shift_id",
        "employee_id",
        "department_id",
        "scheduled_start",
        "scheduled_end",
        "shift_type",
    }

    missing_columns = required_columns - set(shifts_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required shift columns: {sorted(missing_columns)}"
        )

    if shifts_df.empty:
        raise ValueError("Shift table cannot be empty.")

    if shifts_df["shift_id"].isna().any():
        raise ValueError("Shift IDs cannot be null.")

    if shifts_df["shift_id"].duplicated().any():
        raise ValueError("Shift IDs must be unique.")

    valid_employee_ids = set(
        employees_df["employee_id"]
    )

    referenced_employee_ids = set(
        shifts_df["employee_id"]
    )

    unknown_employee_ids = (
        referenced_employee_ids - valid_employee_ids
    )

    if unknown_employee_ids:
        raise ValueError(
            "Shifts reference unknown employees: "
            f"{sorted(unknown_employee_ids)}"
        )

    employee_department_map = dict(
        zip(
            employees_df["employee_id"],
            employees_df["department_id"],
        )
    )

    mismatched_departments = shifts_df[
        shifts_df.apply(
            lambda row: employee_department_map[
                row["employee_id"]
            ] != row["department_id"],
            axis=1,
        )
    ]

    if not mismatched_departments.empty:
        raise ValueError(
            "Shift department IDs must match employee departments."
        )

    scheduled_start = pd.to_datetime(
        shifts_df["scheduled_start"],
        errors="coerce",
    )

    scheduled_end = pd.to_datetime(
        shifts_df["scheduled_end"],
        errors="coerce",
    )

    if scheduled_start.isna().any():
        raise ValueError(
            "Scheduled start values must be valid timestamps."
        )

    if scheduled_end.isna().any():
        raise ValueError(
            "Scheduled end values must be valid timestamps."
        )

    if (scheduled_end <= scheduled_start).any():
        raise ValueError(
            "Scheduled end must occur after scheduled start."
        )

    shift_durations = (
        scheduled_end - scheduled_start
    ).dt.total_seconds() / 3600

    if (
        shift_durations != STANDARD_SHIFT_HOURS
    ).any():
        raise ValueError(
            "Every scheduled shift must have the standard duration."
        )


def save_shifts(
    shifts_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save scheduled shifts to CSV."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shifts_df.to_csv(
        output_path,
        index=False,
    )


def main() -> None:
    """Generate, validate, and save employee shifts."""
    employees_df = generate_employees()

    shifts_df = generate_shifts(employees_df)

    validate_shifts(
        shifts_df,
        employees_df,
    )

    output_path = Path("data/raw/shifts.csv")

    save_shifts(
        shifts_df,
        output_path,
    )

    print(f"Generated {len(shifts_df)} shifts.")
    print(f"Saved shift data to {output_path}")


if __name__ == "__main__":
    main()