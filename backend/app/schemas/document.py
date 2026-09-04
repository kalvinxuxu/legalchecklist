"""Internal, vendor-neutral document AST schemas."""
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

BlockType = Literal["title", "heading", "paragraph", "list", "table", "image", "footer", "unknown"]

class BBox(BaseModel):
    model_config = ConfigDict(frozen=True)
    x0: float = Field(ge=0)
    y0: float = Field(ge=0)
    x1: float = Field(ge=0)
    y1: float = Field(ge=0)

    @model_validator(mode="after")
    def valid_order(self):
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError("bbox coordinates must be ordered")
        return self

class CoordinateMetadata(BaseModel):
    system: Literal["pdf_top_left"] = "pdf_top_left"
    origin: Literal["top_left"] = "top_left"
    units: Literal["points"] = "points"

class DocumentSpan(BaseModel):
    span_id: str
    text: str
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    bbox: BBox | None = None
    span_type: Literal["text", "table", "image", "formula", "unknown"] = "text"
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_ref: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_offsets(self):
        if self.char_end < self.char_start:
            raise ValueError("span offsets must be ordered")
        return self

class DocumentBlock(BaseModel):
    block_id: str
    block_type: BlockType = "paragraph"
    text: str = ""
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    reading_order: int = Field(ge=0)
    bbox: BBox | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    spans: list[DocumentSpan] = Field(default_factory=list)
    parent_block_id: str | None = None

class DocumentPage(BaseModel):
    page_id: str
    page_number: int = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    classification: Literal["text", "scan", "hybrid", "complex", "unsupported"] = "text"
    quality_score: float | None = Field(default=None, ge=0, le=1)
    reading_order: int = Field(ge=0)
    blocks: list[DocumentBlock] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocumentTable(BaseModel):
    table_id: str
    block_id: str
    page_id: str
    caption: str | None = None
    bbox: BBox | None = None
    cells: list[list[str]] = Field(default_factory=list)
    extraction_status: Literal["complete", "partial", "failed"] = "complete"

class UnifiedDocument(BaseModel):
    document_id: str
    version_id: str
    parser_name: str
    parser_version: str
    coord_system: CoordinateMetadata = Field(default_factory=CoordinateMetadata)
    pages: list[DocumentPage] = Field(default_factory=list)
    tables: list[DocumentTable] = Field(default_factory=list)
    text: str = ""
    warnings: list[dict[str, Any]] = Field(default_factory=list)
