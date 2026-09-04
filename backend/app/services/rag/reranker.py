"""Three-stage legal RAG reranking with explicit model fallback metadata."""
from typing import Any
from app.core.config import settings
from app.services.rag.legal_rank_policy import authority_score, is_eligible, metadata_score
from app.services.rag.reranker_providers import RerankerProvider, RerankScore


class DeterministicFallback:
    provider = "deterministic_fallback"
    model = "lexical-policy-v1"
    version = "1"

    def score(self, query: str, passages: list[str]) -> list[RerankScore]:
        terms = {term for term in query.lower().split() if term}
        return [RerankScore(i, sum(term in passage.lower() for term in terms) / max(len(terms), 1)) for i, passage in enumerate(passages)]


def build_provider() -> RerankerProvider:
    provider = settings.RAG_RERANKER_PROVIDER.lower()
    if provider == "bge_local":
        from app.services.rag.bge_reranker import BGEReranker
        return BGEReranker(settings.RAG_RERANKER_MODEL, settings.RAG_RERANKER_BATCH_SIZE, settings.RAG_RERANKER_CACHE_DIR)
    if provider == "jina":
        if not settings.JINA_API_KEY:
            raise RuntimeError("Jina provider requires JINA_API_KEY")
        from app.services.rag.jina_reranker import JinaReranker
        return JinaReranker(settings.JINA_API_KEY, settings.JINA_RERANKER_MODEL, settings.JINA_BASE_URL, settings.RAG_RERANKER_TIMEOUT_SECONDS)
    return DeterministicFallback()


class StagedReranker:
    def __init__(self, provider: RerankerProvider | None = None):
        self._provider = provider

    def _get_provider(self) -> RerankerProvider:
        if self._provider is None:
            self._provider = build_provider()
        return self._provider

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int = 8) -> list[dict[str, Any]]:
        bounded = candidates[:max(1, min(len(candidates), settings.RAG_RERANKER_CANDIDATE_K))]
        eligible = [item for item in bounded if is_eligible(item)]
        if not eligible:
            return []
        fallback_reason = None
        try:
            provider = self._get_provider()
            scores = {score.index: score.score for score in provider.score(query, [str(i.get("content", "")) for i in eligible])}
        except Exception as exc:
            provider = DeterministicFallback()
            fallback_reason = str(exc)[:240]
            scores = {score.index: score.score for score in provider.score(query, [str(i.get("content", "")) for i in eligible])}
        result = []
        for index, item in enumerate(eligible):
            semantic = max(0.0, min(1.0, float(scores.get(index, 0.0))))
            authority, metadata = authority_score(item), metadata_score(item, query)
            enriched = dict(item)
            enriched.update({"semantic_score": round(semantic, 6), "authority_score": round(authority, 6), "metadata_score": round(metadata, 6),
                             "rerank_score": round(0.75 * semantic + 0.15 * authority + 0.10 * metadata, 6),
                             "reranker_provider": provider.provider, "reranker_model": provider.model,
                             "reranker_version": provider.version, "fallback_reason": fallback_reason})
            result.append(enriched)
        result.sort(key=lambda item: (-item["rerank_score"], -item["authority_score"], str(item.get("id", ""))))
        for rank, item in enumerate(result[:top_k], 1): item["rerank_rank"] = rank
        return result[:top_k]


class FeatureReranker(StagedReranker):
    """Backward-compatible name using the explicit deterministic fallback."""
    def __init__(self):
        super().__init__(DeterministicFallback())


reranker = StagedReranker()
