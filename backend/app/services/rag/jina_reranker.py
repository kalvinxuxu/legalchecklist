"""Optional Jina hosted reranker provider."""
from typing import Sequence
import httpx
from app.services.rag.reranker_providers import RerankScore


class JinaReranker:
    provider = "jina"
    version = "api-v1"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float = 8.0):
        self.api_key, self.model, self.base_url, self.timeout = api_key, model, base_url, timeout

    def score(self, query: str, passages: Sequence[str]) -> list[RerankScore]:
        response = httpx.post(
            self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "query": query, "documents": list(passages), "top_n": len(passages), "return_documents": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json().get("results")
        if not isinstance(data, list):
            raise RuntimeError("Jina reranker returned no results")
        return [RerankScore(int(row["index"]), max(0.0, min(1.0, float(row["relevance_score"])))) for row in data]
