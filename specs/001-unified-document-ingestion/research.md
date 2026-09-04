# Research: Evidence Navigation and Opinion Delivery

## Decision: Evidence ID is the primary PDF navigation key

The review result will reference `evidence_id` values produced by the unified document layer. Each ID resolves to one or more `EvidenceLocation` records containing page, normalized top-left bbox, document/version IDs, and resolution status. The frontend passes the ID to `PdfViewer`; it does not compare `original_text` on click.

Rationale: the current implementation compares truncated text and falls back to the first location, which explains incorrect highlights and unrelated jumps. Stable IDs also support cross-page clauses and auditability.

Alternatives considered: keep fuzzy text matching as the primary path (rejected); store only one bbox per finding (rejected for cross-page clauses). Fuzzy matching remains an explicitly labeled legacy fallback.

## Decision: Add a compact opinion projection and retain existing report export

The backend creates a deterministic `ReviewOpinion` projection from the completed review result. It is used by a new opinion export endpoint and by the email composer. The existing full review report endpoint remains compatible.

Rationale: the frontend should not assemble legal deliverables and different delivery channels must use identical finding counts and evidence IDs.

## Decision: Word output uses the existing python-docx boundary

Add an opinion-specific `.docx` generator under the delivery service, reusing the existing Word exporter conventions. It includes metadata, prioritized findings, missing clauses, recommendations, and evidence citations.

## Decision: Email drafts use a provider abstraction with QQ Mail first

Persist a local draft/outbox record before synchronizing. The first provider adapter targets QQ Mail using IMAP Drafts append/update semantics (or an approved provider API when credentials support it). Local development uses a mock/dry-run provider. Saving never sends mail.

Rationale: QQ Mail is the requested mailbox, while provider isolation keeps deployment credentials and future Gmail/enterprise providers out of review code. Idempotency keys prevent duplicate remote drafts after retries.

## Decision: Unresolved evidence is explicit

If an evidence ID cannot resolve, the API returns `resolution_status=unresolved` and the UI shows the unresolved state. It must not silently jump to the first clause. OCR-only page evidence can be page-level without claiming precise bbox accuracy.

## Open operational constraint

Production requires mailbox credentials/app password and IMAP configuration in Railway secrets. No secret is added to the repository or local `.env` by this plan.
