from app.schemas.document import BBox
from app.schemas.evidence import EvidenceLocation, ReviewEvidence

def test_review_evidence_keeps_pdf_bbox_audit_chain():
    evidence=ReviewEvidence(evidence_id="e", document_id="d", version_id="v", quote="条款", locations=[EvidenceLocation(page=1, span_id="s", bbox=BBox(x0=1,y0=2,x1=3,y1=4))], match_type="id_exact", confidence=1)
    assert evidence.locations[0].page == 1 and evidence.locations[0].span_id == "s"
