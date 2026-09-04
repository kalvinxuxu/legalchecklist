"""Build a deterministic, delivery-safe projection of a review result."""
from typing import Any


def build_opinion(contract_name: str, review_result: dict[str, Any]) -> dict[str, Any]:
    risks = review_result.get("risk_clauses", [])
    missing = review_result.get("missing_clauses", [])
    recommendations = review_result.get("suggestions", [])
    return {
        "schema_version": "1",
        "contract_name": contract_name,
        "confidence_score": review_result.get("confidence_score"),
        "overall_risk_level": review_result.get("overall_risk_level"),
        "risk_clauses": risks,
        "missing_clauses": missing,
        "recommendations": recommendations,
        "evidence_ids": [c["evidence_id"] for c in risks if c.get("evidence_id")],
    }
