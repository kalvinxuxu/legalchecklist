import json
from pathlib import Path
from app.schemas.evidence import DocumentChunk


def test_retrieval_contract_declares_three_stage_scores():
    contract = json.loads(Path("specs/001-unified-document-ingestion/contracts/retrieval.json").read_text(encoding="utf-8"))
    assert "stage_1" in contract["pipeline"] and "stage_2" in contract["pipeline"] and "stage_3" in contract["pipeline"]
    assert "semantic_score" in contract["candidate"]
    assert "authority_score" in contract["candidate"]


def test_document_chunk_accepts_retrieval_audit_fields():
    item = DocumentChunk(chunk_id="c", version_id="v", text="条款", semantic_score=.8, authority_score=.9, metadata_score=.7, rerank_score=.83)
    assert item.semantic_score == .8
