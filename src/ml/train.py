"""Train and persist an Isolation Forest anomaly model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.ml.features import FEATURE_COLUMNS, build_features, load_processed_punches


@dataclass(frozen=True)
class TrainingConfig:
    contamination: float = 0.03
    random_state: int = 42
    n_estimators: int = 300


def train_model(
    punches: pd.DataFrame,
    config: TrainingConfig = TrainingConfig(),
) -> Dict[str, object]:
    features, metadata = build_features(punches)
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                IsolationForest(
                    contamination=config.contamination,
                    random_state=config.random_state,
                    n_estimators=config.n_estimators,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    predictions = pipeline.fit_predict(features)
    scores = -pipeline.decision_function(features)

    results = metadata.copy()
    results["anomaly_score"] = scores
    results["predicted_anomaly"] = predictions == -1
    results["reason_hint"] = features.idxmax(axis=1)

    return {
        "pipeline": pipeline,
        "results": results,
        "feature_columns": FEATURE_COLUMNS,
    }


def save_artifacts(
    artifacts: Dict[str, object],
    model_path: Path = Path("artifacts/isolation_forest.joblib"),
    scores_path: Path = Path("data/processed/anomaly_scores.parquet"),
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": artifacts["pipeline"],
            "feature_columns": artifacts["feature_columns"],
        },
        model_path,
    )
    artifacts["results"].to_parquet(scores_path, index=False)


def main() -> None:
    punches = load_processed_punches()
    artifacts = train_model(punches)
    save_artifacts(artifacts)
    predicted = int(artifacts["results"]["predicted_anomaly"].sum())
    print(f"Trained model and flagged {predicted} records.")


if __name__ == "__main__":
    main()
