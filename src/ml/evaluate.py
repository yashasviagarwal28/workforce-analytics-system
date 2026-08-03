"""Evaluate anomaly predictions against separate ground-truth labels."""

from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def evaluate(
    scores: pd.DataFrame,
    labels: pd.DataFrame,
    all_punch_ids: pd.Series,
) -> Dict[str, float]:
    truth = pd.DataFrame({"punch_id": all_punch_ids.astype(str)})
    labeled_ids = set(labels.loc[labels["is_anomaly"] == True, "punch_id"])  # noqa: E712
    truth["actual_anomaly"] = truth["punch_id"].isin(labeled_ids)

    merged = truth.merge(
        scores[["punch_id", "predicted_anomaly", "anomaly_score"]],
        on="punch_id",
        how="inner",
        validate="one_to_one",
    )

    y_true = merged["actual_anomaly"]
    y_pred = merged["predicted_anomaly"]
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()

    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_negatives": int(tn),
    }


def main() -> None:
    scores = pd.read_parquet("data/processed/anomaly_scores.parquet")
    labels = pd.read_parquet("data/processed/labels.parquet")
    punches = pd.read_parquet("data/processed/punches.parquet")
    metrics = evaluate(scores, labels, punches["punch_id"])
    output = Path("artifacts/metrics.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(pd.Series(metrics).to_json(indent=2))
    print(metrics)


if __name__ == "__main__":
    main()
