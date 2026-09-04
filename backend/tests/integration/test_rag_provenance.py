from app.services.rag.structure_chunker import chunk_document
from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock

def test_chunk_provenance_resolves_to_page():
    block=DocumentBlock(block_id="b", text="合同条款", char_start=0, char_end=4, reading_order=0)
    doc=UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1", pages=[DocumentPage(page_id="p", page_number=2, width=100, height=100, reading_order=2, blocks=[block])])
    item=chunk_document(doc)[0]
    assert item["block_ids"] == ["b"] and item["page_start"] == 2
