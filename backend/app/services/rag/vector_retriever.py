"""
RAG 检索器：法律知识检索（Chroma 向量数据库）
"""
from typing import List, Dict, Any, Optional
from app.db.session import db as database
from app.models.legal_knowledge import LegalKnowledge
from app.services.rag.chroma_store import chroma_store, TenantAwareChromaStore
from app.services.rag.embedder import embedder
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class VectorRAGRetriever:
    """法律知识 RAG 检索器 - Chroma 向量版"""

    def __init__(self):
        self.embedding_dimension = settings.EMBEDDING_DIMENSION

    async def retrieve(
        self,
        query: str,
        content_type: Optional[str] = None,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        use_vector: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        检索相关法律知识
        """
        if use_vector:
            return await self._chroma_search(query, content_type, top_k, tenant_id)
        else:
            return await self._fallback_db_search(query, content_type, top_k, tenant_id)

    async def _chroma_search(
        self,
        query: str,
        content_type: Optional[str],
        top_k: int,
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """基于 Chroma 的向量语义检索"""
        try:
            store = TenantAwareChromaStore(tenant_id=tenant_id)
            results = await store.query(
                query_text=query,
                n_results=top_k,
                content_type=content_type,
                include_private=True
            )

            formatted = []
            for r in results:
                formatted.append({
                    "id": r["id"],
                    "title": r["metadata"].get("title", ""),
                    "content": r["content"],
                    "content_type": r["metadata"].get("content_type", ""),
                    "metadata": r["metadata"],
                    "score": r["score"],
                    "tenant_id": r.get("tenant_id")
                })

            logger.info(f"[VectorRAG] Chroma search returned {len(formatted)} results")
            return formatted

        except Exception as e:
            logger.warning(f"[VectorRAG] Chroma search failed: {e}, falling back to DB")
            return await self._fallback_db_search(query, content_type, top_k, tenant_id)

    async def _fallback_db_search(
        self,
        query: str,
        content_type: Optional[str],
        top_k: int,
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """降级方案：数据库 LIKE 模糊搜索"""
        from sqlalchemy import select, or_

        conditions = [
            or_(
                LegalKnowledge.title.ilike(f"%{query}%"),
                LegalKnowledge.content.ilike(f"%{query}%")
            )
        ]

        if content_type:
            conditions.append(LegalKnowledge.content_type == content_type)

        if tenant_id:
            conditions.append(
                or_(
                    LegalKnowledge.tenant_id == tenant_id,
                    LegalKnowledge.tenant_id.is_(None)
                )
            )
        else:
            conditions.append(LegalKnowledge.tenant_id.is_(None))

        stmt = select(LegalKnowledge).where(*conditions).limit(top_k)

        async with database.async_session_maker() as session:
            result = await session.execute(stmt)
            rows = result.scalars().all()

            return [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "content": row.content,
                    "content_type": row.content_type,
                    "metadata": json.loads(row.metadata_json) if row.metadata_json else {},
                    "score": 0.5,
                    "tenant_id": row.tenant_id
                }
                for row in rows
            ]

    async def add_knowledge(
        self,
        title: str,
        content: str,
        content_type: str,
        metadata: Optional[dict] = None,
        tenant_id: Optional[str] = None,
        generate_embedding: bool = True,
        knowledge_id: Optional[str] = None
    ) -> str:
        """添加法律知识到向量库"""
        import uuid

        knowledge_id = knowledge_id or str(uuid.uuid4())
        text_to_embed = f"{title} {content}"

        full_metadata = {
            **(metadata or {}),
            "title": title,
            "content_type": content_type,
            "tenant_id": tenant_id
        }

        # 添加到 Chroma
        if generate_embedding:
            try:
                await chroma_store.add(
                    texts=[text_to_embed],
                    metadatas=[full_metadata],
                    ids=[knowledge_id]
                )
                logger.info(f"[VectorRAG] Added to Chroma: {knowledge_id}")
            except Exception as e:
                logger.warning(f"[VectorRAG] Failed to add to Chroma: {e}")

        # 同步到关系数据库
        async with database.async_session_maker() as session:
            from app.models.legal_knowledge import LegalKnowledge

            knowledge = LegalKnowledge(
                id=knowledge_id,
                title=title,
                content=content,
                content_type=content_type,
                metadata_json=full_metadata,
                tenant_id=tenant_id
            )
            session.add(knowledge)
            await session.commit()
            logger.info(f"[VectorRAG] Added to DB: {knowledge_id}")

        return knowledge_id

    async def batch_add_knowledge(
        self,
        knowledge_list: List[Dict[str, Any]],
        generate_embeddings: bool = True
    ) -> List[str]:
        """批量添加法律知识"""
        import uuid

        ids = []
        chroma_texts = []
        chroma_metadatas = []
        chroma_ids = []

        if generate_embeddings:
            for item in knowledge_list:
                knowledge_id = str(uuid.uuid4())
                text_to_embed = f"{item['title']} {item['content']}"
                full_metadata = {
                    **(item.get("metadata", {})),
                    "title": item["title"],
                    "content_type": item["content_type"],
                    "tenant_id": item.get("tenant_id")
                }
                chroma_texts.append(text_to_embed)
                chroma_metadatas.append(full_metadata)
                chroma_ids.append(knowledge_id)

        # 批量添加到 Chroma
        if generate_embeddings and chroma_texts:
            try:
                await chroma_store.add(
                    texts=chroma_texts,
                    metadatas=chroma_metadatas,
                    ids=chroma_ids
                )
                logger.info(f"[VectorRAG] Batch added {len(chroma_ids)} to Chroma")
            except Exception as e:
                logger.warning(f"[VectorRAG] Batch Chroma add failed: {e}")

        # 同步到关系数据库
        async with database.async_session_maker() as session:
            from app.models.legal_knowledge import LegalKnowledge

            for i, item in enumerate(knowledge_list):
                knowledge_id = chroma_ids[i] if generate_embeddings else str(uuid.uuid4())
                ids.append(knowledge_id)

                knowledge = LegalKnowledge(
                    id=knowledge_id,
                    title=item["title"],
                    content=item["content"],
                    content_type=item["content_type"],
                    metadata_json=item.get("metadata", {}),
                    tenant_id=item.get("tenant_id")
                )
                session.add(knowledge)

            await session.commit()

        logger.info(f"[VectorRAG] Batch added {len(ids)} to DB")
        return ids


# 全局检索器实例
retriever = VectorRAGRetriever()
