"""Persist transformed workforce data idempotently."""

from pathlib import Path
from typing import Dict

import pandas as pd


class LoadError(RuntimeError):
    """Raised when processed data cannot be written."""


def write_table(df: pd.DataFrame, path: Path) -> None:
    """Write one table by replacing the prior output atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.suffix == ".parquet":
            df.to_parquet(temporary_path, index=False)
        elif path.suffix == ".csv":
            df.to_csv(temporary_path, index=False)
        else:
            raise LoadError(f"Unsupported output format: {path.suffix}")
        temporary_path.replace(path)
    except Exception as exc:
        if temporary_path.exists():
            temporary_path.unlink()
        if isinstance(exc, LoadError):
            raise
        raise LoadError(f"Could not write {path}: {exc}") from exc


def load_all(
    tables: Dict[str, pd.DataFrame],
    output_dir: Path = Path("data/processed"),
) -> Dict[str, Path]:
    """Write all transformed tables and return their output paths."""
    paths = {
        name: output_dir / f"{name}.parquet"
        for name in tables
    }
    for name, df in tables.items():
        write_table(df, paths[name])
    return paths
