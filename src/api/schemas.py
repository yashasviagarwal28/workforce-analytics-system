"""Pydantic request and response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    punch_id: str
    shift_id: str
    employee_id: str
    department_id: str
    clock_in: datetime
    anomaly_score: float
    predicted_anomaly: bool
    reason_hint: str
    review_status: str
    reviewer_notes: Optional[str] = None


class AnomalyListResponse(BaseModel):
    items: List[AnomalyResponse]
    total: int
    limit: int
    offset: int


class ReviewUpdate(BaseModel):
    review_status: str = Field(pattern="^(pending|confirmed_issue|legitimate|resolved)$")
    reviewer_notes: Optional[str] = Field(default=None, max_length=2000)


class SummaryResponse(BaseModel):
    total_records: int
    flagged_records: int
    pending_reviews: int
    confirmed_issues: int
