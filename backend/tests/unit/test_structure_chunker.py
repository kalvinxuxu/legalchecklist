from app.schemas.document import UnifiedDocument, DocumentPage, DocumentBlock
from app.services.rag.structure_chunker import chunk_document, semantic_boundary_scores

def test_chunks_keep_block_and_page_provenance():
    blocks=[DocumentBlock(block_id="b1", text="第一条", char_start=0, char_end=3, reading_order=0), DocumentBlock(block_id="b2", text="第二条", char_start=3, char_end=6, reading_order=1)]
    doc=UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1", text="第一条\n第二条", pages=[DocumentPage(page_id="p", page_number=0, width=100, height=100, reading_order=0, blocks=blocks)])
    chunks=chunk_document(doc, max_chars=100)
    assert chunks[0]["block_ids"] == ["b1", "b2"] and chunks[0]["page_start"] == 0
    assert chunks[0]["section_id"] is None
    assert chunks[0]["token_count"] > 0


def test_nested_sections_keep_hierarchy_and_span_provenance():
    blocks = [
        DocumentBlock(block_id="h1", block_type="heading", text="第三章 履行", char_start=0, char_end=6, reading_order=0),
        DocumentBlock(block_id="h2", block_type="heading", text="12.3 逾期责任", char_start=6, char_end=14, reading_order=1),
        DocumentBlock(block_id="b", text="甲方有权要求乙方承担责任。", char_start=14, char_end=27, reading_order=2),
    ]
    chunks = chunk_document(UnifiedDocument(document_id="d", version_id="v", parser_name="test", parser_version="1",
        pages=[DocumentPage(page_id="p", page_number=0, width=100, height=100, reading_order=0, blocks=blocks)]))
    assert chunks[0]["section_path"] == "第三章 履行 > 12.3 逾期责任"
    assert chunks[0]["section_id"] == "12.3"


def test_semantic_boundary_scores_are_optional_and_deterministic():
    vectors = {"a": [1.0, 0.0], "b": [0.99, 0.01], "c": [0.0, 1.0]}
    scores = semantic_boundary_scores(["a", "b", "c"], vectors.__getitem__)
    assert len(scores) == 2
    assert scores[0] < scores[1]
