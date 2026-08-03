"""Generate and validate raw time-punch records."""
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import Optional
import pandas as pd
from config.settings import (
    ARRIVAL_MEAN_MINUTES, ARRIVAL_STANDARD_DEVIATION_MINUTES,
    DEPARTURE_MEAN_MINUTES, DEPARTURE_STANDARD_DEVIATION_MINUTES,
    DUPLICATE_PUNCH_PROBABILITY, MAXIMUM_ARRIVAL_OFFSET_MINUTES,
    MAXIMUM_DEPARTURE_OFFSET_MINUTES, MINIMUM_ARRIVAL_OFFSET_MINUTES,
    MINIMUM_DEPARTURE_OFFSET_MINUTES, MISSING_CLOCK_OUT_PROBABILITY,
    RANDOM_SEED,
)
from src.generation.generate_employees import generate_employees
from src.generation.generate_shifts import generate_shifts

PUNCH_COLUMNS = [
    "punch_id", "shift_id", "employee_id", "department_id",
    "clock_in", "clock_out", "punch_status",
]

def build_punch_id(punch_number: int) -> str:
    if punch_number < 1:
        raise ValueError("Punch number must be at least 1.")
    return f"PCH{punch_number:07d}"

def clip_value(value: float, minimum: float, maximum: float) -> float:
    if minimum > maximum:
        raise ValueError("Minimum clip value cannot exceed maximum.")
    return max(minimum, min(value, maximum))

def generate_arrival_offset(rng: random.Random) -> int:
    value = rng.gauss(ARRIVAL_MEAN_MINUTES, ARRIVAL_STANDARD_DEVIATION_MINUTES)
    return round(clip_value(value, MINIMUM_ARRIVAL_OFFSET_MINUTES, MAXIMUM_ARRIVAL_OFFSET_MINUTES))

def generate_departure_offset(rng: random.Random) -> int:
    value = rng.gauss(DEPARTURE_MEAN_MINUTES, DEPARTURE_STANDARD_DEVIATION_MINUTES)
    return round(clip_value(value, MINIMUM_DEPARTURE_OFFSET_MINUTES, MAXIMUM_DEPARTURE_OFFSET_MINUTES))

def build_actual_punch_times(scheduled_start: datetime, scheduled_end: datetime, rng: random.Random):
    clock_in = scheduled_start + timedelta(minutes=generate_arrival_offset(rng))
    clock_out = scheduled_end + timedelta(minutes=generate_departure_offset(rng))
    if clock_out <= clock_in:
        clock_out = clock_in + timedelta(minutes=1)
    return clock_in, clock_out

def generate_time_punches(shifts_df: pd.DataFrame) -> pd.DataFrame:
    rng = random.Random(RANDOM_SEED + 2)
    rows = []
    punch_number = 1
    for shift in shifts_df.itertuples(index=False):
        scheduled_start = datetime.fromisoformat(shift.scheduled_start)
        scheduled_end = datetime.fromisoformat(shift.scheduled_end)
        clock_in, clock_out = build_actual_punch_times(scheduled_start, scheduled_end, rng)
        missing = rng.random() < MISSING_CLOCK_OUT_PROBABILITY
        clock_out_value: Optional[str] = None if missing else clock_out.isoformat()
        status = "missing_clock_out" if missing else "complete"
        row = {
            "punch_id": build_punch_id(punch_number),
            "shift_id": shift.shift_id,
            "employee_id": shift.employee_id,
            "department_id": shift.department_id,
            "clock_in": clock_in.isoformat(),
            "clock_out": clock_out_value,
            "punch_status": status,
        }
        rows.append(row)
        punch_number += 1
        if rng.random() < DUPLICATE_PUNCH_PROBABILITY:
            duplicate = row.copy()
            duplicate["punch_id"] = build_punch_id(punch_number)
            duplicate["punch_status"] = "duplicate"
            rows.append(duplicate)
            punch_number += 1
    return pd.DataFrame(rows, columns=PUNCH_COLUMNS)

def validate_time_punches(punches_df: pd.DataFrame, shifts_df: pd.DataFrame) -> None:
    required = set(PUNCH_COLUMNS)
    missing = required - set(punches_df.columns)
    if missing:
        raise ValueError(f"Missing required punch columns: {sorted(missing)}")
    if punches_df.empty:
        raise ValueError("Time-punch table cannot be empty.")
    if punches_df["punch_id"].isna().any():
        raise ValueError("Punch IDs cannot be null.")
    if punches_df["punch_id"].duplicated().any():
        raise ValueError("Punch IDs must be unique.")
    unknown_shifts = set(punches_df["shift_id"]) - set(shifts_df["shift_id"])
    if unknown_shifts:
        raise ValueError(f"Punches reference unknown shifts: {sorted(unknown_shifts)}")
    shift_employee = dict(zip(shifts_df["shift_id"], shifts_df["employee_id"]))
    employee_mismatch = punches_df.apply(
        lambda row: shift_employee[row["shift_id"]] != row["employee_id"], axis=1
    )
    if employee_mismatch.any():
        raise ValueError("Punch employee IDs must match shift employees.")
    shift_department = dict(zip(shifts_df["shift_id"], shifts_df["department_id"]))
    department_mismatch = punches_df.apply(
        lambda row: shift_department[row["shift_id"]] != row["department_id"], axis=1
    )
    if department_mismatch.any():
        raise ValueError("Punch department IDs must match shift departments.")
    parsed_clock_in = pd.to_datetime(punches_df["clock_in"], errors="coerce")
    if parsed_clock_in.isna().any():
        raise ValueError("Clock-in values must be valid timestamps.")
    complete = punches_df[punches_df["clock_out"].notna()].copy()
    parsed_clock_out = pd.to_datetime(complete["clock_out"], errors="coerce")
    matching_clock_in = pd.to_datetime(complete["clock_in"], errors="coerce")
    if parsed_clock_out.isna().any():
        raise ValueError("Non-null clock-out values must be valid timestamps.")
    if (parsed_clock_out <= matching_clock_in).any():
        raise ValueError("Clock-out must occur after clock-in.")
    valid_statuses = {"complete", "missing_clock_out", "duplicate"}
    unknown_statuses = set(punches_df["punch_status"]) - valid_statuses
    if unknown_statuses:
        raise ValueError(f"Unknown punch statuses: {sorted(unknown_statuses)}")

def save_time_punches(punches_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    punches_df.to_csv(output_path, index=False)

def main() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)
    punches_df = generate_time_punches(shifts_df)
    validate_time_punches(punches_df, shifts_df)
    output_path = Path("data/raw/time_punches.csv")
    save_time_punches(punches_df, output_path)
    print(f"Generated {len(punches_df)} time punches.")
    print(f"Missing clock-outs: {int(punches_df['clock_out'].isna().sum())}")
    print(f"Duplicate records: {int(punches_df['punch_status'].eq('duplicate').sum())}")
    print(f"Saved time-punch data to {output_path}")

if __name__ == "__main__":
    main()
