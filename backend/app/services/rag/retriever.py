"""
RAG 检索器 - 兼容性别名

此文件保留用于向后兼容。
实际检索逻辑已迁移到 vector_retriever.py
"""
# 重新导出，保持向后兼容
from app.services.rag.hybrid_retriever import retriever, HybridRetriever
from app.services.rag.vector_retriever import VectorRAGRetriever

__all__ = ["retriever", "HybridRetriever", "VectorRAGRetriever"]
