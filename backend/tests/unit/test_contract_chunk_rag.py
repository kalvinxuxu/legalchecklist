import pytest

from app.services.rag import hybrid_retriever as module
from app.services.rag.hybrid_retriever import HybridRetriever
from app.services.review.prompt_builder import EnhancedPromptBuilder


class FakeChunks:
    async def lexical(self, query, contract_id, tenant_id, top_k):
        return [{"id": "a", "chunk_id": "a", "content": "付款期限三十日", "bm25_score": 2.0, "bm25_rank": 1}]

    async def vector(self, query, contract_id, tenant_id, top_k):
        return [{"id": "a", "chunk_id": "a", "content": "付款期限三十日", "score": 0.9, "vector_rank": 1}]


class FakeReranker:
    def rerank(self, query, candidates, top_k):
        return [dict(candidates[0], rerank_score=0.88, rerank_rank=1)]


@pytest.mark.asyncio
async def test_contract_chunks_use_hybrid_fusion_and_rerank(monkeypatch):
    monkeypatch.setattr(module, "contract_chunk_retriever", FakeChunks())
    monkeypatch.setattr(module, "reranker", FakeReranker())
    result = await HybridRetriever().retrieve_contract_chunks("付款", "contract-1", "tenant-1")
    assert result[0]["retrieval_mode"] == "contract_hybrid_rrf_rerank"
    assert result[0]["bm25_rank"] == 1
    assert result[0]["vector_rank"] == 1
    assert result[0]["rerank_score"] == 0.88


def test_prompt_contains_contract_chunk_sources():
    prompt = EnhancedPromptBuilder.build_review_prompt(
        contract_text="全文", contract_type="采购合同", law_context="无",
        policy_context="无", rules=[],
        contract_chunk_context="[source_id=chunk-1]\n付款期限三十日",
    )
    assert "chunk-1" in prompt
    assert "合同条款候选区" in prompt
