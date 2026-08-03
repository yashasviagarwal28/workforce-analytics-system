"""Inject reproducible labeled behavioral anomalies."""
from datetime import timedelta
from pathlib import Path
import random
import pandas as pd
from config.settings import (
    ANOMALY_INJECTION_RATE, ANOMALY_TYPE_WEIGHTS,
    EARLY_CLOCK_IN_MAXIMUM_HOURS, EARLY_CLOCK_IN_MINIMUM_HOURS,
    EXTREME_OVERTIME_MAXIMUM_HOURS, EXTREME_OVERTIME_MINIMUM_HOURS,
    RANDOM_SEED,
)
from src.generation.generate_employees import generate_employees
from src.generation.generate_shifts import generate_shifts
from src.generation.generate_time_punches import generate_time_punches, validate_time_punches

ANOMALY_LABEL_COLUMNS = [
    "anomaly_id", "punch_id", "shift_id", "employee_id", "anomaly_type",
    "original_clock_in", "original_clock_out", "injected_clock_in",
    "injected_clock_out", "anomaly_reason", "is_anomaly",
]

def build_anomaly_id(anomaly_number: int) -> str:
    if anomaly_number < 1:
        raise ValueError("Anomaly number must be at least 1.")
    return f"ANM{anomaly_number:06d}"

def calculate_anomaly_count(eligible_record_count: int) -> int:
    if eligible_record_count < 0:
        raise ValueError("Eligible record count cannot be negative.")
    if eligible_record_count == 0:
        return 0
    return max(1, round(eligible_record_count * ANOMALY_INJECTION_RATE))

def choose_anomaly_type(rng: random.Random) -> str:
    return rng.choices(
        population=list(ANOMALY_TYPE_WEIGHTS.keys()),
        weights=list(ANOMALY_TYPE_WEIGHTS.values()),
        k=1,
    )[0]

def inject_anomalies(punches_df: pd.DataFrame):
    rng = random.Random(RANDOM_SEED + 3)
    modified = punches_df.copy(deep=True)
    eligible_indices = list(modified[modified["punch_status"] == "complete"].index)
    anomaly_count = calculate_anomaly_count(len(eligible_indices))
    selected_indices = rng.sample(eligible_indices, k=anomaly_count)
    labels = []
    for anomaly_number, row_index in enumerate(selected_indices, start=1):
        original = modified.loc[row_index].copy()
        anomaly_type = choose_anomaly_type(rng)
        original_clock_in = pd.Timestamp(original["clock_in"])
        original_clock_out = pd.Timestamp(original["clock_out"])
        injected_clock_in = original_clock_in
        injected_clock_out = original_clock_out
        if anomaly_type == "extremely_early_clock_in":
            injected_clock_in = (
                original_clock_in
                - timedelta(hours=rng.uniform(
                    EARLY_CLOCK_IN_MINIMUM_HOURS,
                    EARLY_CLOCK_IN_MAXIMUM_HOURS,
                ))
            ).round("min")
            reason = "Clock-in was moved several hours before expected behavior."
        elif anomaly_type == "insufficient_rest":
            injected_clock_out = (
                original_clock_out
                + timedelta(hours=rng.uniform(
                    EXTREME_OVERTIME_MINIMUM_HOURS,
                    EXTREME_OVERTIME_MAXIMUM_HOURS,
                ))
            ).round("min")
            reason = "Clock-out was extended to create an unusually short future rest period."
        else:
            injected_clock_out = (
                original_clock_out
                + timedelta(hours=rng.uniform(
                    EXTREME_OVERTIME_MINIMUM_HOURS,
                    EXTREME_OVERTIME_MAXIMUM_HOURS,
                ))
            ).round("min")
            reason = "Clock-out was extended several hours beyond ordinary behavior."
        modified.loc[row_index, "clock_in"] = injected_clock_in.isoformat()
        modified.loc[row_index, "clock_out"] = injected_clock_out.isoformat()
        labels.append({
            "anomaly_id": build_anomaly_id(anomaly_number),
            "punch_id": original["punch_id"],
            "shift_id": original["shift_id"],
            "employee_id": original["employee_id"],
            "anomaly_type": anomaly_type,
            "original_clock_in": original["clock_in"],
            "original_clock_out": original["clock_out"],
            "injected_clock_in": injected_clock_in.isoformat(),
            "injected_clock_out": injected_clock_out.isoformat(),
            "anomaly_reason": reason,
            "is_anomaly": True,
        })
    return modified, pd.DataFrame(labels, columns=ANOMALY_LABEL_COLUMNS)

def validate_anomaly_labels(labels_df: pd.DataFrame, original_punches_df: pd.DataFrame, modified_punches_df: pd.DataFrame) -> None:
    required = set(ANOMALY_LABEL_COLUMNS)
    missing = required - set(labels_df.columns)
    if missing:
        raise ValueError(f"Missing required anomaly-label columns: {sorted(missing)}")
    if labels_df.empty:
        raise ValueError("Anomaly-label table cannot be empty.")
    if labels_df["anomaly_id"].isna().any() or labels_df["anomaly_id"].duplicated().any():
        raise ValueError("Anomaly IDs must be unique and non-null.")
    if labels_df["punch_id"].duplicated().any():
        raise ValueError("Each punch may receive only one anomaly in the current version.")
    unknown = set(labels_df["punch_id"]) - set(original_punches_df["punch_id"])
    if unknown:
        raise ValueError(f"Labels reference unknown punches: {sorted(unknown)}")
    if not labels_df["is_anomaly"].eq(True).all():
        raise ValueError("Every anomaly-label record must be marked true.")
    original_by_id = original_punches_df.set_index("punch_id")
    modified_by_id = modified_punches_df.set_index("punch_id")
    for label in labels_df.itertuples(index=False):
        before = original_by_id.loc[label.punch_id]
        after = modified_by_id.loc[label.punch_id]
        if before["clock_in"] == after["clock_in"] and before["clock_out"] == after["clock_out"]:
            raise ValueError("Every labeled anomaly must change at least one punch timestamp.")

def main() -> None:
    employees_df = generate_employees()
    shifts_df = generate_shifts(employees_df)
    original_punches_df = generate_time_punches(shifts_df)
    validate_time_punches(original_punches_df, shifts_df)
    modified_punches_df, labels_df = inject_anomalies(original_punches_df)
    validate_time_punches(modified_punches_df, shifts_df)
    validate_anomaly_labels(labels_df, original_punches_df, modified_punches_df)
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    modified_punches_df.to_csv(raw_dir / "anomalous_time_punches.csv", index=False)
    labels_df.to_csv(raw_dir / "anomaly_labels.csv", index=False)
    print(f"Injected {len(labels_df)} labeled anomalies.")
    print(labels_df["anomaly_type"].value_counts().to_string())

if __name__ == "__main__":
    main()
