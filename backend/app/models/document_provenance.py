"""Relational provenance rows for AST and review evidence."""
from sqlalchemy import Column, String, Integer, Text, JSON, Float, ForeignKey
from app.models.base import Base, UUIDMixin, TimestampMixin

class DocumentPage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_pages"
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    classification = Column(String(20), nullable=True)
    quality_score = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)

class DocumentBlock(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_blocks"
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    block_id = Column(String(100), nullable=False, unique=True)
    block_type = Column(String(30), nullable=False)
    text = Column(Text, nullable=False, default="")
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    reading_order = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=True)
    parent_block_id = Column(String(100), nullable=True)

class DocumentSpan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_spans"
    block_id = Column(String(36), ForeignKey("document_blocks.id", ondelete="CASCADE"), nullable=False, index=True)
    span_key = Column(String(100), nullable=False, unique=True)
    text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=True)
    span_type = Column(String(30), nullable=False, default="text")
    confidence = Column(Float, nullable=True)

class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_chunks"
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    section_path = Column(String(500), nullable=True)
    section_id = Column(String(120), nullable=True, index=True)
    chunk_type = Column(String(30), nullable=False, default="clause")
    parent_chunk_id = Column(String(36), nullable=True, index=True)
    parent_text = Column(Text, nullable=True)
    block_ids = Column(JSON, nullable=True)
    span_ids = Column(JSON, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    is_complete_clause = Column(Integer, nullable=False, default=1)
    text_hash = Column(String(64), nullable=False)
    # Stored as pgvector literal text for SQLite/local model compatibility;
    # PostgreSQL migration adds a generated vector index/query cast.
    embedding = Column(Text, nullable=True)
    embedding_model = Column(String(120), nullable=True)

class ReviewEvidence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "review_evidence"
    review_run_id = Column(String(36), nullable=True, index=True)
    risk_id = Column(String(100), nullable=True)
    document_id = Column(String(36), nullable=False, index=True)
    version_id = Column(String(36), nullable=False, index=True)
    quote = Column(Text, nullable=False)
    locations = Column(JSON, nullable=False)
    match_type = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=False)
