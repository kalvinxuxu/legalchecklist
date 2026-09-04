"""Migrate legacy Chroma knowledge embeddings into PostgreSQL pgvector.

The operation is idempotent and never deletes Chroma data. Use --apply only
after the target migration has been applied and a backup is available.
"""
import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.config import settings
from app.db.session import db
from app.models.legal_knowledge import LegalKnowledge
from app.services.rag.chroma_store import ChromaStore


def checksum(text: str, embedding: list[float]) -> str:
    return hashlib.sha256((text + json.dumps(embedding, separators=(",", ":"))).encode()).hexdigest()


async def migrate(apply: bool) -> dict:
    if not settings.is_postgresql:
        raise RuntimeError("Set DATABASE_TYPE=postgresql for migration")
    db.connect()
    collection = ChromaStore().collection
    payload = collection.get(include=["documents", "metadatas", "embeddings"])
    ids = payload.get("ids") or []
    documents = payload.get("documents") or []
    metadatas = payload.get("metadatas") or []
    embeddings = payload.get("embeddings") or []
    updated = skipped = missing = mismatched = 0
    checksums = []
    async with db.async_session_maker() as session:
        for index, item_id in enumerate(ids):
            row = await session.get(LegalKnowledge, str(item_id))
            vector = embeddings[index] if index < len(embeddings) else None
            if row is None or not vector:
                missing += 1; continue
            text = f"{row.title} {row.content}"
            if index < len(documents) and documents[index] and documents[index] != text:
                mismatched += 1; continue
            checksums.append(checksum(text, vector))
            if row.embedding_vector:
                skipped += 1; continue
            if apply:
                row.embedding_vector = json.dumps(vector, separators=(",", ":"))
                row.embedding = row.embedding or (metadatas[index] if index < len(metadatas) else None)
                row.embedding_model = row.embedding_model or "chroma-import"
            updated += 1
        if apply:
            await session.commit()
    return {"status": "applied" if apply else "dry_run", "source_records": len(ids),
            "updated": updated, "skipped_existing": skipped, "missing_target_or_embedding": missing,
            "content_mismatches": mismatched, "checksums_generated": len(checksums),
            "checksum_algorithm": "sha256(title+content+embedding)"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write vectors; default is dry-run")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(migrate(args.apply)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
