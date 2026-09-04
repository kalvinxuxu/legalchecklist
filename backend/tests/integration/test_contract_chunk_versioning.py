import pytest
from sqlalchemy import select

from app.db.session import db
from app.models.contract import Contract
from app.models.document import DocumentRecord, DocumentVersion
from app.models.document_provenance import DocumentChunk
from app.models.tenant import Tenant
from app.models.workspace import Workspace
from app.services.rag.contract_chunk_retriever import ContractChunkRetriever


@pytest.mark.asyncio
async def test_contract_chunk_loader_only_reads_current_version(db_session):
    tenant = Tenant(id="tenant-version", name="Version Tenant")
    workspace = Workspace(id="workspace-version", tenant_id=tenant.id, name="Workspace")
    contract = Contract(id="contract-version", workspace_id=workspace.id, file_name="x.pdf", file_path="x.pdf")
    record = DocumentRecord(id="document-version", contract_id=contract.id, file_hash="a" * 64, file_name="x.pdf", current_version_id="version-new")
    old = DocumentVersion(id="version-old", document_id=record.id, version_number=1, parser_name="test", parser_version="1", status="completed")
    current = DocumentVersion(id="version-new", document_id=record.id, version_number=2, parser_name="test", parser_version="2", status="completed")
    db_session.add_all([tenant, workspace, contract, record, old, current,
                        DocumentChunk(id="chunk-old", version_id=old.id, text="旧版本", text_hash="old"),
                        DocumentChunk(id="chunk-new", version_id=current.id, text="当前版本", text_hash="new")])
    await db_session.commit()
    original = db.async_session_maker
    db.async_session_maker = lambda: db_session
    try:
        rows = await ContractChunkRetriever()._load(contract.id, tenant.id)
    finally:
        db.async_session_maker = original
    assert [row["chunk_id"] for row in rows] == ["chunk-new"]

