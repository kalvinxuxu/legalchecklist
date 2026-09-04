from typing import Any

def reciprocal_rank_fusion(*ranked_lists: list[dict[str, Any]], k: int = 60) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source, items in enumerate(ranked_lists):
        for rank, item in enumerate(items, 1):
            key = str(item["id"])
            current = merged.setdefault(key, dict(item))
            current["fused_score"] = current.get("fused_score", 0.0) + 1 / (k + rank)
            current["vector_rank"] = current.get("vector_rank") if source == 0 else current.get("vector_rank", rank)
            if source == 0: current["vector_score"], current["vector_rank"] = item.get("score", 0.0), rank
            if source == 1: current["bm25_score"], current["bm25_rank"] = item.get("bm25_score", 0.0), rank
    result = sorted(merged.values(), key=lambda x: (-x.get("fused_score", 0), str(x["id"])))
    for rank, item in enumerate(result, 1): item["fused_rank"] = rank
    return result
