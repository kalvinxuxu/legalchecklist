"""Durable contract review runs and stage progress."""
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, Float
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class ReviewRunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    stalled = "stalled"


class ReviewStepStatus(str, enum.Enum):
    waiting = "waiting"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class ReviewRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_runs"

    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ReviewRunStatus), default=ReviewRunStatus.queued, nullable=False, index=True)
    current_stage = Column(String(64), nullable=True)
    progress = Column(Float, default=0, nullable=False)
    attempt = Column(Integer, default=0, nullable=False)
    last_heartbeat_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    checkpoint_thread_id = Column(String(128), nullable=False, unique=True, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    contract = relationship("Contract", back_populates="review_runs")
    steps = relationship("ReviewStep", back_populates="run", cascade="all, delete-orphan", order_by="ReviewStep.created_at")


class ReviewStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_steps"

    run_id = Column(String(36), ForeignKey("review_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(64), nullable=False)
    status = Column(Enum(ReviewStepStatus), default=ReviewStepStatus.waiting, nullable=False)
    attempt = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    step_metadata = Column("metadata", JSON, nullable=True)

    run = relationship("ReviewRun", back_populates="steps")
