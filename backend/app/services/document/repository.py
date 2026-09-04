"""Persistence boundary for the canonical AST."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentVersion
from app.models.document_provenance import DocumentPage as PageRow, DocumentBlock as BlockRow, DocumentSpan as SpanRow, DocumentChunk as ChunkRow
from app.services.rag.structure_chunker import chunk_document

async def persist_ast(db: AsyncSession, version: DocumentVersion, document) -> None:
    version.ast_snapshot = document.model_dump(mode="json")
    for page in document.pages:
        page_row = PageRow(version_id=version.id, page_number=page.page_number, width=page.width,
            height=page.height, classification=page.classification, quality_score=page.quality_score,
            metadata_json=page.metadata)
        db.add(page_row)
        await db.flush()
        for block in page.blocks:
            block_row = BlockRow(page_id=page_row.id, block_id=block.block_id, block_type=block.block_type,
                text=block.text, char_start=block.char_start, char_end=block.char_end,
                reading_order=block.reading_order, bbox=block.bbox.model_dump() if block.bbox else None,
                parent_block_id=block.parent_block_id)
            db.add(block_row)
            await db.flush()
            for span in block.spans:
                db.add(SpanRow(block_id=block_row.id, span_key=span.span_id, text=span.text,
                    char_start=span.char_start, char_end=span.char_end,
                    bbox=span.bbox.model_dump() if span.bbox else None,
                    span_type=span.span_type, confidence=span.confidence))
    for chunk in chunk_document(document):
        db.add(ChunkRow(id=chunk["chunk_id"], version_id=version.id, text=chunk["text"], section_path=chunk.get("section_path"),
                        section_id=chunk.get("section_id"), chunk_type=chunk.get("chunk_type", "clause"),
                        parent_chunk_id=chunk.get("parent_chunk_id"), parent_text=chunk.get("parent_text"), block_ids=chunk["block_ids"],
                        span_ids=chunk.get("span_ids", []), page_start=chunk["page_start"], page_end=chunk["page_end"],
                        char_start=chunk.get("char_start"), char_end=chunk.get("char_end"),
                        token_count=chunk.get("token_count"), is_complete_clause=1 if chunk.get("is_complete_clause", True) else 0,
                        text_hash=chunk["text_hash"]))
