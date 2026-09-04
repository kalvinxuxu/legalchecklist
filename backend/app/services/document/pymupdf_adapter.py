"""PyMuPDF extraction into the internal UnifiedDocument AST."""
from pathlib import Path
from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock, DocumentSpan
from app.services.document.coordinates import normalize_bbox
from app.services.document.identity import block_id, span_id, validate_offsets

class PyMuPDFAdapter:
    name = "pymupdf"
    version = "1"

    def parse(self, file_path: str, document_id: str, version_id: str) -> UnifiedDocument:
        import fitz
        pages = []
        tables = []
        text_parts = []
        with fitz.open(str(Path(file_path))) as pdf:
            for page_no, page in enumerate(pdf):
                width, height = page.rect.width, page.rect.height
                page_text = []
                blocks = []
                page_data = page.get_text("dict")
                for raw_block in page_data.get("blocks", []):
                    if raw_block.get("type", 0) != 0:
                        continue
                    lines = raw_block.get("lines", [])
                    spans = []
                    block_text_parts = []
                    for line in lines:
                        for raw_span in line.get("spans", []):
                            value = raw_span.get("text", "")
                            if not value.strip():
                                continue
                            block_text_parts.append(value)
                            page_text.append(value)
                    block_text = " ".join(block_text_parts).strip()
                    if not block_text:
                        continue
                    block_start = sum(len(x) + 1 for x in text_parts) + sum(len(x) + 1 for x in page_text[:-1])
                    block = DocumentBlock(
                        block_id=block_id(version_id, page_no, len(blocks)), text=block_text,
                        char_start=block_start, char_end=block_start + len(block_text),
                        reading_order=len(blocks), block_type="paragraph",
                        bbox=normalize_bbox(tuple(raw_block.get("bbox", (0, 0, width, height))), width, height),
                    )
                    cursor = block_start
                    for line in lines:
                        for raw_span in line.get("spans", []):
                            value = raw_span.get("text", "")
                            if not value.strip():
                                continue
                            start = cursor
                            end = start + len(value)
                            spans.append(DocumentSpan(
                                span_id=span_id(version_id, page_no, len(blocks), len(spans)),
                                text=value, char_start=start, char_end=end,
                                bbox=normalize_bbox(tuple(raw_span.get("bbox", raw_block.get("bbox"))), width, height),
                                source_ref={"font": raw_span.get("font"), "size": raw_span.get("size")},
                            ))
                            cursor = end + 1
                    block.spans = spans
                    if spans:
                        # Some PDFs expose ligatures/font fragments whose raw
                        # span length differs from reconstructed block text.
                        # Keep offsets monotonic and let the canonical text
                        # projection remain the source of truth.
                        block.char_end = max(block.char_end, max(span.char_end for span in spans))
                    blocks.append(block)
                normalized_page_text = "\n".join(page_text)
                text_parts.append(normalized_page_text)
                pages.append(DocumentPage(
                    page_id=f"{version_id}:page:{page_no}", page_number=page_no,
                    width=width, height=height, blocks=blocks, reading_order=page_no,
                    classification="text" if normalized_page_text.strip() else "scan",
                    quality_score=1.0 if normalized_page_text.strip() else 0.0,
                ))
        full_text = "\n\n".join(text_parts)
        return UnifiedDocument(document_id=document_id, version_id=version_id,
            parser_name=self.name, parser_version=self.version, pages=pages,
            text=full_text)

    async def parse_async(self, file_path: str, document_id: str, version_id: str) -> UnifiedDocument:
        import asyncio
        return await asyncio.to_thread(self.parse, file_path, document_id, version_id)
