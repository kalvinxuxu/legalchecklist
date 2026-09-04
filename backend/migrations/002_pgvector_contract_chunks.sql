-- Production vector storage. Run after enabling the PostgreSQL extension.
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE document_chunks
  ADD COLUMN IF NOT EXISTS embedding text;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_model varchar(120);

-- The ORM keeps text storage for SQLite compatibility; production converts it
-- to a native pgvector column before the HNSW index is created.
ALTER TABLE document_chunks
  ALTER COLUMN embedding TYPE vector(1024)
  USING CASE WHEN embedding IS NULL THEN NULL ELSE embedding::vector END;

CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
  ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS ix_document_chunks_version
  ON document_chunks (version_id);

ALTER TABLE legal_knowledge ADD COLUMN IF NOT EXISTS embedding_vector text;
ALTER TABLE legal_knowledge ADD COLUMN IF NOT EXISTS embedding_model varchar(120);
ALTER TABLE legal_knowledge ALTER COLUMN embedding_vector TYPE vector(1024)
  USING CASE WHEN embedding_vector IS NULL THEN NULL ELSE embedding_vector::vector END;
CREATE INDEX IF NOT EXISTS ix_legal_knowledge_embedding_hnsw
  ON legal_knowledge USING hnsw (embedding_vector vector_cosine_ops);
