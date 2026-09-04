from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock
from app.services.rag.structure_chunker import chunk_document

def test_ast_snapshot_is_source_for_text_and_chunks():
    block=DocumentBlock(block_id="b", block_type="heading", text="第一条", char_start=0, char_end=3, reading_order=0)
    doc=UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1", text="第一条", pages=[DocumentPage(page_id="p", page_number=0, width=100, height=100, reading_order=0, blocks=[block])])
    assert chunk_document(doc)[0]["text"] == doc.text
