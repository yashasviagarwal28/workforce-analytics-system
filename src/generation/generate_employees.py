"""Generate and validate synthetic employee records."""
from datetime import date
from pathlib import Path
import random
from typing import Set
from faker import Faker
import pandas as pd
from config.settings import (
    DEPARTMENTS, EARLIEST_HIRE_DATE, EMPLOYMENT_STATUSES,
    HOURLY_RATE_RANGES, JOB_TITLES_BY_DEPARTMENT,
    LATEST_HIRE_DATE, NUMBER_OF_EMPLOYEES, RANDOM_SEED,
)

def build_employee_id(employee_number: int) -> str:
    if employee_number < 1:
        raise ValueError("Employee number must be at least 1.")
    return f"EMP{employee_number:05d}"

def _get_rate_bounds(department_id: str):
    configured_range = HOURLY_RATE_RANGES[department_id]
    if isinstance(configured_range, dict):
        minimum = configured_range["minimum"]
        maximum = configured_range["maximum"]
    else:
        minimum, maximum = configured_range
    return float(minimum), float(maximum)

def generate_employees() -> pd.DataFrame:
    fake = Faker()
    fake.seed_instance(RANDOM_SEED)
    rng = random.Random(RANDOM_SEED)
    department_ids = [d["department_id"] for d in DEPARTMENTS]
    earliest = date.fromisoformat(EARLIEST_HIRE_DATE)
    latest = date.fromisoformat(LATEST_HIRE_DATE)
    rows = []
    for number in range(1, NUMBER_OF_EMPLOYEES + 1):
        department_id = rng.choice(department_ids)
        minimum_rate, maximum_rate = _get_rate_bounds(department_id)
        rows.append({
            "employee_id": build_employee_id(number),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "department_id": department_id,
            "job_title": rng.choice(JOB_TITLES_BY_DEPARTMENT[department_id]),
            "hire_date": fake.date_between(start_date=earliest, end_date=latest).isoformat(),
            "hourly_rate": round(rng.uniform(minimum_rate, maximum_rate), 2),
            "employment_status": rng.choices(
                population=EMPLOYMENT_STATUSES,
                weights=[0.92, 0.05, 0.03],
                k=1,
            )[0],
        })
    return pd.DataFrame(rows)

def validate_employees(employees_df: pd.DataFrame, valid_department_ids: Set[str]) -> None:
    required = {
        "employee_id", "first_name", "last_name", "department_id",
        "job_title", "hire_date", "hourly_rate", "employment_status",
    }
    missing = required - set(employees_df.columns)
    if missing:
        raise ValueError(f"Missing required employee columns: {sorted(missing)}")
    if len(employees_df) != NUMBER_OF_EMPLOYEES:
        raise ValueError("Employee count does not match NUMBER_OF_EMPLOYEES.")
    if employees_df["employee_id"].isna().any():
        raise ValueError("Employee IDs cannot be null.")
    if employees_df["employee_id"].duplicated().any():
        raise ValueError("Employee IDs must be unique.")
    unknown_departments = set(employees_df["department_id"].unique()) - valid_department_ids
    if unknown_departments:
        raise ValueError(f"Employees reference unknown departments: {sorted(unknown_departments)}")
    if (employees_df["hourly_rate"] <= 0).any():
        raise ValueError("Hourly rates must be positive.")
    unknown_statuses = set(employees_df["employment_status"].unique()) - set(EMPLOYMENT_STATUSES)
    if unknown_statuses:
        raise ValueError(f"Unknown employment statuses: {sorted(unknown_statuses)}")

def save_employees(employees_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    employees_df.to_csv(output_path, index=False)

def main() -> None:
    employees_df = generate_employees()
    valid_department_ids = {d["department_id"] for d in DEPARTMENTS}
    validate_employees(employees_df, valid_department_ids)
    output_path = Path("data/raw/employees.csv")
    save_employees(employees_df, output_path)
    print(f"Generated {len(employees_df)} employees.")
    print(f"Saved employee data to {output_path}")

if __name__ == "__main__":
    main()
