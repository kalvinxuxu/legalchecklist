from app.schemas.document import UnifiedDocument, DocumentPage

def test_ast_debug_payload_can_be_bounded():
    doc=UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1", text="x"*200000, pages=[])
    payload=doc.model_dump(mode="json")
    payload["text"]=payload["text"][:100000]
    assert len(payload["text"]) == 100000
