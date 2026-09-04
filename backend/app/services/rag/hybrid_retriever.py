import asyncio
from typing import Any, Optional
from app.services.rag.vector_retriever import VectorRAGRetriever
from app.services.rag.bm25_retriever import bm25_retriever
from app.services.rag.rank_fusion import reciprocal_rank_fusion
from app.services.rag.reranker import reranker
from app.core.config import settings
from app.services.rag.contract_chunk_retriever import contract_chunk_retriever

class HybridRetriever:
    def __init__(self, vector=None, lexical=None):
        self.vector = vector or VectorRAGRetriever()
        self.lexical = lexical or bm25_retriever

    async def retrieve(self, query: str, content_type: Optional[str] = None, top_k: int = 5,
                       tenant_id: Optional[str] = None, use_vector: bool = True, use_hybrid: bool | None = None) -> list[dict[str, Any]]:
        use_hybrid = settings.RAG_HYBRID_ENABLED if use_hybrid is None else use_hybrid
        candidate_k = min(max(top_k * 4, settings.RAG_BM25_CANDIDATE_K, settings.RAG_VECTOR_CANDIDATE_K), settings.RAG_RERANKER_CANDIDATE_K)
        vector_task = self.vector.retrieve(query, content_type, candidate_k, tenant_id) if use_vector else asyncio.sleep(0, result=[])
        lexical_task = self.lexical.retrieve(query, content_type, candidate_k, tenant_id) if use_hybrid else asyncio.sleep(0, result=[])
        vectors, lexical = await asyncio.gather(vector_task, lexical_task, return_exceptions=True)
        vectors = [] if isinstance(vectors, Exception) else vectors
        lexical = [] if isinstance(lexical, Exception) else lexical
        if not vectors and not lexical:
            return []
        if not lexical:
            fused = [dict(item, vector_score=item.get("score", 0.0), vector_rank=i + 1, fused_score=1 / (settings.RAG_RRF_K + i + 1)) for i, item in enumerate(vectors)]
        elif not vectors:
            fused = reciprocal_rank_fusion([], lexical)
        else:
            fused = reciprocal_rank_fusion(vectors, lexical)
        result = reranker.rerank(query, fused, top_k)
        mode = "hybrid_rrf_rerank" if vectors and lexical else "vector_rerank" if vectors else "bm25_rerank"
        for item in result: item["retrieval_mode"] = mode
        return result

    async def retrieve_contract_chunks(self, query: str, contract_id: str,
                                       tenant_id: Optional[str] = None,
                                       top_k: int = 8) -> list[dict[str, Any]]:
        """Retrieve the current contract's clauses through the same pipeline."""
        candidate_k = min(max(top_k * 2, settings.RAG_CONTRACT_CANDIDATE_K), settings.RAG_RERANKER_CANDIDATE_K)
        lexical_task = contract_chunk_retriever.lexical(query, contract_id, tenant_id, candidate_k)
        vector_task = contract_chunk_retriever.vector(query, contract_id, tenant_id, candidate_k)
        lexical, vectors = await asyncio.gather(lexical_task, vector_task, return_exceptions=True)
        lexical = [] if isinstance(lexical, Exception) else lexical
        vectors = [] if isinstance(vectors, Exception) else vectors
        if not lexical and not vectors:
            return []
        if lexical and vectors:
            fused = reciprocal_rank_fusion(vectors, lexical)
        elif lexical:
            fused = reciprocal_rank_fusion([], lexical)
        else:
            fused = [dict(item, fused_score=1 / (settings.RAG_RRF_K + i + 1)) for i, item in enumerate(vectors)]
        result = reranker.rerank(query, fused, top_k)
        mode = "contract_hybrid_rrf_rerank" if vectors and lexical else "contract_vector_rerank" if vectors else "contract_bm25_rerank"
        for item in result:
            item["retrieval_mode"] = mode
        return result

retriever = HybridRetriever()
