"""Evidence contracts shared by review API and PDF viewer."""
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.document import BBox

class EvidenceLocation(BaseModel):
    page: int = Field(ge=0)
    bbox: BBox | None = None
    span_id: str | None = None
    coord_system: Literal["pdf_top_left"] = "pdf_top_left"
    resolution_status: Literal["resolved", "fuzzy_fallback", "page_only", "unresolved"] = "resolved"

class DocumentChunk(BaseModel):
    chunk_id: str
    version_id: str
    text: str
    chunk_type: str = "clause"
    section_id: str | None = None
    section_path: str | None = None
    parent_chunk_id: str | None = None
    parent_text: str | None = None
    block_ids: list[str] = Field(default_factory=list)
    span_ids: list[str] = Field(default_factory=list)
    page_start: int | None = Field(default=None, ge=0)
    page_end: int | None = Field(default=None, ge=0)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    token_count: int | None = Field(default=None, ge=0)
    is_complete_clause: bool = True
    bm25_rank: int | None = Field(default=None, ge=1)
    vector_rank: int | None = Field(default=None, ge=1)
    fused_rank: int | None = Field(default=None, ge=1)
    rerank_rank: int | None = Field(default=None, ge=1)
    bm25_score: float | None = None
    vector_score: float | None = None
    fused_score: float | None = None
    semantic_score: float | None = Field(default=None, ge=0, le=1)
    authority_score: float | None = Field(default=None, ge=0, le=1)
    metadata_score: float | None = Field(default=None, ge=0, le=1)
    rerank_score: float | None = None
    reranker_provider: str | None = None
    reranker_model: str | None = None
    reranker_version: str | None = None
    fallback_reason: str | None = None

class ReviewEvidence(BaseModel):
    evidence_id: str
    risk_id: str | None = None
    document_id: str
    version_id: str
    quote: str
    locations: list[EvidenceLocation] = Field(min_length=1)
    match_type: Literal["id_exact", "offset_exact", "fuzzy_legacy", "page_only"]
    confidence: float = Field(ge=0, le=1)
