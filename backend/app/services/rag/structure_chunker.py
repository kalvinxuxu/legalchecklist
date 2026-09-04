"""Structure-first, token-bounded chunking for legal contracts."""
import hashlib
import re
from collections.abc import Callable

from app.core.config import settings
from app.schemas.document import DocumentBlock, UnifiedDocument

_SECTION_RE = re.compile(
    r"^(?P<number>第\s*[一二三四五六七八九十百千万0-9]+\s*[章节条]|"
    r"[一二三四五六七八九十百千万]+[、.]|"
    r"[0-9]+(?:\.[0-9]+)+(?:\([a-zA-Z0-9]+\))?|"
    r"\(?[一二三四五六七八九十0-9]+[)）.]?)"
)
_SENTENCE_RE = re.compile(r"(?<=[。！？；.!?;])\s+|\r?\n+")


def estimate_tokens(text: str) -> int:
    """Cheap multilingual token estimate; no model/tokenizer is loaded at ingestion."""
    if not text:
        return 0
    cjk = len(re.findall(r"[\u3400-\u9fff]", text))
    non_cjk = len(text) - cjk
    return max(1, cjk + (non_cjk + 3) // 4)


def _section_number(text: str) -> str | None:
    match = _SECTION_RE.match((text or "").strip())
    return match.group("number").replace(" ", "") if match else None


def _is_section(block: DocumentBlock) -> bool:
    text = (block.text or "").strip()
    return block.block_type in {"title", "heading"} or (len(text) > 4 and _section_number(text) is not None)


def _split_block(block: DocumentBlock) -> list[dict]:
    text = (block.text or "").strip()
    if not text:
        return []
    units = []
    cursor = 0
    for part in _SENTENCE_RE.split(text):
        value = part.strip()
        if not value:
            continue
        local_start = text.find(value, cursor)
        local_start = max(local_start, cursor)
        local_end = local_start + len(value)
        units.append({
            "text": value, "block_ids": [block.block_id],
            "span_ids": [span.span_id for span in block.spans],
            "char_start": block.char_start + local_start, "char_end": block.char_start + local_end,
        })
        cursor = local_end
    return units or [{
        "text": text, "block_ids": [block.block_id],
        "span_ids": [span.span_id for span in block.spans],
        "char_start": block.char_start, "char_end": block.char_end,
    }]


def semantic_boundary_scores(units: list[str], embed: Callable[[str], list[float]]) -> list[float]:
    """Return adjacent cosine distances for an optional semantic boundary pass."""
    if len(units) < 2:
        return []
    vectors = [embed(unit) for unit in units]
    scores = []
    for left, right in zip(vectors, vectors[1:]):
        left_norm = sum(value * value for value in left) ** 0.5
        right_norm = sum(value * value for value in right) ** 0.5
        similarity = sum(a * b for a, b in zip(left, right)) / max(left_norm * right_norm, 1e-12)
        scores.append(1.0 - similarity)
    return scores


def chunk_document(document: UnifiedDocument, max_chars: int | None = None,
                   overlap_chars: int | None = None, *,
                   target_tokens: int | None = None, max_tokens: int | None = None,
                   overlap_tokens: int | None = None,
                   semantic_embed: Callable[[str], list[float]] | None = None) -> list[dict]:
    """Build clause chunks with section hierarchy, token bounds, and source provenance."""
    max_chars = max_chars or settings.RAG_CHUNK_MAX_CHARS
    overlap_chars = overlap_chars if overlap_chars is not None else settings.RAG_CHUNK_OVERLAP_CHARS
    target_tokens = target_tokens or settings.RAG_CHUNK_TARGET_TOKENS
    max_tokens = max_tokens or settings.RAG_CHUNK_MAX_TOKENS
    overlap_tokens = overlap_tokens if overlap_tokens is not None else settings.RAG_CHUNK_OVERLAP_TOKENS
    hard_overlap_chars = max(1, min(overlap_chars, overlap_tokens * 4))
    chunks = []
    section_stack: list[tuple[int, str, str]] = []
    current: list[dict] = []
    current_section: tuple[str | None, str | None] = (None, None)
    current_has_body = False

    def section_context():
        if not section_stack:
            return None, None
        return section_stack[-1][2], " > ".join(item[1] for item in section_stack)

    def make_chunk(items: list[dict], chunk_type="clause", parent_chunk_id=None, parent_text=None, complete=True):
        text = "\n".join(item["text"] for item in items).strip()
        if not text:
            return None
        section_id, section_path = current_section
        block_ids = list(dict.fromkeys(x for item in items for x in item["block_ids"]))
        span_ids = list(dict.fromkeys(x for item in items for x in item["span_ids"]))
        chunk_id = hashlib.sha256((document.version_id + "|" + text).encode()).hexdigest()[:32]
        return {
            "chunk_id": chunk_id, "version_id": document.version_id, "text": text,
            "chunk_type": chunk_type, "parent_chunk_id": parent_chunk_id,
            "parent_text": parent_text,
            "section_id": section_id, "section_path": section_path,
            "block_ids": block_ids, "span_ids": span_ids,
            "page_start": min(item["page"] for item in items), "page_end": max(item["page"] for item in items),
            "char_start": min(item["char_start"] for item in items),
            "char_end": max(item["char_end"] for item in items),
            "token_count": estimate_tokens(text), "is_complete_clause": complete,
            "text_hash": hashlib.sha256(text.encode()).hexdigest(),
            "overlap_from_previous": False,
        }

    def emit_group(items: list[dict]):
        if not items:
            return
        if semantic_embed and settings.RAG_SEMANTIC_CHUNKING_ENABLED and len(items) > 1:
            texts = [item["text"] for item in items]
            boundaries = semantic_boundary_scores(texts, semantic_embed)
            threshold = settings.RAG_SEMANTIC_BOUNDARY_THRESHOLD
            groups, group = [], [items[0]]
            for item, boundary in zip(items[1:], boundaries):
                if boundary >= threshold:
                    groups.append(group)
                    group = []
                group.append(item)
            groups.append(group)
            if len(groups) > 1:
                for group in groups:
                    emit_group(group)
                return
        full_text = "\n".join(item["text"] for item in items).strip()
        parent_id = hashlib.sha256((document.version_id + "|parent|" + full_text).encode()).hexdigest()[:32]
        is_split = estimate_tokens(full_text) > max_tokens or len(full_text) > max_chars
        if not is_split:
            item = make_chunk(items)
            if item:
                chunks.append(item)
            return
        # Child chunks share a stable parent identity; the parent text is represented by section metadata.
        child: list[dict] = []
        for unit in items:
            proposed = child + [unit]
            proposed_text = "\n".join(x["text"] for x in proposed)
            if child and (estimate_tokens(proposed_text) > max_tokens or len(proposed_text) > max_chars):
                item = make_chunk(child, "child", parent_id, full_text, False)
                if item:
                    chunks.append(item)
                child = []
            if estimate_tokens(unit["text"]) > max_tokens or len(unit["text"]) > max_chars:
                start = 0
                part_index = 0
                while start < len(unit["text"]):
                    end = min(len(unit["text"]), start + max_chars)
                    part = dict(unit, text=unit["text"][start:end],
                                char_start=unit["char_start"] + start, char_end=unit["char_start"] + end)
                    item = make_chunk([part], "child", parent_id, full_text, False)
                    if item:
                        item["overlap_from_previous"] = part_index > 0
                        chunks.append(item)
                    if end == len(unit["text"]):
                        break
                    start = max(start + 1, end - hard_overlap_chars)
                    part_index += 1
                continue
            child.append(unit)
            if estimate_tokens("\n".join(x["text"] for x in child)) >= target_tokens:
                item = make_chunk(child, "child", parent_id, full_text, False)
                if item:
                    chunks.append(item)
                child = []
        if child:
            item = make_chunk(child, "child", parent_id, full_text, False)
            if item:
                chunks.append(item)

    for page in document.pages:
        for block in page.blocks:
            if not (block.text or "").strip():
                continue
            if _is_section(block):
                if current and current_has_body:
                    emit_group(current)
                    current = []
                current_has_body = False
                number = _section_number(block.text) or f"block-{block.block_id}"
                level = number.count(".") + 1
                while section_stack and section_stack[-1][0] >= level:
                    section_stack.pop()
                section_stack.append((level, block.text.strip()[:500], number))
                current_section = section_context()
            for unit in _split_block(block):
                unit["page"] = page.page_number
                current.append(unit)
            if not _is_section(block):
                current_has_body = True
            if block.block_type == "table":
                emit_group(current)
                current = []
                current_has_body = False
    emit_group(current)

    if semantic_embed and settings.RAG_SEMANTIC_CHUNKING_ENABLED:
        for item in chunks:
            item["semantic_boundary_mode"] = "cosine_distance"
    return chunks
