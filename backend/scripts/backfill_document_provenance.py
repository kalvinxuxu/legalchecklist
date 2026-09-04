"""Backfill one canonical document version for existing PDF contracts."""
import asyncio, hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from app.db.session import db
from app.models.contract import Contract
from app.models.document import DocumentRecord, DocumentVersion
from app.services.document.identity import document_id, version_id
from app.services.document.pymupdf_adapter import PyMuPDFAdapter
from app.services.document.repository import persist_ast

async def main():
    db.connect(); parser=PyMuPDFAdapter(); created=0
    async with db.async_session_maker() as session:
        contracts=(await session.execute(select(Contract).where(Contract.file_path.ilike("%.pdf")))).scalars().all()
        for contract in contracts:
            path=Path(contract.file_path)
            if not path.is_absolute(): path=Path(__file__).resolve().parents[1] / path
            if not path.exists(): continue
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            record=(await session.execute(select(DocumentRecord).where(DocumentRecord.contract_id==contract.id))).scalar_one_or_none()
            if record and record.current_version_id: continue
            record=record or DocumentRecord(id=document_id(digest), contract_id=contract.id, file_hash=digest, file_name=contract.file_name, mime_type="application/pdf", file_size=path.stat().st_size)
            session.add(record); await session.flush()
            vid=version_id(record.id, parser.name, parser.version+":1")
            ast=await parser.parse_async(str(path), record.id, vid)
            version=DocumentVersion(id=vid, document_id=record.id, version_number=1, parser_name=parser.name, parser_version=parser.version, status="completed", parse_quality=1.0 if ast.text else 0.0, warnings=ast.warnings)
            session.add(version); record.current_version_id=vid; contract.content_text=ast.text; await session.flush(); await persist_ast(session, version, ast); created+=1
        await session.commit()
    await db.disconnect(); print({"backfilled": created})

if __name__ == "__main__": asyncio.run(main())
