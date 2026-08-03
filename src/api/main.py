"""FastAPI application for anomaly review."""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.database import Base, engine, get_db
from src.api.models import AnomalyRecord
from src.api.schemas import (
    AnomalyListResponse,
    AnomalyResponse,
    ReviewUpdate,
    SummaryResponse,
)
from src.api.seed import seed_anomalies


app = FastAPI(title="OpsPulse API", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/admin/seed")
def seed(db: Session = Depends(get_db)) -> dict:
    try:
        inserted = seed_anomalies(db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"inserted": inserted}


@app.get("/anomalies", response_model=AnomalyListResponse)
def list_anomalies(
    flagged_only: bool = True,
    review_status: Optional[str] = None,
    department_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> AnomalyListResponse:
    query = db.query(AnomalyRecord)
    if flagged_only:
        query = query.filter(AnomalyRecord.predicted_anomaly.is_(True))
    if review_status:
        query = query.filter(AnomalyRecord.review_status == review_status)
    if department_id:
        query = query.filter(AnomalyRecord.department_id == department_id)

    total = query.count()
    items = (
        query.order_by(AnomalyRecord.anomaly_score.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return AnomalyListResponse(items=items, total=total, limit=limit, offset=offset)


@app.get("/anomalies/{punch_id}", response_model=AnomalyResponse)
def get_anomaly(punch_id: str, db: Session = Depends(get_db)) -> AnomalyRecord:
    record = db.get(AnomalyRecord, punch_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Anomaly record not found")
    return record


@app.patch("/anomalies/{punch_id}", response_model=AnomalyResponse)
def update_review(
    punch_id: str,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
) -> AnomalyRecord:
    record = db.get(AnomalyRecord, punch_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Anomaly record not found")
    record.review_status = payload.review_status
    record.reviewer_notes = payload.reviewer_notes
    db.commit()
    db.refresh(record)
    return record


@app.get("/metrics/summary", response_model=SummaryResponse)
def summary(db: Session = Depends(get_db)) -> SummaryResponse:
    total = db.query(func.count(AnomalyRecord.punch_id)).scalar() or 0
    flagged = (
        db.query(func.count(AnomalyRecord.punch_id))
        .filter(AnomalyRecord.predicted_anomaly.is_(True))
        .scalar()
        or 0
    )
    pending = (
        db.query(func.count(AnomalyRecord.punch_id))
        .filter(AnomalyRecord.review_status == "pending")
        .scalar()
        or 0
    )
    confirmed = (
        db.query(func.count(AnomalyRecord.punch_id))
        .filter(AnomalyRecord.review_status == "confirmed_issue")
        .scalar()
        or 0
    )
    return SummaryResponse(
        total_records=total,
        flagged_records=flagged,
        pending_reviews=pending,
        confirmed_issues=confirmed,
    )
