# Quickstart Validation

## Prerequisites

1. Start PostgreSQL/Redis and the backend, worker, and frontend using the existing local commands.
2. Apply the existing document provenance migrations plus the new evidence/opinion/email draft migration when implemented.
3. Use a text PDF with a multi-line risk and a cross-page clause; also test one DOCX contract.
4. For mailbox tests, leave provider unset and use the mock provider. Do not put QQ passwords in the repository.

## Evidence navigation scenario

1. Upload and complete review.
2. Call `GET /contracts/{id}/clause-locations` and verify every finding has `evidence_id`, `version_id`, and one or more locations.
3. Click a modification opinion in the UI.
4. Verify the PDF page changes to the evidence page, all evidence rectangles render, and coordinates remain aligned after zoom.
5. Force an unknown evidence ID and verify the UI reports unresolved without jumping to the first clause.

## Delivery scenario

1. From a completed review, export the opinion and the Word opinion.
2. Verify the downloaded content has identical risk/missing/recommendation counts and evidence IDs to the page.
3. Generate an email draft with default recipient `kalvinxuxu@qq.com`, edit subject/body, and click “存草稿”.
4. Verify one local draft with `sync_status=synced` under the mock provider and no send operation.
5. Repeat the same save with the same idempotency key and verify no duplicate draft is created.
6. Make the mock provider fail, verify `sync_failed`, then retry and verify recovery.

## Automated gates

- Backend: evidence resolver, multi-location navigation, opinion projection, Word export, draft idempotency, and provider failure tests.
- Frontend: PDF page jump/highlight, unresolved state, export dialog, editable email draft, and save/retry E2E flow.
- Benchmark: direct evidence mapping >=95%; no first-location fallback for unresolved evidence; export counts/evidence IDs match the completed review.
