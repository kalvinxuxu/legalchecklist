from app.services.rag.rank_fusion import reciprocal_rank_fusion
from app.services.rag.reranker import FeatureReranker

def test_rrf_merges_duplicate_candidates_and_preserves_scores():
    result = reciprocal_rank_fusion(
        [{"id": "a", "content": "semantic", "score": .8}],
        [{"id": "a", "content": "semantic", "bm25_score": 3.2}],
    )
    assert len(result) == 1
    assert result[0]["vector_score"] == .8
    assert result[0]["bm25_score"] == 3.2
    assert result[0]["fused_score"] > 0

def test_reranker_is_deterministic_and_returns_audit_score():
    items = [{"id": "b", "content": "解除合同", "fused_score": .01}, {"id": "a", "content": "违约责任", "fused_score": .02}]
    first = FeatureReranker().rerank("违约责任", items)
    second = FeatureReranker().rerank("违约责任", items)
    assert [x["id"] for x in first] == [x["id"] for x in second]
    assert "rerank_score" in first[0]
    assert first[0]["semantic_score"] >= 0
    assert first[0]["reranker_provider"] == "deterministic_fallback"


def test_reranker_bounds_candidates_to_top40_and_keeps_stage_scores():
    items = [{"id": str(i), "content": "付款", "fused_score": 0.1, "fused_rank": i + 1} for i in range(50)]
    result = FeatureReranker().rerank("付款", items, top_k=50)
    assert len(result) == 40
    assert {"semantic_score", "authority_score", "metadata_score", "rerank_score"} <= result[0].keys()
