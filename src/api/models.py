"""SQLAlchemy persistence models."""

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text

from src.api.database import Base


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    punch_id = Column(String, primary_key=True)
    shift_id = Column(String, nullable=False, index=True)
    employee_id = Column(String, nullable=False, index=True)
    department_id = Column(String, nullable=False, index=True)
    clock_in = Column(DateTime, nullable=False)
    anomaly_score = Column(Float, nullable=False, index=True)
    predicted_anomaly = Column(Boolean, nullable=False, index=True)
    reason_hint = Column(String, nullable=False)
    review_status = Column(String, nullable=False, default="pending", index=True)
    reviewer_notes = Column(Text, nullable=True)
