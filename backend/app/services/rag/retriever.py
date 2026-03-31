"""
RAG 检索器：法律知识检索
"""
from typing import List, Dict, Any
from app.services.rag.embedder import embedder
from app.db.session import get_db
import aiomysql
import json


class LegalRAGRetriever:
    """法律知识 RAG 检索器"""

    def __init__(self):
        self.embedder = embedder

    async def retrieve(
        self,
        query: str,
        content_type: str = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相关法律知识

        Args:
            query: 查询文本
            content_type: 内容类型过滤 (law/case/template/rule)
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        # 1. 生成查询向量
        query_vector = await self.embedder.embed(query)

        # 2. 数据库检索（使用向量相似度）
        # 注：MySQL 本身不支持向量检索，这里使用简化方案
        # 生产环境建议使用 Elasticsearch 或 PGVector
        results = await self._search_by_keywords(query, content_type, top_k)

        return results

    async def _search_by_keywords(
        self,
        query: str,
        content_type: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        基于关键词的简化检索（过渡方案）

        使用 MySQL 全文索引进行检索
        """
        async for db in get_db():
            async with db.cursor() as cursor:
                # 构建搜索条件
                conditions = ["MATCH(title, content) AGAINST(%s IN NATURAL LANGUAGE MODE)"]
                params = [query]

                if content_type:
                    conditions.append("content_type = %s")
                    params.append(content_type)

                sql = f"""
                    SELECT id, title, content, content_type, metadata
                    FROM legal_knowledge
                    WHERE {' AND '.join(conditions)}
                    LIMIT %s
                """
                params.append(top_k)

                await cursor.execute(sql, params)
                rows = await cursor.fetchall()

                return [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "content": row["content"],
                        "content_type": row["content_type"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "score": 1.0  # MySQL 全文搜索无法提供精确相似度分数
                    }
                    for row in rows
                ]

    async def add_knowledge(
        self,
        title: str,
        content: str,
        content_type: str,
        metadata: dict = None
    ) -> str:
        """
        添加法律知识到库中

        Args:
            title: 标题
            content: 内容
            content_type: 类型 (law/case/template/rule)
            metadata: 元数据

        Returns:
            新知识 ID
        """
        import uuid

        async for db in get_db():
            knowledge_id = str(uuid.uuid4())

            async with db.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO legal_knowledge
                    (id, title, content, content_type, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (knowledge_id, title, content, content_type, json.dumps(metadata))
                )
                await db.commit()

            return knowledge_id


# 全局检索器实例
retriever = LegalRAGRetriever()
