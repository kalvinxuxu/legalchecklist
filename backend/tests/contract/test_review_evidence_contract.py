import json
from pathlib import Path

def test_review_evidence_contract_supports_multiple_locations():
    schema=json.loads((Path(__file__).parents[3]/"specs/001-unified-document-ingestion/contracts/review-evidence.json").read_text(encoding="utf-8"))
    location_fields=schema["risk_clause_additions"]["evidence"][0]
    assert "locations" in location_fields and "span_ids" in location_fields
