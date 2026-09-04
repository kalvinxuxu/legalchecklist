-- PostgreSQL lexical retrieval support. Run after legal_knowledge exists.
-- The simple configuration is deliberately language-neutral; Chinese deployments
-- may additionally enable pg_bigm without changing the application contract.
CREATE INDEX IF NOT EXISTS idx_legal_knowledge_fts
ON legal_knowledge USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, '')));

CREATE INDEX IF NOT EXISTS idx_document_chunks_fts
ON document_chunks USING GIN (to_tsvector('simple', coalesce(text, '')));
