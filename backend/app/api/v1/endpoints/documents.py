from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.endpoints.auth import get_current_user
from app.db.session import get_db
from app.middleware.tenant_isolation import verify_contract_access
from app.models.contract import Contract
from app.models.document import DocumentRecord, DocumentVersion, ParseAttempt
from app.services.document.ingestion_service import document_ingestion_service
from app.api.v1.endpoints.contracts import resolve_contract_file_path

router = APIRouter()

@router.post("/{contract_id}/ingest")
async def ingest_document(contract: Contract = Depends(verify_contract_access), db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    path = resolve_contract_file_path(contract.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="合同文件不存在")
    return await document_ingestion_service.ingest_contract(db, contract, str(path))

@router.get("/{contract_id}/ingestion")
async def ingestion_status(contract: Contract = Depends(verify_contract_access), db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    record = (await db.execute(select(DocumentRecord).where(DocumentRecord.contract_id == contract.id))).scalar_one_or_none()
    if not record:
        return {"status": "not_started", "document_id": None, "version_id": None}
    version = (await db.execute(select(DocumentVersion).where(DocumentVersion.id == record.current_version_id))).scalar_one_or_none()
    attempts = list((await db.execute(select(ParseAttempt).where(ParseAttempt.version_id == version.id))).scalars().all()) if version else []
    return {"status": version.status if version else "queued", "document_id": record.id,
            "version_id": version.id if version else None, "parser": version.parser_name if version else None,
            "quality_score": version.parse_quality if version else None,
            "warnings": version.warnings if version else [],
            "pages": [{"page": item.page_number, "classification": item.classification,
                        "parser": item.parser_name, "quality_score": item.quality_score,
                        "status": item.status, "metrics": item.metrics} for item in attempts]}

@router.get("/{contract_id}/ingestion/ast")
async def ingestion_ast(contract: Contract = Depends(verify_contract_access), db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    record = (await db.execute(select(DocumentRecord).where(DocumentRecord.contract_id == contract.id))).scalar_one_or_none()
    if not record or not record.current_version_id:
        raise HTTPException(status_code=404, detail="文档尚未解析")
    version = (await db.execute(select(DocumentVersion).where(DocumentVersion.id == record.current_version_id))).scalar_one()
    # Debug endpoint intentionally returns bounded AST metadata, not raw file bytes.
    snapshot = dict(version.ast_snapshot or {})
    snapshot["text"] = snapshot.get("text", "")[:100000]
    return snapshot
