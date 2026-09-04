from app.services.review.context_builder import PartitionedContextBuilder


def test_child_context_expands_parent_without_changing_source_id():
    items = [{
        "chunk_id": "child-1", "content": "12.3 逾期责任", "page_start": 3, "page_end": 4,
        "parent_chunk_id": "parent-1", "parent_text": "第十二条 违约责任\n12.3 逾期责任\n12.4 解除责任",
    }]
    expanded = PartitionedContextBuilder.expand_parent_context(items)
    assert expanded[0]["chunk_id"] == "child-1"
    assert "精准子条款" in expanded[0]["content"]
    assert "12.4 解除责任" in expanded[0]["content"]


def test_contract_context_does_not_expand_without_parent_text():
    text = PartitionedContextBuilder.build_contract_context([{"chunk_id": "c1", "content": "普通条款", "page_start": 1, "page_end": 1}])
    assert "普通条款" in text and "完整父条款上下文" not in text
