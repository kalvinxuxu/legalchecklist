# Data Model: Evidence Navigation and Opinion Delivery

## EvidenceLocation

- `id`: UUID primary key
- `evidence_id`: stable review evidence identity
- `contract_id`, `document_id`, `version_id`: tenant-scoped provenance
- `page`: zero-based PDF page
- `bbox`: `{x0,y0,x1,y1}` in `pdf_top_left`
- `resolution_status`: `resolved | fuzzy_fallback | page_only | unresolved`
- `match_type`, `confidence`, `source_span_ids`: diagnostics

One evidence can have many locations, including multiple pages. Locations are immutable for a document version.

## ReviewOpinion

- `id`, `contract_id`, `review_run_id`, `document_version_id`
- `generated_at`, `schema_version`
- `summary`, `risk_items`, `missing_items`, `recommendations`
- each item carries `evidence_id[]`, severity, original text, explanation, and suggested change

Generated as a projection; it is regenerated when the selected completed review changes.

## EmailDraft

- `id`, `tenant_id`, `contract_id`, `review_run_id`, `opinion_id`
- `to[]`, `cc[]`, `bcc[]`, `subject`, `body_text`, optional `body_html`
- `provider`, `provider_draft_id`, `sync_status`
- `idempotency_key`, `retry_count`, `last_error`, timestamps

Validation: recipient addresses are syntactically valid; body is never sent by this feature; tenant access is required.

## State transitions

`local_saved -> sync_pending -> synced`  
`sync_pending -> sync_failed -> sync_pending` on retry  
`synced -> sync_pending` when the user edits the draft  

No transition sends an email. Remote draft updates use the same idempotency key for a logical save operation.
