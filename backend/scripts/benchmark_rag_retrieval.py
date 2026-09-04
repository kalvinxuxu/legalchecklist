"""Labeled comparison benchmark for legal retrieval/reranking providers."""
import argparse
import copy
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.rag.legal_rank_policy import is_eligible
from app.services.rag.reranker import FeatureReranker, StagedReranker
from app.services.rag.reranker_providers import RerankScore


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, max(0, int((len(values) - 1) * p / 100)))]


def metrics(rows: list[dict]) -> dict:
    recall, mrr, ndcg, duplicates, authority_violations, latencies = [], [], [], 0, 0, []
    for row in rows:
        relevant = set(row.get("relevant_ids", []))
        results = row.get("results", [])[:10]
        hits = [index + 1 for index, item in enumerate(results) if item in relevant]
        recall.append(bool(hits)); mrr.append(1 / hits[0] if hits else 0)
        ideal = sum(1 / (index + 1) for index in range(min(len(relevant), 10)))
        ndcg.append(sum(1 / (index + 1) for index, item in enumerate(results) if item in relevant) / ideal if ideal else 0)
        duplicates += len(results) != len(set(results))
        authority_violations += sum(not is_eligible(item) for item in row.get("ranked_items", [])[:10])
        latencies.append(row.get("latency_ms", 0))
    count = max(len(rows), 1)
    return {"count": len(rows), "recall_at_10": round(sum(recall) / count, 4), "mrr": round(sum(mrr) / count, 4),
            "ndcg_at_10": round(sum(ndcg) / count, 4), "duplicate_rate": round(duplicates / count, 4),
            "authority_violations": authority_violations, "p95_latency_ms": round(percentile(latencies, 95), 3)}


class OfflineBGE:
    provider, model, version = "bge_local_offline_fixture", "fixture-cross-encoder", "offline-v1"

    def score(self, query, passages):
        terms = set(query.lower().split())
        return [RerankScore(i, sum(term in text.lower() for term in terms) / max(len(terms), 1)) for i, text in enumerate(passages)]


def rank(provider_name: str, row: dict, live: bool) -> list[dict]:
    candidates = copy.deepcopy(row["candidates"])
    if provider_name == "vector_only":
        return sorted(candidates, key=lambda item: (-item.get("vector_score", 0), item["id"]))[:10]
    if provider_name == "legacy_feature":
        return FeatureReranker().rerank(row["query"], candidates, top_k=10)
    if provider_name == "bge_local" and not live:
        return StagedReranker(OfflineBGE()).rerank(row["query"], candidates, top_k=10)
    if provider_name == "bge_local":
        from app.core.config import settings
        from app.services.rag.bge_reranker import BGEReranker
        return StagedReranker(BGEReranker(settings.RAG_RERANKER_MODEL, settings.RAG_RERANKER_BATCH_SIZE, settings.RAG_RERANKER_CACHE_DIR)).rerank(row["query"], candidates, top_k=10)
    if provider_name == "jina":
        from app.core.config import settings
        from app.services.rag.jina_reranker import JinaReranker
        if not settings.JINA_API_KEY:
            raise RuntimeError("JINA_API_KEY is not configured")
        return StagedReranker(JinaReranker(settings.JINA_API_KEY, settings.JINA_RERANKER_MODEL, settings.JINA_BASE_URL, settings.RAG_RERANKER_TIMEOUT_SECONDS)).rerank(row["query"], candidates, top_k=10)
    raise ValueError(provider_name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", default="backend/tests/fixtures/rag/retrieval.json")
    parser.add_argument("--live", action="store_true", help="run real BGE/Jina instead of offline BGE fixture")
    args = parser.parse_args()
    path = Path(args.fixture)
    if not path.exists():
        print(json.dumps({"status": "no_fixture", "path": str(path)})); return
    rows = json.loads(path.read_text(encoding="utf-8"))
    output = {"fixture": str(path), "mode": "live" if args.live else "offline", "providers": {}}
    for name in ("vector_only", "legacy_feature", "bge_local", "jina"):
        evaluated, unavailable = [], None
        try:
            for source in rows:
                started = time.perf_counter(); ranked = rank(name, source, args.live)
                item = copy.deepcopy(source); item["ranked_items"] = ranked
                item["results"] = [candidate["id"] for candidate in ranked]
                item["latency_ms"] = (time.perf_counter() - started) * 1000; evaluated.append(item)
        except Exception as exc:
            unavailable = str(exc)
        output["providers"][name] = {"status": "unavailable", "reason": unavailable} if unavailable else {"status": "ok", **metrics(evaluated)}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
