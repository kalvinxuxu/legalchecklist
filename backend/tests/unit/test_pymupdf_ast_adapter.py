from app.schemas.document import DocumentBlock, DocumentSpan

def test_ast_block_contains_ordered_spans():
    span=DocumentSpan(span_id="s", text="abc", char_start=0, char_end=3)
    block=DocumentBlock(block_id="b", text="abc", char_start=0, char_end=3, reading_order=0, spans=[span])
    assert block.spans[0].char_start == block.char_start
