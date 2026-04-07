"""
Word 文档辅助编辑服务

提供段落级解析、修订模式生成、建议生成等功能
"""
from .paragraph_indexer import word_indexer
from .revision_doc import revision_doc_generator
from .suggestion_engine import suggestion_engine

__all__ = ["word_indexer", "revision_doc_generator", "suggestion_engine"]
