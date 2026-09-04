from app.schemas.document import DocumentBlock, DocumentPage, UnifiedDocument
from app.services.rag.structure_chunker import chunk_document


def make_doc(blocks):
    return UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1",
        pages=[DocumentPage(page_id="p", page_number=0, width=100, height=100, reading_order=0, blocks=blocks)])


def test_section_path_and_stable_chunk_id():
    chunks = chunk_document(make_doc([
        DocumentBlock(block_id="h", block_type="heading", text="第八条 付款", char_start=0, char_end=6, reading_order=0),
        DocumentBlock(block_id="b", text="甲方应在三十日内付款。", char_start=6, char_end=18, reading_order=1),
    ]), max_chars=100)
    assert chunks[0]["section_path"] == "第八条 付款"
    assert chunks[0]["chunk_id"] == chunk_document(make_doc([
        DocumentBlock(block_id="h", block_type="heading", text="第八条 付款", char_start=0, char_end=6, reading_order=0),
        DocumentBlock(block_id="b", text="甲方应在三十日内付款。", char_start=6, char_end=18, reading_order=1),
    ]), max_chars=100)[0]["chunk_id"]


def test_long_clause_has_overlap_and_bounded_parts():
    text = "付款条件" + "甲方应当在合同生效后按约支付款项。" * 100
    chunks = chunk_document(make_doc([DocumentBlock(block_id="b", text=text, char_start=0, char_end=len(text), reading_order=0)]), max_chars=180, overlap_chars=30)
    assert len(chunks) > 2
    assert all(len(item["text"]) <= 180 for item in chunks)
    assert any(item["overlap_from_previous"] for item in chunks[1:])
    assert all(item["chunk_type"] == "child" for item in chunks)
    assert all(item["parent_chunk_id"] for item in chunks)
