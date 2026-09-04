CREATE TABLE IF NOT EXISTS email_drafts (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    contract_id VARCHAR(36) NOT NULL,
    review_run_id VARCHAR(36),
    opinion_id VARCHAR(36),
    sender_email VARCHAR(320),
    recipients JSONB NOT NULL,
    attachments JSONB NOT NULL DEFAULT '[]'::jsonb,
    subject VARCHAR(500) NOT NULL,
    body_text TEXT NOT NULL,
    body_html TEXT,
    provider VARCHAR(50) NOT NULL DEFAULT 'mock',
    provider_draft_id VARCHAR(255),
    sync_status VARCHAR(30) NOT NULL DEFAULT 'local_saved',
    idempotency_key VARCHAR(128) NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_email_drafts_tenant_idempotency UNIQUE (tenant_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS ix_email_drafts_contract_id ON email_drafts(contract_id);
