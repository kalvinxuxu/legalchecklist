"""Stable IDs and text-offset invariants for document provenance."""
import hashlib

def stable_id(*parts: object, prefix: str = "") -> str:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:32]
    return f"{prefix}_{digest}" if prefix else digest

def document_id(file_hash: str) -> str: return stable_id(file_hash, prefix="doc")
def version_id(document: str, parser: str, parser_version: str) -> str:
    return stable_id(document, parser, parser_version, prefix="ver")
def block_id(version: str, page: int, index: int) -> str: return stable_id(version, page, index, prefix="blk")
def span_id(version: str, page: int, block: int, index: int) -> str: return stable_id(version, page, block, index, prefix="spn")

def validate_offsets(text: str, start: int, end: int) -> None:
    if not 0 <= start <= end <= len(text):
        raise ValueError(f"invalid text offsets: {start}:{end} for {len(text)} chars")
