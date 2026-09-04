"""Versioned ingestion orchestration for contracts."""
import hashlib
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentRecord, DocumentVersion
from app.services.document.identity import document_id, version_id
from app.services.document.pymupdf_adapter import PyMuPDFAdapter
from app.services.document.text_projection import project_text
from app.services.document.repository import persist_ast
from app.models.document import ParseAttempt
from app.services.document.parser_router import ParserRouter
from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock, DocumentSpan
from app.services.document.identity import block_id, span_id
from app.services.document.parser import document_parser

class DocumentIngestionService:
    async def ingest_contract(self, db: AsyncSession, contract, file_path: str) -> dict:
        path = Path(file_path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        record = (await db.execute(select(DocumentRecord).where(DocumentRecord.contract_id == contract.id))).scalar_one_or_none()
        if record is None:
            record = DocumentRecord(id=document_id(digest), contract_id=contract.id, file_hash=digest,
                                   file_name=contract.file_name, mime_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if path.suffix.lower() == ".docx" else "application/pdf"), file_size=path.stat().st_size)
            db.add(record)
        number = ((await db.execute(select(DocumentVersion).where(DocumentVersion.document_id == record.id))).scalars().all())
        parser = PyMuPDFAdapter()
        parser_name, parser_version = ("python-docx", "0.8+") if path.suffix.lower() == ".docx" else (parser.name, parser.version)
        ver_id = version_id(record.id, parser_name, parser_version + ":" + str(len(number) + 1))
        if path.suffix.lower() == ".docx":
            parsed = await document_parser.parse_word(str(path))
            parts = parsed.get("paragraphs", []) + [" | ".join(row) for table in parsed.get("tables", []) for row in table]
            text = "\n\n".join(item for item in parts if item.strip())
            blocks, offset = [], 0
            for index, item in enumerate(parts):
                if not item.strip():
                    continue
                start, end = offset, offset + len(item)
                blocks.append(DocumentBlock(block_id=block_id(ver_id, 0, index), block_type="paragraph", text=item,
                    char_start=start, char_end=end, reading_order=index,
                    spans=[DocumentSpan(span_id=span_id(ver_id, 0, index, 0), text=item,
                        char_start=start, char_end=end, source_ref={"format": "docx"})]))
                offset = end + 2
            ast = UnifiedDocument(document_id=record.id, version_id=ver_id, parser_name="python-docx", parser_version="0.8+",
                pages=[DocumentPage(page_id=block_id(ver_id, 0, 999), page_number=0, width=612, height=792,
                    classification="text", quality_score=1.0, reading_order=0, blocks=blocks)], text=text,
                warnings=[{"code": "docx_page_only_evidence", "message": "DOCX 使用逻辑页，暂无版式坐标"}])
        else:
            ast = await parser.parse_async(str(path), record.id, ver_id)
        version = DocumentVersion(id=ver_id, document_id=record.id, version_number=len(number) + 1,
            parser_name=parser_name, parser_version=parser_version, status="completed",
            parse_quality=1.0 if ast.text.strip() else 0.0, warnings=ast.warnings,
            ast_snapshot=ast.model_dump(mode="json"))
        db.add(version)
        record.current_version_id = version.id
        contract.content_text = ast.text
        await db.flush()
        attempts = ParserRouter().route(str(path)) if path.suffix.lower() == ".pdf" else [{"page": 0, "classification": "text", "parser": parser_name, "quality_score": 1.0}]
        for attempt in attempts:
            db.add(ParseAttempt(version_id=version.id, scope="page", page_number=attempt["page"],
                classification=attempt["classification"], parser_name=attempt["parser"],
                parser_version="configured", status="completed",
                quality_score=attempt["quality_score"], metrics=attempt))
        await persist_ast(db, version, ast)
        await db.commit()
        # Embedding enrichment is optional; BM25 remains usable offline.
        from app.services.rag.contract_chunk_retriever import contract_chunk_retriever
        indexed_chunks = await contract_chunk_retriever.index_version_chunks(version.id)
        return {"document_id": record.id, "version_id": version.id, "status": version.status,
                "parser": parser_name, "pages": len(ast.pages), "text": ast.text,
                "chunks_indexed": indexed_chunks}

document_ingestion_service = DocumentIngestionService()
