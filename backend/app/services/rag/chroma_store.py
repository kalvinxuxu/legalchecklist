"""
Chroma 向量数据库适配层 - 纯 Chromadb 实现
支持多租户隔离、元数据过滤
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.services.rag.embedder import embedder
from app.core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class ChromaStore:
    """Chroma 向量数据库操作接口 - 纯 Chromadb 实现"""

    def __init__(self):
        self._client = None
        self._collection = None

    @property
    def client(self):
        """延迟初始化 Chroma 客户端"""
        if self._client is None:
            persist_dir = getattr(settings, 'CHROMA_PERSIST_DIR', './data/chroma')
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def collection(self):
        """获取或创建 collection"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="legal_knowledge",
                metadata={"description": "法律知识库向量存储"}
            )
        return self._collection

    async def add(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档到向量库

        Args:
            texts: 文档内容列表
            metadatas: 元数据列表 (title, content_type, tenant_id 等)
            ids: ID 列表，默认自动生成

        Returns:
            生成的 ID 列表
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        # 批量生成嵌入
        embeddings = await embedder.embed_batch(texts)

        # 添加到 Chroma
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"[ChromaStore] Added {len(texts)} documents, ids: {ids[:3]}...")
        return ids

    async def query(
        self,
        query_text: str,
        n_results: int = 5,
        tenant_id: Optional[str] = None,
        content_type: Optional[str] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询相似文档

        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            tenant_id: 租户 ID（多租户隔离）
            content_type: 内容类型过滤
            where: 额外的 Chroma where 条件

        Returns:
            检索结果列表
        """
        # 生成查询向量
        query_embedding = await embedder.embed(query_text)

        # 构建 where 条件
        filter_conditions = {}
        if tenant_id:
            filter_conditions["tenant_id"] = tenant_id
        if content_type:
            filter_conditions["content_type"] = content_type
        if where:
            filter_conditions.update(where)

        where_clause = filter_conditions if filter_conditions else None

        # 执行查询
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        # 格式化返回结果
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "id": doc_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": 1 - results['distances'][0][i] if results['distances'] else 0.0,
                    "tenant_id": results['metadatas'][0][i].get("tenant_id") if results['metadatas'] else None
                })

        logger.debug(f"[ChromaStore] Query '{query_text[:30]}...' returned {len(formatted_results)} results")
        return formatted_results

    async def delete(self, ids: List[str]) -> None:
        """删除指定 ID 的文档"""
        self.collection.delete(ids=ids)
        logger.info(f"[ChromaStore] Deleted {len(ids)} documents")

    async def count(self, tenant_id: Optional[str] = None) -> int:
        """统计文档数量"""
        if tenant_id:
            results = self.collection.get(where={"tenant_id": tenant_id})
        else:
            results = self.collection.get()
        return len(results['ids']) if results['ids'] else 0

    async def upsert(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """更新或插入文档"""
        embeddings = await embedder.embed_batch(texts)
        self.collection.upsert(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"[ChromaStore] Upserted {len(ids)} documents")


class TenantAwareChromaStore(ChromaStore):
    """支持租户感知的 ChromaStore"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__()
        self._tenant_id = tenant_id

    async def query(
        self,
        query_text: str,
        n_results: int = 5,
        content_type: Optional[str] = None,
        include_private: bool = True
    ) -> List[Dict[str, Any]]:
        """
        查询 - 自动处理多租户

        Args:
            query_text: 查询文本
            n_results: 返回数量
            content_type: 内容类型过滤
            include_private: 是否包含私有库（租户数据）
        """
        conditions = []

        # 如果没有指定租户，且include_private=True，则返回所有数据（不限制tenant）
        if not self._tenant_id:
            if content_type:
                conditions.append({"content_type": content_type})
            else:
                # 无租户、无content_type过滤，直接查询全部
                return await self._query_no_filter(query_text, n_results, content_type)
        else:
            # 有指定租户
            if include_private:
                conditions.append({"tenant_id": self._tenant_id})
                if content_type:
                    conditions.append({"tenant_id": self._tenant_id, "content_type": content_type})
            # 公共知识（tenant_id 为 NULL）
            if include_private:
                conditions.append({"tenant_id": None})
                if content_type:
                    conditions.append({"tenant_id": None, "content_type": content_type})

        if not conditions:
            return await super().query(query_text, n_results)

        # ChromaDB `where` only supports single condition, so we need separate queries
        # Also ChromaDB doesn't support None values in where clause
        all_results = []
        for cond in conditions:
            # Split compound conditions into single-condition queries
            for key, value in cond.items():
                if value is None:
                    continue  # Skip None values
                single_condition = {key: value}
                try:
                    results = await self._query_single_condition(
                        query_text, n_results, single_condition
                    )
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"[ChromaStore] Query failed for condition {single_condition}: {e}")

        # 去重并按相似度排序
        seen_ids = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x['score'], reverse=True):
            if r['id'] not in seen_ids:
                seen_ids.add(r['id'])
                unique_results.append(r)

        return unique_results[:n_results]

    async def _query_single_condition(
        self,
        query_text: str,
        n_results: int,
        condition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """单条件查询"""
        query_embedding = await embedder.embed(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=condition,
            include=["documents", "metadatas", "distances"]
        )

        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    "id": doc_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": 1 - results['distances'][0][i] if results['distances'] else 0.0,
                    "tenant_id": results['metadatas'][0][i].get("tenant_id") if results['metadatas'] else None
                })

        return formatted

    async def _query_no_filter(
        self,
        query_text: str,
        n_results: int,
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """无租户过滤的查询 - 查询所有数据"""
        query_embedding = await embedder.embed(query_text)

        where_clause = {"content_type": content_type} if content_type else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    "id": doc_id,
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": 1 - results['distances'][0][i] if results['distances'] else 0.0,
                    "tenant_id": results['metadatas'][0][i].get("tenant_id") if results['metadatas'] else None
                })

        logger.debug(f"[ChromaStore] Query no-filter '{query_text[:30]}...' returned {len(formatted)} results")
        return formatted


# 全局实例
chroma_store = ChromaStore()
