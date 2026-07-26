"""Generate the department dimension table for OpsPulse."""

from pathlib import Path

import pandas as pd

from config.settings import DEPARTMENTS


def generate_departments() -> pd.DataFrame:
    """Create and return the department table."""
    return pd.DataFrame(DEPARTMENTS)


def validate_departments(departments_df: pd.DataFrame) -> None:
    """Validate required department-table rules."""
    required_columns = {
        "department_id",
        "department_name",
        "operating_schedule",
    }

    missing_columns = required_columns - set(departments_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required department columns: {sorted(missing_columns)}"
        )

    if departments_df.empty:
        raise ValueError("Department table cannot be empty.")

    if departments_df["department_id"].isna().any():
        raise ValueError("Department IDs cannot be null.")

    if departments_df["department_id"].duplicated().any():
        raise ValueError("Department IDs must be unique.")

    if departments_df["department_name"].isna().any():
        raise ValueError("Department names cannot be null.")


def save_departments(
    departments_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save department data to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    departments_df.to_csv(output_path, index=False)


def main() -> None:
    """Generate, validate, and save the department table."""
    departments_df = generate_departments()
    validate_departments(departments_df)

    output_path = Path("data/raw/departments.csv")
    save_departments(departments_df, output_path)

    print(f"Generated {len(departments_df)} departments.")
    print(f"Saved department data to {output_path}")


if __name__ == "__main__":
    main()