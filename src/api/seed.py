"""Seed API database from processed anomaly scores."""

import pandas as pd
from sqlalchemy.orm import Session

from src.api.models import AnomalyRecord


def seed_anomalies(db: Session) -> int:
    scores = pd.read_parquet("data/processed/anomaly_scores.parquet")
    existing = {row[0] for row in db.query(AnomalyRecord.punch_id).all()}

    inserted = 0
    for row in scores.itertuples(index=False):
        if row.punch_id in existing:
            continue
        db.add(
            AnomalyRecord(
                punch_id=row.punch_id,
                shift_id=row.shift_id,
                employee_id=row.employee_id,
                department_id=row.department_id,
                clock_in=pd.Timestamp(row.clock_in).to_pydatetime(),
                anomaly_score=float(row.anomaly_score),
                predicted_anomaly=bool(row.predicted_anomaly),
                reason_hint=str(row.reason_hint),
                review_status="pending",
            )
        )
        inserted += 1
    db.commit()
    return inserted
