"""Generate and validate scheduled employee shifts."""
from datetime import date, datetime, time, timedelta
from pathlib import Path
import random
import pandas as pd
from config.settings import (
    DEPARTMENTS, OPERATIONS_SHIFT_START_HOURS, RANDOM_SEED,
    SHIFT_END_DATE, SHIFT_GENERATION_PROBABILITY, SHIFT_START_DATE,
    STANDARD_SHIFT_HOURS, WEEKDAY_SHIFT_START_HOURS,
)
from src.generation.generate_employees import generate_employees

def build_shift_id(shift_number: int) -> str:
    if shift_number < 1:
        raise ValueError("Shift number must be at least 1.")
    return f"SFT{shift_number:07d}"

def generate_date_range(start_date: date, end_date: date) -> list:
    if end_date < start_date:
        raise ValueError("Shift end date cannot be before shift start date.")
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates

def get_department_schedule_map() -> dict:
    return {d["department_id"]: d["operating_schedule"] for d in DEPARTMENTS}

def is_eligible_shift_date(shift_date: date, operating_schedule: str) -> bool:
    if operating_schedule == "24/7":
        return True
    if operating_schedule == "Weekdays":
        return shift_date.weekday() < 5
    raise ValueError(f"Unknown operating schedule: {operating_schedule}")

def choose_shift_start_hour(operating_schedule: str, rng: random.Random) -> int:
    if operating_schedule == "24/7":
        return rng.choice(OPERATIONS_SHIFT_START_HOURS)
    if operating_schedule == "Weekdays":
        return rng.choice(WEEKDAY_SHIFT_START_HOURS)
    raise ValueError(f"Unknown operating schedule: {operating_schedule}")

def build_shift_datetimes(shift_date: date, start_hour: int):
    scheduled_start = datetime.combine(shift_date, time(hour=start_hour))
    scheduled_end = scheduled_start + timedelta(hours=STANDARD_SHIFT_HOURS)
    return scheduled_start, scheduled_end

def generate_shifts(employees_df: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(RANDOM_SEED + 1)
    dates = generate_date_range(
        date.fromisoformat(SHIFT_START_DATE),
        date.fromisoformat(SHIFT_END_DATE),
    )
    schedule_map = get_department_schedule_map()
    rows = []
    shift_number = 1
    active = employees_df[employees_df["employment_status"] == "active"]
    for employee in active.itertuples(index=False):
        schedule = schedule_map[employee.department_id]
        probability = SHIFT_GENERATION_PROBABILITY[schedule]
        for shift_date in dates:
            if not is_eligible_shift_date(shift_date, schedule):
                continue
            if rng.random() >= probability:
                continue
            start_hour = choose_shift_start_hour(schedule, rng)
            scheduled_start, scheduled_end = build_shift_datetimes(shift_date, start_hour)
            rows.append({
                "shift_id": build_shift_id(shift_number),
                "employee_id": employee.employee_id,
                "department_id": employee.department_id,
                "scheduled_start": scheduled_start.isoformat(),
                "scheduled_end": scheduled_end.isoformat(),
                "shift_type": schedule,
            })
            shift_number += 1
    return pd.DataFrame(rows)

def validate_shifts(shifts_df: pd.DataFrame, employees_df: pd.DataFrame) -> None:
    required = {
        "shift_id", "employee_id", "department_id",
        "scheduled_start", "scheduled_end", "shift_type",
    }
    missing = required - set(shifts_df.columns)
    if missing:
        raise ValueError(f"Missing required shift columns: {sorted(missing)}")
    if shifts_df.empty:
        raise ValueError("Shift table cannot be empty.")
    if shifts_df["shift_id"].isna().any():
        raise ValueError("Shift IDs cannot be null.")
    if shifts_df["shift_id"].duplicated().any():
        raise ValueError("Shift IDs must be unique.")
    unknown = set(shifts_df["employee_id"]) - set(employees_df["employee_id"])
    if unknown:
        raise ValueError(f"Shifts reference unknown employees: {sorted(unknown)}")
    employee_department = dict(zip(employees_df["employee_id"], employees_df["department_id"]))
    mismatch = shifts_df.apply(
        lambda row: employee_department[row["employee_id"]] != row["department_id"],
        axis=1,
    )
    if mismatch.any():
        raise ValueError("Shift department IDs must match employee departments.")
    scheduled_start = pd.to_datetime(shifts_df["scheduled_start"], errors="coerce")
    scheduled_end = pd.to_datetime(shifts_df["scheduled_end"], errors="coerce")
    if scheduled_start.isna().any():
        raise ValueError("Scheduled start values must be valid timestamps.")
    if scheduled_end.isna().any():
        raise ValueError("Scheduled end values must be valid timestamps.")
    if (scheduled_end <= scheduled_start).any():
        raise ValueError("Scheduled end must occur after scheduled start.")
    durations = (scheduled_end - scheduled_start).dt.total_seconds() / 3600
    if (durations != STANDARD_SHIFT_HOURS).any():
        raise ValueError("Every scheduled shift must have the standard duration.")

def save_shifts(shifts_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shifts_df.to_csv(output_path, index=False)

def main() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)
    validate_shifts(shifts_df, employees_df)
    output_path = Path("data/raw/shifts.csv")
    save_shifts(shifts_df, output_path)
    print(f"Generated {len(shifts_df)} shifts.")
    print(f"Saved shift data to {output_path}")

if __name__ == "__main__":
    main()
