"""Read raw workforce files without applying business transformations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd


class ExtractionError(RuntimeError):
    """Raised when required raw input cannot be extracted."""


@dataclass(frozen=True)
class RawPaths:
    departments: Path = Path("data/raw/departments.csv")
    employees: Path = Path("data/raw/employees.csv")
    shifts: Path = Path("data/raw/shifts.csv")
    punches: Path = Path("data/raw/anomalous_time_punches.csv")
    labels: Path = Path("data/raw/anomaly_labels.csv")


def read_csv(path: Path) -> pd.DataFrame:
    """Read one CSV exactly as stored, preserving raw strings."""
    if not path.exists():
        raise ExtractionError(f"Required input file does not exist: {path}")
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=True)
    except Exception as exc:
        raise ExtractionError(f"Could not read {path}: {exc}") from exc


def extract_all(paths: RawPaths = RawPaths()) -> Dict[str, pd.DataFrame]:
    """Extract every raw table used by the pipeline."""
    return {
        "departments": read_csv(paths.departments),
        "employees": read_csv(paths.employees),
        "shifts": read_csv(paths.shifts),
        "punches": read_csv(paths.punches),
        "labels": read_csv(paths.labels),
    }
