import json
from pathlib import Path

def test_ingestion_contract_has_version_and_status_fields():
    contract=json.loads((Path(__file__).parents[3]/"specs/001-unified-document-ingestion/contracts/ingestion.json").read_text(encoding="utf-8"))
    response=contract["response"]
    assert "document_id" in response and "version_id" in response and "status" in response
