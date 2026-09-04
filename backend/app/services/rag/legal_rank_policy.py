"""Deterministic legal-source policy applied after semantic reranking."""
from datetime import date
from typing import Any

AUTHORITY_LEVELS = {
    "supreme_interpretation": 1.00,
    "guiding_case": 0.90,
    "statute": 0.85,
    "regulation": 0.75,
    "internal_policy": 0.55,
    "article": 0.25,
}


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def is_eligible(item: dict[str, Any], as_of: date | None = None, jurisdiction: str | None = None) -> bool:
    if item.get("source_status") in {"expired", "repealed", "invalid"}:
        return False
    if jurisdiction and item.get("jurisdiction") not in {None, "", jurisdiction}:
        return False
    current = as_of or date.today()
    start, end = _as_date(item.get("effective_from")), _as_date(item.get("effective_to"))
    return not (start and start > current) and not (end and end < current)


def authority_score(item: dict[str, Any]) -> float:
    return AUTHORITY_LEVELS.get(str(item.get("authority_level", "article")), 0.25)


def metadata_score(item: dict[str, Any], query: str = "") -> float:
    score = 0.5
    if item.get("source_status") == "effective": score += 0.3
    if item.get("jurisdiction"): score += 0.1
    if item.get("section_path"): score += 0.1
    return min(score, 1.0)
