from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock, DocumentSpan, BBox
from app.services.document.evidence_resolver import resolve_quote

def test_exact_quote_resolves_span_location():
    span = DocumentSpan(span_id="s1", text="risk clause", char_start=0, char_end=11, bbox=BBox(x0=1,y0=1,x1=10,y1=5))
    block = DocumentBlock(block_id="b1", text="risk clause", char_start=0, char_end=11, reading_order=0, spans=[span])
    page = DocumentPage(page_id="p1", page_number=0, width=100, height=100, reading_order=0, blocks=[block])
    doc = UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1", pages=[page], text="risk clause")
    locations, match_type, confidence = resolve_quote(doc, "risk clause")
    assert locations[0].span_id == "s1" and match_type == "id_exact" and confidence == 1
