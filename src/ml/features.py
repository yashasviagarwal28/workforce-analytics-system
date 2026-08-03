"""Create model-ready anomaly-detection features."""

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd


FEATURE_COLUMNS: List[str] = [
    "worked_hours",
    "daily_overtime_hours",
    "arrival_minutes",
    "departure_minutes",
    "scheduled_hours",
    "rest_hours_before_shift",
    "employee_mean_worked_hours",
    "employee_std_worked_hours",
    "worked_hours_zscore",
]


def build_features(punches: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = punches.copy()
    df["clock_in"] = pd.to_datetime(df["clock_in"])
    df["clock_out"] = pd.to_datetime(df["clock_out"])
    df = df.sort_values(["employee_id", "clock_in"]).reset_index(drop=True)

    previous_clock_out = df.groupby("employee_id")["clock_out"].shift(1)
    df["rest_hours_before_shift"] = (
        df["clock_in"] - previous_clock_out
    ).dt.total_seconds() / 3600
    df["rest_hours_before_shift"] = df["rest_hours_before_shift"].fillna(24.0)

    grouped = df.groupby("employee_id")["worked_hours"]
    df["employee_mean_worked_hours"] = grouped.transform("mean")
    df["employee_std_worked_hours"] = grouped.transform("std").fillna(0.0)
    safe_std = df["employee_std_worked_hours"].replace(0, np.nan)
    df["worked_hours_zscore"] = (
        (df["worked_hours"] - df["employee_mean_worked_hours"]) / safe_std
    ).fillna(0.0)

    metadata = df[
        ["punch_id", "shift_id", "employee_id", "department_id", "clock_in"]
    ].copy()
    features = df[FEATURE_COLUMNS].astype(float).replace([np.inf, -np.inf], 0).fillna(0)
    return features, metadata


def load_processed_punches(
    path: Path = Path("data/processed/punches.parquet"),
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Processed punches not found: {path}")
    return pd.read_parquet(path)
