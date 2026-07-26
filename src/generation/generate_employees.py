"""Generate synthetic employee records for OpsPulse."""

from datetime import date
from pathlib import Path
import random

from faker import Faker
import pandas as pd

from config.settings import (
    DEPARTMENTS,
    EARLIEST_HIRE_DATE,
    EMPLOYMENT_STATUSES,
    HOURLY_RATE_RANGES,
    JOB_TITLES_BY_DEPARTMENT,
    LATEST_HIRE_DATE,
    NUMBER_OF_EMPLOYEES,
    RANDOM_SEED,
)


def build_employee_id(employee_number: int) -> str:
    """Create a stable, readable employee identifier.

    Args:
        employee_number: Positive employee sequence number.

    Returns:
        An identifier such as EMP00001.

    Raises:
        ValueError: If the employee number is not positive.
    """
    if employee_number < 1:
        raise ValueError("Employee number must be at least 1.")

    return f"EMP{employee_number:05d}"


def generate_employees() -> pd.DataFrame:
    """Generate reproducible synthetic employee records.

    Returns:
        A DataFrame containing synthetic employees.
    """
    fake = Faker()
    fake.seed_instance(RANDOM_SEED)

    rng = random.Random(RANDOM_SEED)

    valid_department_ids = [
        department["department_id"]
        for department in DEPARTMENTS
    ]

    employees: list[dict[str, object]] = []

    earliest_hire_date = date.fromisoformat(EARLIEST_HIRE_DATE)
    latest_hire_date = date.fromisoformat(LATEST_HIRE_DATE)

    for employee_number in range(1, NUMBER_OF_EMPLOYEES + 1):
        department_id = rng.choice(valid_department_ids)

        job_title = rng.choice(
            JOB_TITLES_BY_DEPARTMENT[department_id]
        )

        rate_range = HOURLY_RATE_RANGES[department_id]

        hourly_rate = round(
            rng.uniform(
                rate_range["minimum"],
                rate_range["maximum"],
            ),
            2,
        )

        hire_date = fake.date_between(
            start_date=earliest_hire_date,
            end_date=latest_hire_date,
        )

        employment_status = rng.choices(
            population=EMPLOYMENT_STATUSES,
            weights=[0.92, 0.05, 0.03],
            k=1,
        )[0]

        employee = {
            "employee_id": build_employee_id(employee_number),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "department_id": department_id,
            "job_title": job_title,
            "hire_date": hire_date.isoformat(),
            "hourly_rate": hourly_rate,
            "employment_status": employment_status,
        }

        employees.append(employee)

    employees_df = pd.DataFrame(employees)

    return employees_df


def validate_employees(
    employees_df: pd.DataFrame,
    valid_department_ids: set[str],
) -> None:
    """Validate employee-table business and schema rules.

    Args:
        employees_df: Employee records to validate.
        valid_department_ids: Department IDs employees may reference.

    Raises:
        ValueError: If any validation rule is violated.
    """
    required_columns = {
        "employee_id",
        "first_name",
        "last_name",
        "department_id",
        "job_title",
        "hire_date",
        "hourly_rate",
        "employment_status",
    }

    missing_columns = required_columns - set(employees_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required employee columns: {sorted(missing_columns)}"
        )

    if len(employees_df) != NUMBER_OF_EMPLOYEES:
        raise ValueError(
            "Employee count does not match NUMBER_OF_EMPLOYEES."
        )

    if employees_df["employee_id"].isna().any():
        raise ValueError("Employee IDs cannot be null.")

    if employees_df["employee_id"].duplicated().any():
        raise ValueError("Employee IDs must be unique.")

    if employees_df["department_id"].isna().any():
        raise ValueError("Department IDs cannot be null.")

    referenced_department_ids = set(
        employees_df["department_id"].unique()
    )

    unknown_department_ids = (
        referenced_department_ids - valid_department_ids
    )

    if unknown_department_ids:
        raise ValueError(
            "Employees reference unknown departments: "
            f"{sorted(unknown_department_ids)}"
        )

    if employees_df["first_name"].isna().any():
        raise ValueError("First names cannot be null.")

    if employees_df["last_name"].isna().any():
        raise ValueError("Last names cannot be null.")

    if (employees_df["hourly_rate"] <= 0).any():
        raise ValueError("Hourly rates must be positive.")

    valid_statuses = set(EMPLOYMENT_STATUSES)

    unknown_statuses = (
        set(employees_df["employment_status"].unique())
        - valid_statuses
    )

    if unknown_statuses:
        raise ValueError(
            f"Unknown employment statuses: {sorted(unknown_statuses)}"
        )


def save_employees(
    employees_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save employee data to CSV.

    Args:
        employees_df: Validated employee data.
        output_path: Destination CSV path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    employees_df.to_csv(output_path, index=False)


def main() -> None:
    """Generate, validate, and save employee data."""
    employees_df = generate_employees()

    valid_department_ids = {
        department["department_id"]
        for department in DEPARTMENTS
    }

    validate_employees(
        employees_df,
        valid_department_ids,
    )

    output_path = Path("data/raw/employees.csv")

    save_employees(employees_df, output_path)

    print(f"Generated {len(employees_df)} employees.")
    print(f"Saved employee data to {output_path}")


if __name__ == "__main__":
    main()