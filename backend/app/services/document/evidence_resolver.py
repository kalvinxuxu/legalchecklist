from app.schemas.document import UnifiedDocument
from app.schemas.evidence import EvidenceLocation
import re

def resolve_quote(document: UnifiedDocument, quote: str) -> tuple[list[EvidenceLocation], str, float]:
    if not quote:
        return [], "fuzzy_legacy", 0.0

    # 合同条款经常跨 span、block 甚至 page。建立带来源映射的阅读顺序文本，
    # 在整份 AST 上匹配，再把命中字符映射回所有涉及的 bbox。
    source_chars: list[str] = []
    source_refs: list[tuple[int, object, object]] = []

    def append_text(text: str, page_number: int, bbox, span_id: str | None):
        normalized = re.sub(r"\s+", " ", text or "")
        for char in normalized:
            if char.isspace():
                continue
            source_chars.append(char)
            source_refs.append((page_number, bbox, span_id))

    for page in document.pages:
        for block in page.blocks:
            units = block.spans or []
            if units:
                for span in units:
                    append_text(span.text, page.page_number, span.bbox, span.span_id)
            else:
                append_text(block.text, page.page_number, block.bbox, None)

    normalized_quote = re.sub(r"\s+", "", quote)
    haystack = "".join(source_chars)
    start = haystack.find(normalized_quote)
    if start >= 0:
        end = start + len(normalized_quote)
        locations: list[EvidenceLocation] = []
        seen: set[tuple] = set()
        for page_number, bbox, span_id in source_refs[start:end]:
            if bbox is None:
                continue
            key = (page_number, span_id, tuple(bbox.model_dump().items()) if hasattr(bbox, "model_dump") else str(bbox))
            if key in seen:
                continue
            seen.add(key)
            locations.append(EvidenceLocation(page=page_number, bbox=bbox, span_id=span_id))
        if locations:
            return locations, "id_exact", 1.0

    # 无坐标 AST 的降级情况：保留 block 级定位，避免整个证据丢失。
    for page in document.pages:
        for block in page.blocks:
            if normalized_quote in re.sub(r"\s+", " ", block.text or "") and block.bbox:
                return [EvidenceLocation(page=page.page_number, bbox=block.bbox, span_id=None)], "page_only", 0.7
    return [], "fuzzy_legacy", 0.0
