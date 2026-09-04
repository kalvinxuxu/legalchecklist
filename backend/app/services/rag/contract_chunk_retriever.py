"""Hybrid retrieval over the current contract's structure-aware chunks."""
import json
import math
from collections import Counter
from typing import Any, Optional

from sqlalchemy import select

from app.core.config import settings
from app.db.session import db
from app.models.contract import Contract
from app.models.document import DocumentRecord, DocumentVersion
from app.models.document_provenance import DocumentChunk
from app.services.rag.bm25_retriever import _tokens, bm25_score
from app.services.rag.embedder import embedder


class ContractChunkRetriever:
    """PostgreSQL-backed contract chunk index; no Chroma dependency."""

    async def index_version_chunks(self, version_id: str) -> int:
        async with db.async_session_maker() as session:
            rows = list((await session.execute(select(DocumentChunk).where(DocumentChunk.version_id == version_id))).scalars().all())
            if not rows or (settings.EMBEDDING_PROVIDER.lower() == "zhipu" and not settings.ZHIPU_EMBEDDING_API_KEY):
                return 0
            try:
                vectors = await embedder.embed_batch([row.text for row in rows])
            except Exception:
                return 0
            for row, vector in zip(rows, vectors):
                row.embedding = json.dumps(vector, separators=(",", ":"))
                row.embedding_model = f"{embedder.provider_name}:{embedder.model}:{settings.EMBEDDING_MODEL_VERSION}"
            await session.commit()
            return len(rows)

    async def _load(self, contract_id: str, tenant_id: Optional[str]) -> list[dict[str, Any]]:
        async with db.async_session_maker() as session:
            stmt = (select(DocumentChunk, DocumentVersion, DocumentRecord, Contract)
                    .join(DocumentVersion, DocumentChunk.version_id == DocumentVersion.id)
                    .join(DocumentRecord, DocumentVersion.document_id == DocumentRecord.id)
                    .join(Contract, DocumentRecord.contract_id == Contract.id)
                    .where(Contract.id == contract_id, DocumentVersion.id == DocumentRecord.current_version_id))
            if tenant_id:
                from app.models.workspace import Workspace
                stmt = stmt.join(Workspace, Contract.workspace_id == Workspace.id).where(Workspace.tenant_id == tenant_id)
            rows = (await session.execute(stmt)).all()
        return [self._format(chunk, version, record) for chunk, version, record, _ in rows]

    @staticmethod
    def _format(chunk, version, record) -> dict[str, Any]:
        return {
            "id": str(chunk.id), "chunk_id": str(chunk.id), "content": chunk.text,
            "document_id": str(record.id), "document_version_id": str(version.id),
            "version_id": str(version.id), "block_ids": chunk.block_ids or [],
            "span_ids": chunk.span_ids or [], "chunk_type": chunk.chunk_type,
            "parent_chunk_id": chunk.parent_chunk_id, "parent_text": chunk.parent_text, "section_id": chunk.section_id,
            "page_start": chunk.page_start, "page_end": chunk.page_end,
            "char_start": chunk.char_start, "char_end": chunk.char_end,
            "token_count": chunk.token_count, "is_complete_clause": bool(chunk.is_complete_clause),
            "section_path": chunk.section_path, "embedding": chunk.embedding,
            "embedding_model": chunk.embedding_model,
            "source_type": "contract_chunk", "title": chunk.section_path or "合同条款",
        }

    async def lexical(self, query: str, contract_id: str, tenant_id: Optional[str], top_k: int) -> list[dict[str, Any]]:
        rows = await self._load(contract_id, tenant_id)
        texts = [row["content"] for row in rows]
        df = Counter(term for text in texts for term in set(_tokens(text)))
        avg_len = sum(len(_tokens(text)) for text in texts) / max(len(texts), 1)
        scored = []
        for row, text in zip(rows, texts):
            score = bm25_score(query, text, len(rows), df, avg_len)
            if score > 0:
                item = dict(row, bm25_score=score)
                scored.append(item)
        scored.sort(key=lambda item: (-item["bm25_score"], item["id"]))
        for rank, item in enumerate(scored[:top_k], 1): item["bm25_rank"] = rank
        return scored[:top_k]

    async def vector(self, query: str, contract_id: str, tenant_id: Optional[str], top_k: int) -> list[dict[str, Any]]:
        if not settings.is_postgresql or (settings.EMBEDDING_PROVIDER.lower() == "zhipu" and not settings.ZHIPU_EMBEDDING_API_KEY):
            return []
        rows = await self._load(contract_id, tenant_id)
        rows = [row for row in rows if row.get("embedding") and row.get("embedding_model", "").startswith(f"{embedder.provider_name}:")]
        if not rows:
            return []
        query_vector = await embedder.embed(query)
        # The embedding column is text for SQLite compatibility; PostgreSQL
        # casts it to pgvector at query time and can use the migration index.
        from sqlalchemy import text
        ids = [row["id"] for row in rows]
        async with db.async_session_maker() as session:
            id_array = "{" + ",".join(ids) + "}"
            stmt = text("""
                SELECT id, 1 - (embedding::vector <=> CAST(:query_vector AS vector)) AS score
                FROM document_chunks WHERE id = ANY(CAST(:ids AS text[]))
                ORDER BY embedding::vector <=> CAST(:query_vector AS vector) LIMIT :top_k
            """).bindparams(query_vector=json.dumps(query_vector), ids=id_array, top_k=top_k)
            result = await session.execute(stmt)
            scores = {str(row.id): float(row.score) for row in result}
        output = []
        for rank, row in enumerate(sorted(rows, key=lambda item: scores.get(item["id"], -1), reverse=True)[:top_k], 1):
            output.append(dict(row, score=scores[row["id"]], vector_score=scores[row["id"]], vector_rank=rank))
        return output


contract_chunk_retriever = ContractChunkRetriever()
