"""Orchestrate extract, transform, and load."""

import logging
from pathlib import Path
from typing import Dict

from src.etl.extract import RawPaths, extract_all
from src.etl.load import load_all
from src.etl.transform import transform_all


LOGGER = logging.getLogger(__name__)


def run_pipeline(
    raw_paths: RawPaths = RawPaths(),
    output_dir: Path = Path("data/processed"),
) -> Dict[str, Path]:
    LOGGER.info("Starting ETL pipeline")
    raw = extract_all(raw_paths)
    LOGGER.info("Extracted tables: %s", {k: len(v) for k, v in raw.items()})
    transformed = transform_all(raw)
    LOGGER.info("Transformed tables: %s", {k: len(v) for k, v in transformed.items()})
    paths = load_all(transformed, output_dir)
    LOGGER.info("Completed ETL pipeline")
    return paths


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    paths = run_pipeline()
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
