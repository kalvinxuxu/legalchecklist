"""Persisted review delivery records."""
from sqlalchemy import Column, String, Text, JSON, Integer, Index
from app.models.base import Base, UUIDMixin, TimestampMixin


class EmailDraft(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_drafts"

    tenant_id = Column(String(36), nullable=False, index=True)
    contract_id = Column(String(36), nullable=False, index=True)
    review_run_id = Column(String(36), nullable=True)
    opinion_id = Column(String(36), nullable=True)
    sender_email = Column(String(320), nullable=True)
    recipients = Column(JSON, nullable=False, default=list)
    attachments = Column(JSON, nullable=False, default=list)
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False, default="mock")
    provider_draft_id = Column(String(255), nullable=True)
    sync_status = Column(String(30), nullable=False, default="local_saved")
    idempotency_key = Column(String(128), nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    __table_args__ = (
        Index("uq_email_drafts_tenant_idempotency", "tenant_id", "idempotency_key", unique=True),
    )
