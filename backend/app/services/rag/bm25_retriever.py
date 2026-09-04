"""Portable BM25-style lexical retrieval over the PostgreSQL source table.

The scoring implementation is intentionally database-independent so local SQLite
and Railway PostgreSQL produce the same ranking. PostgreSQL FTS can replace the
candidate scan later without changing the result contract.
"""
import math, re, json
from collections import Counter
from typing import Any, Optional
from sqlalchemy import select, or_, func
from app.db.session import db as database
from app.models.legal_knowledge import LegalKnowledge

_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)

def _tokens(value: str) -> list[str]:
    # Chinese is kept as individual characters to make exact legal terms useful
    # even when no external tokenizer is installed.
    raw = _TOKEN_RE.findall((value or "").lower())
    return [c for token in raw for c in token] if any("\u4e00" <= c <= "\u9fff" for c in "".join(raw)) else raw

def bm25_score(query: str, text: str, document_count: int, document_frequency: dict[str, int], avg_len: float) -> float:
    q = Counter(_tokens(query)); words = _tokens(text); counts = Counter(words)
    if not q or not words: return 0.0
    k1, b = 1.2, 0.75
    score = 0.0
    for term, qf in q.items():
        df = document_frequency.get(term, 0)
        if not df: continue
        idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
        tf = counts[term]
        score += idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * len(words) / max(avg_len, 1)))) * min(qf, 2)
    return round(score, 6)

class BM25Retriever:
    async def retrieve(self, query: str, content_type: Optional[str] = None, top_k: int = 20, tenant_id: Optional[str] = None) -> list[dict[str, Any]]:
        conditions = []
        if content_type: conditions.append(LegalKnowledge.content_type == content_type)
        if tenant_id: conditions.append(or_(LegalKnowledge.tenant_id == tenant_id, LegalKnowledge.tenant_id.is_(None)))
        else: conditions.append(LegalKnowledge.tenant_id.is_(None))
        async with database.async_session_maker() as session:
            if database.engine and database.engine.dialect.name == "postgresql":
                # PostgreSQL's simple configuration is language-neutral and works
                # for English/legal identifiers; Chinese falls through to the
                # portable scorer when the FTS query yields no candidates.
                document = func.to_tsvector("simple", LegalKnowledge.title + " " + LegalKnowledge.content)
                query_vector = func.plainto_tsquery("simple", query)
                stmt = select(LegalKnowledge, func.ts_rank_cd(document, query_vector).label("fts_score")).where(*conditions).where(document.op("@@")(query_vector)).order_by(func.ts_rank_cd(document, query_vector).desc()).limit(top_k * 4)
                fts_rows = list((await session.execute(stmt)).all())
                if fts_rows:
                    return [self._format(row, float(score), rank) for rank, (row, score) in enumerate(fts_rows, 1)]
            rows = list((await session.execute(select(LegalKnowledge).where(*conditions).limit(500))).scalars().all())
        texts = [f"{row.title}\n{row.content}" for row in rows]
        df = Counter(term for text in texts for term in set(_tokens(text)))
        avg_len = sum(len(_tokens(text)) for text in texts) / max(len(texts), 1)
        ranked = []
        for row, text in zip(rows, texts):
            score = bm25_score(query, text, len(rows), df, avg_len)
            if score <= 0: continue
            metadata = row.metadata_json or {}
            if isinstance(metadata, str):
                try: metadata = json.loads(metadata)
                except json.JSONDecodeError: metadata = {}
            ranked.append(self._format(row, score, None, metadata))
        ranked.sort(key=lambda item: (-item["bm25_score"], item["id"]))
        for rank, item in enumerate(ranked[:top_k], 1): item["bm25_rank"] = rank
        return ranked[:top_k]

    @staticmethod
    def _format(row, score: float, rank: int | None, metadata=None) -> dict[str, Any]:
        metadata = metadata if metadata is not None else (row.metadata_json or {})
        if isinstance(metadata, str):
            try: metadata = json.loads(metadata)
            except json.JSONDecodeError: metadata = {}
        result = {"id": str(row.id), "title": row.title, "content": row.content,
            "content_type": row.content_type, "metadata": metadata, "bm25_score": score,
            "tenant_id": row.tenant_id}
        if rank is not None: result["bm25_rank"] = rank
        return result

bm25_retriever = BM25Retriever()
