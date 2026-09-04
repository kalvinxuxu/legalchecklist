"""Versioned document identity and parser attempts."""
from sqlalchemy import Column, String, Integer, Text, JSON, Float, ForeignKey
from app.models.base import Base, UUIDMixin, TimestampMixin

class DocumentRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_records"
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    file_hash = Column(String(64), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    file_size = Column(Integer, nullable=True)
    current_version_id = Column(String(36), nullable=True)

class DocumentVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_versions"
    document_id = Column(String(36), ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    parser_name = Column(String(100), nullable=False)
    parser_version = Column(String(100), nullable=False)
    coord_system = Column(String(50), nullable=False, default="pdf_top_left")
    status = Column(String(20), nullable=False, default="queued")
    parse_quality = Column(Float, nullable=True)
    warnings = Column(JSON, nullable=True)
    ast_snapshot = Column(JSON, nullable=True)
    completed_at = Column(String(40), nullable=True)

class ParseAttempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_parse_attempts"
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    scope = Column(String(20), nullable=False, default="page")
    page_number = Column(Integer, nullable=True)
    classification = Column(String(20), nullable=True)
    parser_name = Column(String(100), nullable=False)
    parser_version = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)
    quality_score = Column(Float, nullable=True)
    error_code = Column(String(100), nullable=True)
    fallback_from_attempt_id = Column(String(36), nullable=True)
    metrics = Column(JSON, nullable=True)
