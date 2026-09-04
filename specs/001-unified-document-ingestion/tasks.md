---

description: "Implementation tasks for Unified Document Ingestion and Provenance"
---

# Tasks: Unified Document Ingestion and Provenance

**Input**: Design documents from `/specs/001-unified-document-ingestion/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Organization**: Tasks are grouped by user story. The MVP is US1 plus the minimum US2 foundation needed to create exact evidence.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish fixtures, package boundaries, and migration-safe configuration.

- [X] T001 [P] Add representative text, multi-line, cross-page, scan, hybrid, table-heavy, and malformed PDF fixtures under `backend/tests/fixtures/pdf/`
- [X] T002 [P] Add parser benchmark fixture manifest and expected outcome metadata in `backend/tests/fixtures/pdf/manifest.json`
- [X] T003 [P] Add the document-ingestion package exports in `backend/app/services/document/__init__.py`
- [X] T004 [P] Add frontend evidence types and API response types in `frontend/src/types/document.ts`
- [X] T005 Add feature flags and parser configuration defaults in `backend/app/core/config.py` for AST ingestion, Docling, MinerU, and Linux OCR

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared contracts and persistence boundaries required by every story.

- [X] T006 [P] Define Pydantic AST schemas for `UnifiedDocument`, `DocumentPage`, `DocumentBlock`, `DocumentSpan`, `DocumentTable`, bbox, and coordinate metadata in `backend/app/schemas/document.py`
- [X] T007 [P] Define Pydantic schemas for `DocumentChunk`, `ReviewEvidence`, and multi-location evidence in `backend/app/schemas/evidence.py`
- [X] T008 [P] Add immutable document/version/parse-attempt ORM models in `backend/app/models/document.py`
- [X] T009 [P] Add relational block/span/table/chunk/evidence ORM models in `backend/app/models/document_provenance.py`
- [X] T010 Register document provenance models in `backend/app/models/__init__.py` and database table creation/import paths in `backend/app/db/session.py`
- [X] T011 Add Alembic migration scaffolding and the initial provenance tables in `backend/alembic/versions/`
- [X] T012 Implement coordinate normalization and bbox validation in `backend/app/services/document/coordinates.py`
- [X] T013 Implement deterministic document/version/block/span ID generation and text-offset validation in `backend/app/services/document/identity.py`
- [X] T014 [P] Add unit tests for coordinate normalization, bbox bounds, IDs, and offset invariants in `backend/tests/unit/test_document_primitives.py`
- [X] T015 Add structured ingestion logging fields for document ID, version ID, parser, page, quality, and fallback in `backend/app/services/document/logging.py`

**Checkpoint**: AST schemas, persistence boundary, coordinate system, and identity rules are available before story work begins.

## Phase 3: User Story 1 - Stable Evidence Highlighting (Priority: P1) 🎯 MVP

**Goal**: Produce exact or explicitly fallback evidence locations for current text PDFs while preserving the existing PDF.js viewer.

**Independent Test**: Review a fixture with a multi-line risk clause and verify evidence IDs resolve to every expected page/span bbox and remain aligned at multiple zoom levels.

### Tests for User Story 1

- [X] T016 [P] [US1] Add contract tests for additive evidence fields and `coord_system` in `backend/tests/contract/test_review_evidence_contract.py` using `specs/001-unified-document-ingestion/contracts/review-evidence.json`
- [X] T017 [P] [US1] Add unit tests for grouping PyMuPDF spans into lines/blocks and assigning offsets in `backend/tests/unit/test_pymupdf_ast_adapter.py`
- [X] T018 [P] [US1] Add unit tests for exact ID resolution, cross-span evidence, and `fuzzy_legacy` fallback in `backend/tests/unit/test_evidence_resolver.py`
- [X] T019 [P] [US1] Extend frontend component tests for multi-rectangle highlights and page navigation in `frontend/src/components/__tests__/PdfViewer.test.ts`
- [X] T020 [US1] Add an end-to-end evidence/highlight scenario to `frontend/e2e/flows/contract-review.spec.ts`

### Implementation for User Story 1

- [X] T021 [P] [US1] Implement PyMuPDF `dict` to UnifiedDocument adapter with page, block, line, and span hierarchy in `backend/app/services/document/pymupdf_adapter.py`
- [X] T022 [P] [US1] Implement deterministic span/block index and exact evidence resolver in `backend/app/services/document/evidence_resolver.py`
- [X] T023 [US1] Implement AST-to-legacy-contract-text projection in `backend/app/services/document/text_projection.py`
- [X] T024 [US1] Implement persistence service for document versions, pages, blocks, spans, and evidence locations in `backend/app/services/document/repository.py`
- [X] T025 [US1] Update `backend/app/services/review/evidence_locator.py` to resolve risk clauses by block/span IDs first and invoke fuzzy matching only as `fuzzy_legacy`
- [X] T026 [US1] Update `backend/app/services/review/durable_graph.py` to persist and reuse the active document version during parse and finalize stages
- [X] T027 [US1] Extend `backend/app/api/v1/endpoints/contracts.py` PDF position responses with `document_id`, `version_id`, `coord_system`, evidence IDs, and multiple locations
- [X] T028 [US1] Update `frontend/src/components/PdfViewer.vue` to consume normalized coordinate metadata and render multiple evidence rectangles per clause
- [X] T029 [US1] Update `frontend/src/composables/useContracts.ts` and `frontend/src/views/Review.vue` to consume additive evidence fields while preserving legacy `original_text`
- [X] T030 [US1] Add structured evidence-resolution warnings and metrics to `backend/app/services/document/logging.py`

**Checkpoint**: US1 is independently demoable with current PyMuPDF, current PDF.js, exact evidence IDs, and legacy fallback support.

## Phase 4: User Story 2 - Structure-Aware Ingestion (Priority: P1)

**Goal**: Make one versioned UnifiedDocument the source for full text, page geometry, structure, and downstream consumers.

**Independent Test**: Parse text and table fixtures and verify review text, page positions, and AST snapshots are derived from the same document version without independent PDF reparsing.

### Tests for User Story 2

- [X] T031 [P] [US2] Add AST snapshot tests for text, heading, paragraph, list, table, and footer blocks in `backend/tests/integration/test_unified_document.py`
- [X] T032 [P] [US2] Add idempotency/version-lineage tests for repeated parsing and parser-version changes in `backend/tests/integration/test_document_versioning.py`
- [X] T033 [P] [US2] Add ingestion API contract tests for the request/response shape in `backend/tests/contract/test_ingestion_contract.py` using `specs/001-unified-document-ingestion/contracts/ingestion.json`
- [X] T034 [US2] Add a regression test proving existing contract review flows still pass using one persisted document version in `backend/tests/test_postgres_checkpoint_recovery.py`

### Implementation for User Story 2

- [X] T035 [US2] Implement `UnifiedDocumentAssembler` to build canonical pages, blocks, spans, tables, derived text, and warnings in `backend/app/services/document/assembler.py`
- [X] T036 [US2] Implement parser adapter protocol and adapter result types in `backend/app/services/document/adapters.py`
- [X] T037 [US2] Refactor `backend/app/services/document/parser.py` to delegate PDF parsing to the adapter/assembler while preserving the existing `parse_pdf()` projection
- [X] T038 [US2] Add ingestion orchestration and status transitions in `backend/app/services/document/ingestion_service.py`
- [X] T039 [US2] Add authenticated document ingestion/status endpoints in `backend/app/api/v1/endpoints/documents.py` with tenant-scoped access
- [X] T040 [US2] Update `backend/app/api/v1/endpoints/contracts.py` upload and review-status responses to expose the active document version additively
- [X] T041 [US2] Update `backend/app/services/review/durable_graph.py` to consume projected AST text and persisted provenance instead of reparsing the PDF in downstream stages
- [X] T042 [US2] Add AST snapshot/debug export support in `backend/app/api/v1/endpoints/documents.py` with bounded output and tenant checks
- [X] T043 [US2] Add frontend ingestion-status and evidence metadata handling in `frontend/src/composables/useDocumentIngestion.ts` and `frontend/src/views/Review.vue`

**Checkpoint**: US1 and US2 both work; the AST is the shared source for review text and PDF evidence.

## Phase 5: User Story 3 - Page-Level Parser Routing (Priority: P2)

**Goal**: Detect text/scan/hybrid/complex pages and select Linux-compatible parser/OCR fallbacks based on quality.

**Independent Test**: Run the fixture manifest and verify per-page classification, selected adapter, OCR scope, quality score, and fallback lineage.

### Tests for User Story 3

- [X] T044 [P] [US3] Add page classification tests for text, scan, hybrid, complex, and unsupported fixtures in `backend/tests/unit/test_pdf_preflight.py`
- [X] T045 [P] [US3] Add parser-router fallback tests with unavailable adapters and low-quality results in `backend/tests/unit/test_parser_router.py`
- [X] T046 [P] [US3] Add Linux OCR adapter tests with mocked OCR output and page-only evidence in `backend/tests/unit/test_ocr_adapter.py`
- [X] T047 [US3] Add fixture benchmark assertions for OCR rate, quality threshold, and fallback lineage in `backend/tests/integration/test_parser_benchmark.py`

### Implementation for User Story 3

- [X] T048 [US3] Implement page-level PDF preflight metrics for embedded text, image coverage, fonts, and page dimensions in `backend/app/services/document/preflight.py`
- [X] T049 [US3] Implement parser quality scoring and threshold decisions in `backend/app/services/document/quality_gate.py`
- [X] T050 [P] [US3] Implement Docling-to-UnifiedDocument adapter behind an optional dependency in `backend/app/services/document/docling_adapter.py`
- [X] T051 [P] [US3] Implement MinerU-to-UnifiedDocument adapter for complex layouts in `backend/app/services/document/mineru_adapter.py`
- [X] T052 [P] [US3] Implement Linux-compatible OCR adapter and remove Windows-only Tesseract path assumptions in `backend/app/services/document/ocr_adapter.py`
- [X] T053 [US3] Implement parser router, fallback lineage, and per-page attempt persistence in `backend/app/services/document/parser_router.py`
- [X] T054 [US3] Add optional parser/OCR dependencies and Railway-safe runtime configuration in `backend/requirements.txt` and `backend/Dockerfile`
- [X] T055 [US3] Update ingestion status API to expose page classification, parser attempts, quality scores, and warnings in `backend/app/api/v1/endpoints/documents.py`
- [X] T056 [US3] Update frontend ingestion diagnostics and degraded page-only evidence messaging in `frontend/src/views/Review.vue` and `frontend/src/components/review/`

**Checkpoint**: US3 routes pages without full-document OCR and records every parser/fallback decision.

## Phase 6: User Story 4 - Structure-Aware Retrieval and Review (Priority: P2)

**Goal**: Preserve document/chunk/block/span provenance through RAG and constrain LLM evidence selection to supplied IDs.

**Independent Test**: Index a numbered contract, retrieve a section, run review, and resolve the returned evidence to the original PDF without fuzzy matching.

### Tests for User Story 4

- [X] T057 [P] [US4] Add structure-aware chunking tests for numbered sections, headings, tables, and cross-page blocks in `backend/tests/unit/test_structure_chunker.py`
- [X] T058 [P] [US4] Add retrieval provenance tests for chunk-to-block/page resolution in `backend/tests/integration/test_rag_provenance.py`
- [X] T059 [P] [US4] Add review prompt/result validation tests rejecting unknown evidence IDs in `backend/tests/unit/test_review_evidence_validation.py`
- [X] T060 [US4] Add end-to-end audit test from RAG result to review evidence to PDF bbox in `backend/tests/integration/test_review_provenance.py`

### Implementation for User Story 4

- [X] T061 [US4] Implement section-aware chunking from UnifiedDocument in `backend/app/services/rag/structure_chunker.py`
- [X] T062 [US4] Extend vector index metadata and retrieval results with document/version/chunk/block/page provenance in `backend/app/services/rag/retriever.py` and `backend/app/services/rag/vector_retriever.py`
- [X] T062-A [US4] Add PostgreSQL full-text/BM25-style lexical indexing for structure-aware chunks in `backend/app/services/rag/bm25_retriever.py` and the document chunk model
- [X] T062-B [US4] Implement parallel BM25 and vector candidate retrieval with tenant/version filters in `backend/app/services/rag/hybrid_retriever.py`
- [X] T062-C [US4] Implement configurable Reciprocal Rank Fusion and preserve lexical/vector ranks and scores in `backend/app/services/rag/rank_fusion.py`
- [X] T062-D [US4] Implement deterministic first-stage reranking with lexical, vector, section, and provenance features in `backend/app/services/rag/reranker.py`
- [X] T063 [US4] Update `backend/app/services/review/context_builder.py` to serialize bounded source blocks with immutable IDs for the LLM
- [X] T064 [US4] Update `backend/app/services/review/prompt_builder.py` to require evidence IDs selected from supplied context and preserve legacy fields during migration
- [X] T064-A [US4] Make review context consume only reranked candidates and retain `bm25_score`, `vector_score`, `fused_score`, and `rerank_score` in `backend/app/services/review/context_builder.py`
- [X] T065 [US4] Update `backend/app/services/review/service.py` to validate, normalize, and persist `ReviewEvidence` before returning results
- [X] T066 [US4] Update `backend/app/services/review/durable_graph.py` to pass structure-aware chunks and evidence-bearing context through the durable workflow
- [X] T067 [US4] Add additive review response serialization for evidence and multi-location highlights in `backend/app/api/v1/endpoints/contracts.py`
- [X] T068 [US4] Update frontend risk cards and PDF navigation to use `risk_id`/evidence IDs in `frontend/src/components/review/` and `frontend/src/views/Review.vue`

### Reranker Upgrade: Hybrid Recall → Cross-Encoder → Legal Policy

- [X] T076 [P] [US4] Add retrieval audit schema tests for `semantic_score`, `authority_score`, `metadata_score`, provider/model/version, fallback reason, and provenance in `backend/tests/contract/test_retrieval_contract.py` using `specs/001-unified-document-ingestion/contracts/retrieval.json`
- [X] T077 [P] [US4] Add reranker provider settings for `bge_local`, `jina`, and `deterministic_fallback`, including model, Top40 candidate limit, timeout, batch size, and score normalization in `backend/app/core/config.py`
- [X] T078 [P] [US4] Define the cross-encoder provider protocol and normalized score result type in `backend/app/services/rag/reranker_providers.py`
- [X] T079 [US4] Implement local `BAAI/bge-reranker-v2-m3` provider with lazy model loading, CPU-safe inference, batching, timeout/error handling, and model metadata in `backend/app/services/rag/bge_reranker.py`
- [X] T080 [P] [US4] Implement optional Jina reranker provider with API timeout, authentication, response validation, and provider metadata in `backend/app/services/rag/jina_reranker.py`
- [X] T081 [P] [US4] Add deterministic legal authority taxonomy and effective-date/jurisdiction/source-status policy scoring in `backend/app/services/rag/legal_rank_policy.py`
- [X] T082 [US4] Replace the hand-tuned `FeatureReranker` formula with a staged reranker orchestrator that scores Top40 candidates, applies legal hard filters, calculates the documented final score, and records fallback reasons in `backend/app/services/rag/reranker.py`
- [X] T083 [US4] Update `backend/app/services/rag/hybrid_retriever.py` and `backend/app/services/rag/rank_fusion.py` to use configurable BM25/vector candidate limits and `RAG_RRF_K`, enforce the Top40 boundary, and preserve all stage ranks/scores
- [X] T084 [US4] Extend `backend/app/schemas/evidence.py`, `backend/app/services/review/context_builder.py`, and `backend/app/services/review/service.py` to expose and persist the complete retrieval audit fields without allowing the LLM to alter them
- [X] T085 [P] [US4] Add unit tests for BGE/Jina provider selection, batching, score normalization, unavailable-provider fallback, and deterministic tie-breaking in `backend/tests/unit/test_reranker_providers.py`
- [X] T086 [P] [US4] Add unit tests for authority ordering, effective-date exclusion, jurisdiction/version filters, and metadata boosts in `backend/tests/unit/test_legal_rank_policy.py`
- [X] T087 [US4] Extend hybrid retrieval tests to verify Top40 RRF input, three-stage ordering, score fields, and fallback observability in `backend/tests/unit/test_hybrid_retrieval.py`
- [X] T088 [US4] Add labeled-clause comparison benchmark for vector-only, legacy feature, BGE local, and Jina providers with Recall@10, MRR/nDCG@10, duplicate rate, authority violations, and P95 latency in `backend/scripts/benchmark_rag_retrieval.py`
- [X] T089 [US4] Add offline local contract verification for representative PDF and DOCX files, including ingestion, retrieval audit, evidence provenance, and explicit model/fallback status in `backend/scripts/local_contract_smoke.py`
- [X] T090 [US4] Add optional reranker dependencies and Railway-safe environment documentation, keeping BGE model download/cache configurable and Jina credentials out of source control in `backend/requirements.txt`, `backend/Dockerfile`, `.env.example`, and `README.md`
- [X] T091 [US4] Run the local PDF/DOCX smoke validation and retrieval benchmark, record provider metrics and authority-order checks in `specs/001-unified-document-ingestion/benchmark-results.md`

**Checkpoint**: RAG, LLM review, stored evidence, and PDF.js highlighting share one provenance chain.

## Phase 7: User Story 5 - Evidence-Driven PDF Navigation (Priority: P1; dependency-ordered after US4)

**Goal**: Make every review finding navigate to its exact evidence locations and make unresolved evidence explicit.

**Independent Test**: Complete a review with multi-line and cross-page findings, click each modification opinion, and verify the PDF opens the correct page, renders all evidence rectangles, and never jumps to an unrelated first location.

### Tests for User Story 5

- [ ] T106 [P] [US5] Add API contract tests for evidence lookup, location arrays, coordinate metadata, and unresolved status in `backend/tests/contract/test_delivery_api.py` using `specs/001-unified-document-ingestion/contracts/delivery-api.md`
- [ ] T107 [P] [US5] Add resolver tests for evidence-ID lookup, multi-span/multi-page locations, version mismatch, and no-first-location fallback in `backend/tests/unit/test_evidence_navigation.py`
- [ ] T108 [P] [US5] Add PDF viewer component tests for page jump, multi-rectangle rendering, zoom alignment, and unresolved state in `frontend/src/components/__tests__/PdfViewer.test.ts`
- [ ] T109 [US5] Add Playwright coverage for clicking a risk modification opinion and navigating the PDF in `frontend/e2e/flows/contract-review.spec.ts`

### Implementation for User Story 5

- [X] T110 [P] [US5] Add `EvidenceLocation` schema fields and resolution-status validation in `backend/app/schemas/evidence.py`
- [X] T111 [P] [US5] Add evidence-location persistence fields/indexes and migration in `backend/app/models/clause_location.py`, `backend/migrations/004_evidence_navigation.sql`, and `backend/app/models/__init__.py`
- [X] T112 [US5] Implement evidence-ID-first location lookup with document/version checks and explicit fallback diagnostics in `backend/app/services/document/evidence_navigation.py`
- [ ] T113 [US5] Update review result normalization to persist stable evidence IDs and all resolved locations for risk/missing findings in `backend/app/services/review/service.py` and `backend/app/services/review/evidence_locator.py`
- [X] T114 [US5] Add `GET /api/v1/contracts/{contract_id}/evidence/{evidence_id}` and extend clause-location responses with resolution status in `backend/app/api/v1/endpoints/contracts.py`
- [X] T115 [US5] Update `frontend/src/components/PdfViewer.vue` to expose evidence-ID navigation, cross-page location controls, and coordinate-system-aware scrolling
- [X] T116 [US5] Replace text-similarity-first `highlightPdfClause` with evidence-ID navigation and unresolved feedback in `frontend/src/views/Review.vue`
- [ ] T117 [US5] Add evidence-resolution metrics and structured logs for direct, fuzzy, page-only, and unresolved outcomes in `backend/app/services/document/metrics.py` and `backend/app/services/document/logging.py`

**Checkpoint**: A completed review finding deterministically opens its own PDF evidence, including cross-page evidence, with no silent unrelated fallback.

## Phase 8: User Story 6 - Opinion Delivery and Draft Email (Priority: P1; dependency-ordered after completed review evidence)

**Goal**: Deliver completed review opinions as downloadable documents and an editable, unsent email draft synchronized to the configured mailbox.

**Independent Test**: From a completed review, export the opinion and Word file, edit a draft addressed to `kalvinxuxu@qq.com`, save it twice with the same idempotency key, and verify one local/remote draft with visible synchronization status and no sent message.

### Tests for User Story 6

- [ ] T118 [P] [US6] Add opinion projection tests for stable counts, ordering, redaction, and evidence IDs in `backend/tests/unit/test_review_opinion.py`
- [ ] T119 [P] [US6] Add Word export tests for valid `.docx` output, required sections, metadata, and evidence citations in `backend/tests/unit/test_opinion_docx_export.py`
- [ ] T120 [P] [US6] Add mock-provider tests for draft create/update, timeout retry, idempotency, and no-send behavior in `backend/tests/unit/test_email_draft_provider.py`
- [ ] T121 [US6] Add API contract/integration tests for opinion export and email draft lifecycle in `backend/tests/integration/test_delivery_workflow.py`
- [ ] T122 [US6] Add frontend E2E coverage for export opinion, export Word, edit email, save draft, retry failure, and status display in `frontend/e2e/flows/review-delivery.spec.ts`

### Implementation for User Story 6

- [X] T123 [P] [US6] Add `ReviewOpinion`, `EmailDraft`, and provider-sync schemas/models plus indexes in `backend/app/schemas/delivery.py`, `backend/app/models/delivery.py`, and `backend/migrations/005_review_delivery.sql`
- [X] T124 [US6] Implement deterministic opinion projection and redacted delivery payload in `backend/app/services/delivery/opinion_service.py`
- [X] T125 [US6] Implement compact opinion text/HTML and `python-docx` generation with evidence references in `backend/app/services/delivery/opinion_exporter.py`
- [X] T126 [US6] Implement mailbox provider protocol, local mock provider, QQ IMAP Drafts adapter, secret-based configuration, and credential-safe logging in `backend/app/services/delivery/mail_provider.py`, `backend/app/services/delivery/mock_provider.py`, `backend/app/services/delivery/qq_imap_provider.py`, and `backend/app/core/config.py`
- [X] T127 [US6] Implement idempotent local outbox persistence, provider synchronization, retry, and status transitions in `backend/app/services/delivery/email_draft_service.py`
- [X] T128 [US6] Add opinion export, Word export, create draft, get draft, and retry draft endpoints in `backend/app/api/v1/endpoints/delivery.py` and register them in `backend/app/api/v1/__init__.py`
- [X] T129 [US6] Add frontend delivery API composables, opinion/Word export actions, editable email draft dialog, default recipient, and sync status UI in `frontend/src/composables/useReviewDelivery.ts` and `frontend/src/views/Review.vue`
- [ ] T130 [US6] Document QQ IMAP secrets, mock-provider local setup, no-send guarantee, and Railway deployment variables in `.env.example`, `README.md`, and `docs/Railway-Vercel部署指南.md`

**Checkpoint**: Opinion and Word downloads match the completed review, and email drafts can be saved/retried without sending or duplicating messages.

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness, migration safety, observability, and documentation.

- [X] T069 [P] Add bounded AST serialization, redaction rules, and tenant-isolation tests in `backend/tests/unit/test_document_security.py`
- [X] T070 [P] Add ingestion latency, parser success, OCR rate, quality, evidence resolution, and fallback metrics in `backend/app/services/document/metrics.py`
- [X] T071 [P] Add parser benchmark report generation to `backend/scripts/benchmark_document_ingestion.py`
- [X] T071-A [P] Add labeled retrieval benchmark fixtures and Recall@K, MRR/nDCG@K, duplicate-rate, and P95 latency reporting in `backend/scripts/benchmark_rag_retrieval.py`
- [X] T072 Add migration/backfill command for existing contracts and legacy `original_text` results in `backend/scripts/backfill_document_provenance.py`
- [X] T073 Remove dead duplicate PDF parsing and make `SequenceMatcher` fallback-only after all callers migrate in `backend/app/services/review/evidence_locator.py` and `backend/app/services/document/parser.py`
- [X] T092 [US4] Add PostgreSQL pgvector production storage and HNSW migration for legal knowledge and document chunks in `backend/app/models`, `backend/migrations/002_pgvector_contract_chunks.sql`, and `backend/app/core/config.py`
- [X] T093 [US4] Persist embeddings for structure-aware contract chunks and implement tenant/version-scoped BM25 plus pgvector retrieval in `backend/app/services/rag/contract_chunk_retriever.py`
- [X] T094 [US4] Integrate contract chunk Hybrid RRF/Rerank context into the durable review graph and prompt while retaining legal/policy context in `backend/app/services/review/durable_graph.py`, `backend/app/services/review/service.py`, and `backend/app/services/review/prompt_builder.py`
- [X] T095 [US4] Add pgvector/contract-chunk retrieval diagnostics and offline regression coverage in `backend/tests/unit` and `backend/scripts/local_contract_smoke.py`
- [X] T096 [US4] Add repeatable Chroma-to-pgvector migration, checksum validation, idempotent rerun, and rollback-safe cutover in `backend/scripts/migrate_chroma_to_pgvector.py` and `docs/Railway-Vercel部署指南.md`
- [X] T097 [US4] Add current-version-only vector retrieval and duplicate-embedding regression tests in `backend/tests/integration/test_contract_chunk_versioning.py`
- [ ] T098 [US4] Expand labeled clause fixtures and run real BGE/Jina comparison with Recall@10, MRR/nDCG@10, authority violations, duplicate rate, and P95 latency in `backend/scripts/benchmark_rag_retrieval.py` (BGE completed; Jina pending API key)
- [X] T099 [US3] Define and execute Docling activation acceptance checks for AST parity, table integrity, evidence resolution, and layout quality in `backend/tests/integration/test_docling_acceptance.py` (Docling 2.124.0 passed against the generated complex-layout fixture; canonical AST remains PyMuPDF-backed)
- [X] T100 [US4] Add production rollout checklist for pgvector extension, embedding backfill, BM25-only degradation, current-version filtering, and observability in `docs/Railway-Vercel部署指南.md`
- [X] T101 [US4] Upgrade contract chunking to token-bounded limits, sentence/subclause boundaries, and deterministic hard-split overlap in `backend/app/services/rag/structure_chunker.py` and `backend/app/core/config.py`
- [X] T102 [US4] Persist section hierarchy, chunk type, parent identity, span IDs, character offsets, token count, and clause completeness through schema/model/repository/migration layers
- [X] T103 [US4] Add nested-section, child-chunk, overlap-provenance, and current-version regression coverage in `backend/tests/unit` and `backend/tests/integration`
- [X] T104 [US4] Add optional cosine semantic-boundary splitting subordinate to legal section boundaries, disabled by default and covered by deterministic unit tests
- [X] T105 [US4] Expand retrieved child chunks with bounded parent-clause context while preserving child source IDs and evidence provenance in `backend/app/services/review/context_builder.py`
- [X] T074 Update Railway deployment dependencies, environment variables, and worker/runtime guidance in `docs/Railway-Vercel部署指南.md` and `README.md`
- [X] T075 Run all scenarios in `specs/001-unified-document-ingestion/quickstart.md` and record benchmark results in `specs/001-unified-document-ingestion/benchmark-results.md`

- [ ] T131 [P] Add delivery audit events, provider latency/error metrics, and body/credential redaction checks in `backend/app/services/delivery/metrics.py` and `backend/tests/unit/test_delivery_security.py`
- [ ] T132 [P] Add migration/backfill validation for legacy clause locations and legacy review results in `backend/scripts/backfill_delivery_provenance.py`
- [ ] T133 Run the evidence-navigation and delivery scenarios in `specs/001-unified-document-ingestion/quickstart.md` and record accuracy/export/idempotency results in `specs/001-unified-document-ingestion/benchmark-results.md`

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No feature dependency; fixture and package setup can begin immediately.
- **Phase 2 Foundational**: Depends on T003-T005; blocks all user-story implementation.
- **US1**: Depends on T006-T015; MVP is T016-T030.
- **US2**: Depends on US1's evidence primitives T021-T024 and all foundational tasks.
- **US3**: Depends on US2's adapter protocol and ingestion orchestration T035-T038.
- **US4**: Depends on US2's canonical AST persistence and US1's evidence resolver; US3 is optional for text-PDF retrieval. Reranker upgrade tasks T076-T091 depend on the existing hybrid retrieval and provenance tasks T061-T065.
- **US5**: Depends on US1/US4 evidence persistence and the active document-version contract; T106-T109 can begin after the contract shape is agreed, while T112-T116 follow the schemas and resolver.
- **US6**: Depends on a completed review result and the delivery API contract; it can proceed in parallel with US5 after shared review result schemas are stable. T123-T126 can run in parallel; T127-T129 follow persistence/provider boundaries.
- **Priority note**: US5 and US6 are P1 business priorities, but their implementation phases remain after US4 because they consume the evidence/provenance contracts delivered there.
- **Polish (Phase 9)**: Depends on US5 and US6 for delivery metrics and the final quickstart run.

### User Story Dependencies

- **US1**: First independently deliverable story; no dependency on Docling, MinerU, or OCR.
- **US2**: Builds the canonical AST around US1's PyMuPDF provenance.
- **US3**: Adds alternate parser/OCR routing to the US2 adapter boundary.
- **US4**: Uses the AST and evidence chain from US1/US2; can start before US3 for text PDFs.
- **US5**: Uses the evidence chain from US1/US4 and is independently testable with existing PyMuPDF text-PDF fixtures.
- **US6**: Uses completed review results and is independently testable with the mock mailbox provider; QQ credentials are only needed for production integration.

### Parallel Opportunities

- Setup T001-T004 can run in parallel.
- Foundational T006-T009, T012-T014 can run in parallel after package setup.
- US1 tests T016-T020 can run in parallel; T021 and T022 can run in parallel after schemas.
- US3 Docling, MinerU, and OCR adapters T050-T052 can run in parallel after T036.
- US4 chunking, BM25/vector retrieval, fusion, reranking, and evidence validation T061-T065 plus T062-A-T062-D/T064-A can be split by service after AST persistence is available.
- Reranker upgrade T077-T081 and tests T076/T085/T086 can run in parallel after the provider contract is agreed; T082-T084 depend on those interfaces; T087-T091 run after orchestration is integrated.
- Polish metrics, benchmark tooling, and security tests T069-T071 can run in parallel.
- US5 tests T106-T109 can run in parallel; T110-T111 can run in parallel; T112-T114 are backend tracks and T115-T116 are frontend tracks after the API/schema contract.
- US6 tests T118-T120 can run in parallel; T123-T126 can run in parallel; T124-T125 can run independently of T126 until endpoint integration T128.

## Parallel Example: User Story 1

```text
Track A: T016 → T021 → T024 → T025
Track B: T017 → T022 → T026
Track C: T018 → T023 → T027
Track D: T019 → T028 → T029
Track E: T020 → integration validation
```

## Parallel Example: User Stories 5 and 6

```text
US5: T106/T107/T108 → T110/T111 → T112/T114 → T115/T116 → T109
US6: T118/T119/T120 → T123/T124/T125/T126 → T127 → T128/T129 → T121/T122
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Implement US1 using the existing PyMuPDF span output.
3. Verify exact multi-span evidence and PDF.js alignment.
4. Release only after legacy `original_text` results still work through `fuzzy_legacy`.

### Incremental Delivery

1. US1 delivers exact evidence for normal text PDFs.
2. US2 makes the AST canonical and removes downstream reparsing.
3. US3 adds scan/hybrid/complex routing and Railway-compatible OCR.
4. US4 makes RAG and LLM review provenance-aware, using BM25+Vector hybrid retrieval, RRF, cross-encoder reranking, and deterministic legal policy ranking.
5. Polish adds backfill, benchmark reporting, and production observability.
6. Reranker upgrade adds local BGE validation first, optional Jina comparison second, then enables Railway deployment only after the local benchmark passes.
7. US5 fixes deterministic PDF evidence navigation before US6 delivery features consume the same evidence IDs.
8. US6 adds opinion/Word export and mock-first email drafts; QQ Mail synchronization is enabled only after local idempotency and no-send tests pass.

## Notes

- Every task follows the required checklist format and includes an exact file path.
- `[P]` means the task can run in parallel with other tasks in the same phase after stated dependencies are met.
- No task introduces a direct dependency from business logic to DoclingDocument or MinerU output.
- The current deterministic reranker remains only as an explicitly labeled fallback until T082 is complete; no fallback result may claim BGE/Jina scoring.
- `tasks.md` intentionally does not assume a Git branch switch; the current checkout remains `master` until the user chooses to create a feature branch.
