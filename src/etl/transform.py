"""Clean, validate, and enrich extracted workforce data."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple

import numpy as np
import pandas as pd


class TransformationError(RuntimeError):
    """Raised when transformed data violates required invariants."""


PUNCH_DEDUP_KEYS = [
    "shift_id",
    "employee_id",
    "department_id",
    "clock_in",
    "clock_out",
]


def _require_columns(df: pd.DataFrame, required: set, table_name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise TransformationError(
            f"{table_name} is missing required columns: {sorted(missing)}"
        )


def _parse_datetime(series: pd.Series, name: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if parsed.isna().any():
        bad_count = int(parsed.isna().sum())
        raise TransformationError(f"{name} contains {bad_count} invalid timestamps")
    return parsed


def _money(value: float) -> float:
    return float(
        Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def transform_departments(df: pd.DataFrame) -> pd.DataFrame:
    required = {"department_id", "department_name", "operating_schedule"}
    _require_columns(df, required, "departments")
    out = df.copy()
    if out["department_id"].isna().any() or out["department_id"].duplicated().any():
        raise TransformationError("department_id must be non-null and unique")
    return out.sort_values("department_id").reset_index(drop=True)


def transform_employees(
    df: pd.DataFrame,
    departments: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "employee_id",
        "first_name",
        "last_name",
        "department_id",
        "job_title",
        "hire_date",
        "hourly_rate",
        "employment_status",
    }
    _require_columns(df, required, "employees")
    out = df.copy()
    out["hire_date"] = _parse_datetime(out["hire_date"], "hire_date").dt.date
    out["hourly_rate"] = pd.to_numeric(out["hourly_rate"], errors="coerce")
    if out["hourly_rate"].isna().any() or (out["hourly_rate"] <= 0).any():
        raise TransformationError("hourly_rate must be numeric and positive")
    if out["employee_id"].isna().any() or out["employee_id"].duplicated().any():
        raise TransformationError("employee_id must be non-null and unique")
    valid_departments = set(departments["department_id"])
    unknown = set(out["department_id"]) - valid_departments
    if unknown:
        raise TransformationError(f"employees reference unknown departments: {sorted(unknown)}")
    return out.sort_values("employee_id").reset_index(drop=True)


def transform_shifts(
    df: pd.DataFrame,
    employees: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "shift_id",
        "employee_id",
        "department_id",
        "scheduled_start",
        "scheduled_end",
        "shift_type",
    }
    _require_columns(df, required, "shifts")
    out = df.copy()
    out["scheduled_start"] = _parse_datetime(out["scheduled_start"], "scheduled_start")
    out["scheduled_end"] = _parse_datetime(out["scheduled_end"], "scheduled_end")
    if (out["scheduled_end"] <= out["scheduled_start"]).any():
        raise TransformationError("scheduled_end must be after scheduled_start")
    if out["shift_id"].isna().any() or out["shift_id"].duplicated().any():
        raise TransformationError("shift_id must be non-null and unique")
    valid_employees = set(employees["employee_id"])
    unknown = set(out["employee_id"]) - valid_employees
    if unknown:
        raise TransformationError(f"shifts reference unknown employees: {sorted(unknown)}")
    out["scheduled_hours"] = (
        out["scheduled_end"] - out["scheduled_start"]
    ).dt.total_seconds() / 3600
    return out.sort_values(["employee_id", "scheduled_start"]).reset_index(drop=True)


def transform_punches(
    df: pd.DataFrame,
    shifts: pd.DataFrame,
    employees: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return clean punches and quarantined records."""
    required = {
        "punch_id",
        "shift_id",
        "employee_id",
        "department_id",
        "clock_in",
        "clock_out",
        "punch_status",
    }
    _require_columns(df, required, "punches")

    out = df.copy()
    out["clock_in"] = pd.to_datetime(out["clock_in"], errors="coerce")
    out["clock_out"] = pd.to_datetime(out["clock_out"], errors="coerce")

    reasons = pd.Series("", index=out.index, dtype="object")
    reasons = reasons.mask(out["clock_in"].isna(), "invalid_clock_in")
    reasons = reasons.mask(out["clock_out"].isna() & reasons.eq(""), "missing_or_invalid_clock_out")

    valid_shifts = set(shifts["shift_id"])
    valid_employees = set(employees["employee_id"])
    reasons = reasons.mask(
        ~out["shift_id"].isin(valid_shifts) & reasons.eq(""),
        "unknown_shift",
    )
    reasons = reasons.mask(
        ~out["employee_id"].isin(valid_employees) & reasons.eq(""),
        "unknown_employee",
    )

    complete_mask = out["clock_in"].notna() & out["clock_out"].notna()
    reasons = reasons.mask(
        complete_mask & (out["clock_out"] <= out["clock_in"]) & reasons.eq(""),
        "nonpositive_duration",
    )

    duplicate_mask = out.duplicated(subset=PUNCH_DEDUP_KEYS, keep="first")
    reasons = reasons.mask(duplicate_mask & reasons.eq(""), "duplicate_business_event")

    quarantine = out[reasons.ne("")].copy()
    quarantine["quarantine_reason"] = reasons[reasons.ne("")]

    clean = out[reasons.eq("")].copy()
    clean["worked_hours"] = (
        clean["clock_out"] - clean["clock_in"]
    ).dt.total_seconds() / 3600

    shift_cols = shifts[
        [
            "shift_id",
            "scheduled_start",
            "scheduled_end",
            "scheduled_hours",
        ]
    ]
    clean = clean.merge(shift_cols, on="shift_id", how="left", validate="many_to_one")

    clean["arrival_minutes"] = (
        clean["clock_in"] - clean["scheduled_start"]
    ).dt.total_seconds() / 60
    clean["departure_minutes"] = (
        clean["clock_out"] - clean["scheduled_end"]
    ).dt.total_seconds() / 60
    clean["regular_hours"] = np.minimum(clean["worked_hours"], 8.0)
    clean["daily_overtime_hours"] = np.maximum(clean["worked_hours"] - 8.0, 0.0)

    employee_rates = employees[["employee_id", "hourly_rate"]]
    clean = clean.merge(employee_rates, on="employee_id", how="left", validate="many_to_one")
    clean["regular_pay"] = (
        clean["regular_hours"] * clean["hourly_rate"]
    ).map(_money)
    clean["overtime_pay"] = (
        clean["daily_overtime_hours"] * clean["hourly_rate"] * 1.5
    ).map(_money)
    clean["gross_pay_estimate"] = (
        clean["regular_pay"] + clean["overtime_pay"]
    ).map(_money)

    clean["work_date"] = clean["clock_in"].dt.date
    clean["week_start"] = (
        clean["clock_in"] - pd.to_timedelta(clean["clock_in"].dt.weekday, unit="D")
    ).dt.date

    clean = clean.sort_values(["employee_id", "clock_in"]).reset_index(drop=True)
    quarantine = quarantine.sort_values("punch_id").reset_index(drop=True)
    return clean, quarantine


def transform_labels(
    df: pd.DataFrame,
    clean_punches: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "anomaly_id",
        "punch_id",
        "shift_id",
        "employee_id",
        "anomaly_type",
        "is_anomaly",
    }
    _require_columns(df, required, "labels")
    out = df.copy()
    out["is_anomaly"] = (
        out["is_anomaly"]
        .astype(str)
        .str.lower()
        .map({"true": True, "false": False})
    )
    if out["is_anomaly"].isna().any():
        raise TransformationError("is_anomaly must contain true or false")
    clean_ids = set(clean_punches["punch_id"])
    out["is_evaluable"] = out["punch_id"].isin(clean_ids)
    return out.sort_values("anomaly_id").reset_index(drop=True)


def transform_all(raw: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    departments = transform_departments(raw["departments"])
    employees = transform_employees(raw["employees"], departments)
    shifts = transform_shifts(raw["shifts"], employees)
    punches, quarantine = transform_punches(raw["punches"], shifts, employees)
    labels = transform_labels(raw["labels"], punches)
    return {
        "departments": departments,
        "employees": employees,
        "shifts": shifts,
        "punches": punches,
        "quarantine": quarantine,
        "labels": labels,
    }
