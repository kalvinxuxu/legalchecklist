-- Structure-aware chunk metadata and provenance extensions.
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS section_id varchar(120);
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS chunk_type varchar(30) NOT NULL DEFAULT 'clause';
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS parent_chunk_id varchar(36);
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS parent_text text;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS span_ids jsonb;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS char_start integer;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS char_end integer;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS token_count integer;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS is_complete_clause integer NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS ix_document_chunks_section_id ON document_chunks (section_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_parent_chunk_id ON document_chunks (parent_chunk_id);
