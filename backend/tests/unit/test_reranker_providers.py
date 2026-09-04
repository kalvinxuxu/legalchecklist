from app.services.rag.reranker import DeterministicFallback, StagedReranker


def test_fallback_is_explicit_and_scores_are_bounded():
    result = StagedReranker(DeterministicFallback()).rerank("违约责任", [{"id": "a", "content": "违约责任", "authority_level": "statute"}])
    assert result[0]["reranker_provider"] == "deterministic_fallback"
    assert 0 <= result[0]["semantic_score"] <= 1
    assert result[0]["fallback_reason"] is None


def test_unavailable_provider_records_fallback_reason():
    class Broken:
        provider = "bge_local"; model = "test"; version = "1"
        def score(self, query, passages): raise RuntimeError("model unavailable")
    result = StagedReranker(Broken()).rerank("付款", [{"id": "a", "content": "付款"}])
    assert result[0]["reranker_provider"] == "deterministic_fallback"
    assert "model unavailable" in result[0]["fallback_reason"]
