"""
RAG 检索器：法律知识检索（SQLite 兼容版）
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from app.db.session import db as database
from app.models.legal_knowledge import LegalKnowledge
from sqlalchemy import select
import json


class LegalRAGRetriever:
    """法律知识 RAG 检索器 - SQLite 兼容版"""

    def __init__(self):
        pass

    async def retrieve(
        self,
        query: str,
        content_type: Optional[str] = None,
        top_k: int = 5,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关法律知识

        Args:
            query: 查询文本
            content_type: 内容类型过滤 (law/case/template/rule)
            top_k: 返回结果数量
            tenant_id: 租户 ID（用于私有库检索）

        Returns:
            检索结果列表
        """
        results = await self._search_by_like(query, content_type, top_k, tenant_id)
        return results

    async def _search_by_like(
        self,
        query: str,
        content_type: Optional[str],
        top_k: int,
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        基于 SQLite LIKE 的模糊搜索（兼容 MySQL 全文搜索）

        使用 LIKE 进行中文模糊匹配
        """
        # 使用同步方式获取会话，避免 async generator 问题
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select

        async with database.async_session_maker() as session:
            # 构建搜索条件 - 使用 LIKE 代替 MATCH AGAINST
            conditions = ["(title LIKE :query OR content LIKE :query)"]
            params = {"query": f"%{query}%"}

            # 内容类型过滤
            if content_type:
                conditions.append("content_type = :content_type")
                params["content_type"] = content_type

            # 租户隔离：公共库 + 私有库
            if tenant_id:
                conditions.append("(tenant_id IS NULL OR tenant_id = :tenant_id)")
                params["tenant_id"] = tenant_id
            else:
                conditions.append("tenant_id IS NULL")

            # SQLite 使用 LENGTH 计算长度排序相关性
            sql = f"""
                SELECT id, title, content, content_type, metadata_json, tenant_id,
                       LENGTH(title) + LENGTH(content) AS relevance
                FROM legal_knowledge
                WHERE {' AND '.join(conditions)}
                ORDER BY relevance ASC
                LIMIT :limit
            """
            params["limit"] = top_k

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
        tenant_id: Optional[str] = None
    ) -> str:
        """
        添加法律知识到库中

        Args:
            title: 标题
            content: 内容
            content_type: 类型 (law/case/template/rule)
            metadata: 元数据
            tenant_id: 租户 ID（私有库）

        Returns:
            新知识 ID
        """
        import uuid

        async for session in get_db():
            knowledge_id = str(uuid.uuid4())

            from app.models.legal_knowledge import LegalKnowledge
            knowledge = LegalKnowledge(
                id=knowledge_id,
                title=title,
                content=content,
                content_type=content_type,
                metadata_json=metadata or {},
                tenant_id=tenant_id
            )
            session.add(knowledge)
            await session.commit()

            return knowledge_id

    async def batch_add_knowledge(
        self,
        knowledge_list: List[Dict[str, Any]]
    ) -> List[str]:
        """
        批量添加法律知识

        Args:
            knowledge_list: 知识列表，每个元素包含 title, content, content_type, metadata

        Returns:
            新知识 ID 列表
        """
        import uuid
        from app.models.legal_knowledge import LegalKnowledge

        ids = []
        async for session in get_db():
            for item in knowledge_list:
                knowledge_id = str(uuid.uuid4())
                knowledge = LegalKnowledge(
                    id=knowledge_id,
                    title=item["title"],
                    content=item["content"],
                    content_type=item["content_type"],
                    metadata_json=item.get("metadata", {}),
                    tenant_id=item.get("tenant_id")
                )
                session.add(knowledge)
                ids.append(knowledge_id)
            await session.commit()

        return ids


# 全局检索器实例
retriever = LegalRAGRetriever()
