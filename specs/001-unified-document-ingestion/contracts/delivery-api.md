# Delivery API Contract

All endpoints require the existing authenticated, tenant-scoped contract access dependency.

## Resolve evidence

`GET /api/v1/contracts/{contract_id}/evidence/{evidence_id}`

Returns:

```json
{
  "evidence_id": "ev-123",
  "document_id": "doc-1",
  "version_id": "ver-1",
  "locations": [{"page": 16, "bbox": {"x0": 72, "y0": 180, "x1": 520, "y1": 246}, "coord_system": "pdf_top_left", "resolution_status": "resolved"}],
  "resolution_status": "resolved"
}
```

## Export opinion

`POST /api/v1/contracts/{contract_id}/export-opinion`

Request options select risk, missing-clause, recommendation, and evidence-reference sections. `format` accepts `html` or `json` and defaults to `html`. The default response is a downloadable UTF-8 HTML file with `Content-Type: text/html; charset=utf-8` and filename `审查意见_{contract_name}.html`; `json` is an API preview projection and is not a file download.

## Export Word opinion

`POST /api/v1/contracts/{contract_id}/export-opinion-docx`

Response: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`; must contain the same `review_run_id`, counts, and evidence IDs as the completed review.

## Save email draft

`POST /api/v1/contracts/{contract_id}/email-drafts`

Request:

```json
{"to":["kalvinxuxu@qq.com"],"subject":"合同审查意见","body_text":"...","provider":"qq_imap","idempotency_key":"client-generated-key"}
```

Response includes `draft_id`, `provider_draft_id` when available, `sync_status`, and `last_error`; it never returns credentials or sends mail.

`GET /api/v1/contracts/{contract_id}/email-drafts/{draft_id}` returns the local and provider synchronization state.

`POST /api/v1/contracts/{contract_id}/email-drafts/{draft_id}/retry` retries only the provider synchronization using the existing draft and idempotency key.
