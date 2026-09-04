"""
RAG 服务模块
"""
from app.services.rag.hybrid_retriever import retriever, HybridRetriever
from app.services.rag.vector_retriever import VectorRAGRetriever
from app.services.rag.embedder import embedder, ZhipuEmbedder

# 默认导出：向量检索器
# 自动根据数据库类型选择：
#   - PostgreSQL: 使用 pgvector 向量检索
#   - SQLite/MySQL: 降级为 LIKE 模糊搜索

__all__ = [
    "retriever",
    "VectorRAGRetriever", "HybridRetriever",
    "embedder",
    "ZhipuEmbedder",
]
