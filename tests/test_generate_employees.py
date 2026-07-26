"""Tests for employee generation."""

import pandas as pd
import pytest

from config.settings import (
    DEPARTMENTS,
    NUMBER_OF_EMPLOYEES,
)
from src.generation.generate_employees import (
    build_employee_id,
    generate_employees,
    validate_employees,
)


def get_valid_department_ids() -> set[str]:
    """Return configured department identifiers."""
    return {
        department["department_id"]
        for department in DEPARTMENTS
    }


def test_build_employee_id_formats_number() -> None:
    assert build_employee_id(1) == "EMP00001"
    assert build_employee_id(42) == "EMP00042"
    assert build_employee_id(999) == "EMP00999"


def test_build_employee_id_rejects_zero() -> None:
    with pytest.raises(
        ValueError,
        match="Employee number must be at least 1",
    ):
        build_employee_id(0)


def test_generate_employees_returns_expected_count() -> None:
    employees_df = generate_employees()

    assert len(employees_df) == NUMBER_OF_EMPLOYEES


def test_employee_ids_are_unique() -> None:
    employees_df = generate_employees()

    assert not employees_df["employee_id"].duplicated().any()


def test_all_employees_reference_valid_departments() -> None:
    employees_df = generate_employees()

    actual_department_ids = set(
        employees_df["department_id"].unique()
    )

    assert actual_department_ids.issubset(
        get_valid_department_ids()
    )


def test_generation_is_reproducible() -> None:
    first_df = generate_employees()
    second_df = generate_employees()

    pd.testing.assert_frame_equal(
        first_df,
        second_df,
    )


def test_validation_rejects_unknown_department() -> None:
    invalid_employees_df = generate_employees()

    invalid_employees_df.loc[
        0,
        "department_id",
    ] = "D999"

    with pytest.raises(
        ValueError,
        match="Employees reference unknown departments",
    ):
        validate_employees(
            invalid_employees_df,
            get_valid_department_ids(),
        )


def test_validation_rejects_duplicate_employee_ids() -> None:
    invalid_employees_df = generate_employees()

    invalid_employees_df.loc[
        1,
        "employee_id",
    ] = invalid_employees_df.loc[
        0,
        "employee_id",
    ]

    with pytest.raises(
        ValueError,
        match="Employee IDs must be unique",
    ):
        validate_employees(
            invalid_employees_df,
            get_valid_department_ids(),
        )