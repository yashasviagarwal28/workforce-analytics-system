"""Tests for department generation."""

import pandas as pd
import pytest

from src.generation.generate_departments import (
    generate_departments,
    validate_departments,
)


def test_generate_departments_returns_dataframe() -> None:
    departments_df = generate_departments()

    assert isinstance(departments_df, pd.DataFrame)


def test_department_ids_are_unique() -> None:
    departments_df = generate_departments()

    assert not departments_df["department_id"].duplicated().any()


def test_department_table_is_not_empty() -> None:
    departments_df = generate_departments()

    assert not departments_df.empty


def test_validation_rejects_duplicate_department_ids() -> None:
    invalid_departments_df = pd.DataFrame(
        [
            {
                "department_id": "D001",
                "department_name": "Operations",
                "operating_schedule": "24/7",
            },
            {
                "department_id": "D001",
                "department_name": "Finance",
                "operating_schedule": "Weekdays",
            },
        ]
    )

    with pytest.raises(
        ValueError,
        match="Department IDs must be unique",
    ):
        validate_departments(invalid_departments_df)