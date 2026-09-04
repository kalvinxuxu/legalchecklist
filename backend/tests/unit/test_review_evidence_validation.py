from app.services.review.service import validate_evidence_ids

def test_unknown_evidence_id_is_not_returned_as_valid():
    result = validate_evidence_ids({"risk_clauses": [{"evidence_id": "forged"}]}, {"valid"})
    assert "evidence_id" not in result["risk_clauses"][0]
    assert result["risk_clauses"][0]["evidence_warning"] == "unknown_evidence_id"
