"""Canonical document ingestion primitives."""
from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock, DocumentSpan, BBox
from app.services.document.pymupdf_adapter import PyMuPDFAdapter

__all__ = ["UnifiedDocument", "DocumentPage", "DocumentBlock", "DocumentSpan", "BBox", "PyMuPDFAdapter"]
