"""
RAG 检索器：法律知识检索（PostgreSQL + pgvector 向量版）
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from app.db.session import db as database
from app.models.legal_knowledge import LegalKnowledge
from app.services.rag.embedder import embedder
from app.core.config import settings
import json


class VectorRAGRetriever:
    """法律知识 RAG 检索器 - PostgreSQL + pgvector 向量版"""

    def __init__(self):
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        self._has_pgvector = self._check_pgvector()

    def _check_pgvector(self) -> bool:
        """检查是否启用了 pgvector"""
        return settings.is_postgresql and hasattr(LegalKnowledge, 'embedding')

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

        Args:
            query: 查询文本
            content_type: 内容类型过滤 (law/case/template/rule)
            top_k: 返回结果数量
            tenant_id: 租户 ID（用于私有库检索）
            use_vector: 是否使用向量检索（False 则降级为 LIKE 搜索）

        Returns:
            检索结果列表
        """
        if use_vector and self._has_pgvector:
            return await self._vector_search(query, content_type, top_k, tenant_id)
        else:
            return await self._fallback_like_search(query, content_type, top_k, tenant_id)

    async def _vector_search(
        self,
        query: str,
        content_type: Optional[str],
        top_k: int,
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        基于 pgvector 的向量语义检索
        """
        # 1. 将查询文本向量化
        query_vector = await embedder.embed(query)
        query_vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        # 2. 构建 SQL 查询（使用余弦距离 <=>）
        conditions = ["(embedding IS NOT NULL)"]
        params: Dict[str, Any] = {
            "query_vector": query_vector_str,
            "limit": top_k
        }

        # 内容类型过滤
        if content_type:
            conditions.append("content_type = :content_type")
            params["content_type"] = content_type

        # 租户隔离
        if tenant_id:
            conditions.append("(tenant_id IS NULL OR tenant_id = :tenant_id)")
            params["tenant_id"] = tenant_id
        else:
            conditions.append("tenant_id IS NULL")

        # PostgreSQL 向量检索：余弦距离 (<=>)
        sql = f"""
            SELECT id, title, content, content_type, metadata_json, tenant_id,
                   1 - (embedding <=> :query_vector::vector) AS similarity
            FROM legal_knowledge
            WHERE {' AND '.join(conditions)}
            ORDER BY embedding <=> :query_vector::vector
            LIMIT :limit
        """

        async with database.async_session_maker() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "content": row.content,
                    "content_type": row.content_type,
                    "metadata": json.loads(row.metadata_json) if row.metadata_json else {},
                    "score": float(row.similarity) if row.similarity else 0.0,
                    "tenant_id": row.tenant_id
                }
                for row in rows
            ]

    async def _fallback_like_search(
        self,
        query: str,
        content_type: Optional[str],
        top_k: int,
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        降级方案：LIKE 模糊搜索（SQLite/MySQL 无 pgvector 时使用）
        """
        conditions = ["(title LIKE :query OR content LIKE :query)"]
        params: Dict[str, Any] = {"query": f"%{query}%"}

        if content_type:
            conditions.append("content_type = :content_type")
            params["content_type"] = content_type

        if tenant_id:
            conditions.append("(tenant_id IS NULL OR tenant_id = :tenant_id)")
            params["tenant_id"] = tenant_id
        else:
            conditions.append("tenant_id IS NULL")

        sql = f"""
            SELECT id, title, content, content_type, metadata_json, tenant_id,
                   LENGTH(title) + LENGTH(content) AS relevance
            FROM legal_knowledge
            WHERE {' AND '.join(conditions)}
            ORDER BY relevance ASC
            LIMIT :limit
        """
        params["limit"] = top_k

        async with database.async_session_maker() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "content": row.content,
                    "content_type": row.content_type,
                    "metadata": json.loads(row.metadata_json) if row.metadata_json else {},
                    "score": 1.0 / (row.relevance + 1) if row.relevance else 0.0,
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
        generate_embedding: bool = True
    ) -> str:
        """
        添加法律知识到库中（自动生成向量）

        Args:
            title: 标题
            content: 内容
            content_type: 类型 (law/case/template/rule)
            metadata: 元数据
            tenant_id: 租户 ID（私有库）
            generate_embedding: 是否自动生成向量

        Returns:
            新知识 ID
        """
        import uuid

        knowledge_id = str(uuid.uuid4())
        embedding_vector = None

        # 自动生成向量
        if generate_embedding and self._has_pgvector:
            text_to_embed = f"{title} {content}"
            embedding_vector = await embedder.embed(text_to_embed)

        async for session in database.async_session_maker():
            from app.models.legal_knowledge import LegalKnowledge

            knowledge = LegalKnowledge(
                id=knowledge_id,
                title=title,
                content=content,
                content_type=content_type,
                metadata_json=metadata or {},
                tenant_id=tenant_id,
                embedding=embedding_vector
            )
            session.add(knowledge)
            await session.commit()
            return knowledge_id

    async def batch_add_knowledge(
        self,
        knowledge_list: List[Dict[str, Any]],
        generate_embeddings: bool = True
    ) -> List[str]:
        """
        批量添加法律知识

        Args:
            knowledge_list: 知识列表
            generate_embeddings: 是否批量生成向量

        Returns:
            新知识 ID 列表
        """
        import uuid

        ids = []

        # 批量生成向量（如启用）
        embeddings_map: Dict[str, List[float]] = {}
        if generate_embeddings and self._has_pgvector:
            texts_to_embed = [
                f"{item['title']} {item['content']}"
                for item in knowledge_list
            ]
            # 批量向量化（分批避免超时）
            all_embeddings = []
            batch_size = 32
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i:i+batch_size]
                batch_embeddings = await embedder.embed_batch(batch)
                all_embeddings.extend(batch_embeddings)

            for idx, item in enumerate(knowledge_list):
                embeddings_map[item.get('title', '')] = all_embeddings[idx]

        async for session in database.async_session_maker():
            from app.models.legal_knowledge import LegalKnowledge

            for item in knowledge_list:
                knowledge_id = str(uuid.uuid4())
                knowledge = LegalKnowledge(
                    id=knowledge_id,
                    title=item["title"],
                    content=item["content"],
                    content_type=item["content_type"],
                    metadata_json=item.get("metadata", {}),
                    tenant_id=item.get("tenant_id"),
                    embedding=embeddings_map.get(item.get('title', ''))
                )
                session.add(knowledge)
                ids.append(knowledge_id)

            await session.commit()

        return ids


# 全局检索器实例
retriever = VectorRAGRetriever()
