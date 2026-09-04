# Feature Specification: Unified Document Ingestion and Provenance

**Feature Branch**: `001-unified-document-ingestion`

**Created**: 2026-09-02

**Status**: Draft

**Input**: Upgrade the legal AI ingestion architecture without rewriting the product. Establish a unified document structure layer so parsing, RAG, LLM review, clause evidence, and PDF highlighting consume the same provenance model.

## User Scenarios & Testing

### User Story 1 - Stable evidence highlighting (Priority: P1)

As a legal reviewer, I want every detected risk to link to the exact source block/span and page geometry, so that the highlighted PDF points to the evidence that produced the finding.

**Why this priority**: Evidence traceability is the core reliability gap in the current two-pass parser and fuzzy matching design.

**Independent Test**: Upload a text PDF containing a multi-line risky clause, run review, and verify that the result contains evidence IDs and the UI highlights all corresponding rectangles.

**Acceptance Scenarios**:

1. **Given** a text PDF with one clause split across multiple PDF spans, **When** the review completes, **Then** the risk result references stable block/span IDs and the stored locations contain every relevant bbox.
2. **Given** a PDF is rendered at different zoom levels, **When** the user navigates to an evidence item, **Then** the highlight remains aligned with the source text.
3. **Given** a legacy result contains only `original_text`, **When** evidence IDs are unavailable, **Then** the existing fuzzy locator is used as an explicitly marked fallback.

### User Story 2 - Structure-aware ingestion (Priority: P1)

As the review pipeline, I want one normalized document representation containing pages, blocks, spans, hierarchy, tables, and provenance, so that downstream consumers do not parse the same PDF independently.

**Why this priority**: It removes the architectural split between semantic text and page geometry while preserving PyMuPDF/PDF.js.

**Independent Test**: Parse representative PDF fixtures and verify that the normalized output can produce contract text, RAG chunks, review input, and display locations without reparsing the source.

**Acceptance Scenarios**:

1. **Given** a normal text PDF, **When** ingestion runs, **Then** it creates a versioned UnifiedDocument with page dimensions, reading order, block IDs, span IDs, normalized coordinates, and derived full text.
2. **Given** a PDF with headings, paragraphs, and tables, **When** ingestion runs, **Then** those elements retain their type and parent/child relationships where the selected parser supports them.
3. **Given** ingestion is retried, **When** the same document and parser version are used, **Then** the output identity and provenance are deterministic or the change is explicitly versioned.

### User Story 3 - Page-level parser routing (Priority: P2)

As a user uploading mixed business documents, I want the system to distinguish text, scanned, and hybrid pages, so that OCR is used only where needed and complex layouts can use an appropriate parser.

**Why this priority**: Page-level routing improves Chinese scan handling, cost, latency, and mixed-document coverage.

**Independent Test**: Run ingestion against text, scan, hybrid, table-heavy, and malformed fixtures and verify route selection plus fallback behavior.

**Acceptance Scenarios**:

1. **Given** a text page, **When** preflight runs, **Then** the page is routed to a text/layout parser without full-page OCR.
2. **Given** a scanned page, **When** preflight runs, **Then** the page is routed to the configured Linux-compatible OCR engine and records confidence.
3. **Given** the primary parser fails or produces low-quality output, **When** the quality gate runs, **Then** a configured fallback parser is attempted and the parser decision is recorded.

### User Story 4 - Structure-aware retrieval and review (Priority: P2)

As a legal reviewer, I want retrieved context and risk findings to retain document, chunk, block, and span provenance, so that legal conclusions can be audited back to the contract.

**Why this priority**: RAG and review quality depend on preserving clause boundaries and evidence, not only character windows.

**Independent Test**: Index a contract with numbered sections, retrieve a clause, and verify that the result includes section metadata and resolves to PDF locations.

**Acceptance Scenarios**:

1. **Given** numbered contract sections, **When** chunks are generated, **Then** chunks respect section/block boundaries where possible and include page ranges and source IDs.
2. **Given** an LLM review request, **When** evidence is selected, **Then** the model can only select IDs supplied in the review context.
3. **Given** a cross-page clause, **When** it is returned as evidence, **Then** it can contain multiple locations under one risk/evidence identity.

### User Story 5 - Evidence-driven PDF navigation (Priority: P1)

As a legal reviewer, I want clicking a risk or modification opinion to open the exact source clause in the PDF, so that I can verify and edit it without manual searching.

**Independent Test**: Complete a review containing a multi-line and a cross-page risk, click its modification opinion, and verify that the viewer selects the evidence ID, navigates to the first location, and renders all associated rectangles using the documented coordinate system.

**Acceptance Scenarios**:

1. **Given** a finding with valid evidence IDs, **When** its opinion is clicked, **Then** the UI navigates to the evidence page and highlights every location belonging to that evidence.
2. **Given** an evidence item spanning pages, **When** the first location is opened, **Then** the UI exposes next/previous evidence-location navigation instead of silently selecting an unrelated clause.
3. **Given** evidence cannot be resolved, **When** the opinion is clicked, **Then** the UI shows an explicit unresolved state and never falls back to the first contract location.

### User Story 6 - Opinion delivery and draft email (Priority: P1)

As a legal reviewer, I want to export a concise opinion, generate a Word document, and save an email draft for `kalvinxuxu@qq.com`, so that review output can enter the normal legal workflow.

**Independent Test**: Complete a review, export the opinion and Word file, generate an editable email draft, save it, and verify an auditable draft record and idempotent provider operation.

**Acceptance Scenarios**:

1. **Given** a completed review, **When** the reviewer chooses “导出意见”, **Then** a structured opinion document is downloaded with risks, missing clauses, recommended changes, evidence references, and generation metadata.
2. **Given** a completed review, **When** the reviewer chooses “导出 Word”, **Then** a `.docx` file is returned with stable headings and clause/evidence references.
3. **Given** a completed review, **When** the reviewer edits recipient, subject, and body and clicks “存草稿”, **Then** the system stores a draft and synchronizes it to the configured mailbox provider without sending the email.
4. **Given** a provider timeout or retry, **When** the same draft operation is retried, **Then** it does not create duplicate drafts and exposes synchronization status.

### Edge Cases

- A PDF may contain text on some pages and only images on others; routing must be page-level.
- A clause may cross lines, spans, blocks, or pages; one evidence item must support multiple locations.
- A parser may return malformed coordinates, missing text, or inconsistent reading order; ingestion must normalize or reject with structured warnings.
- OCR may return text without precise bboxes; the system must expose page-level evidence without claiming exact highlighting.
- Tables may not map cleanly to paragraphs; table cells must retain their own provenance or be marked unsupported.
- A parser dependency may be unavailable in Railway; the service must fail clearly and preserve the document's failed-ingestion state.
- Reprocessing with a new parser version must not silently overwrite the prior provenance used by an existing review.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST introduce a versioned internal `UnifiedDocument` representation independent of Docling, MinerU, PyMuPDF, or any single parser.
- **FR-002**: The representation MUST support documents, pages, blocks, spans, tables, hierarchy, reading order, text offsets, parser metadata, and normalized page coordinates.
- **FR-003**: Every block and span MUST have a stable ID within a document version; IDs MUST be usable by RAG, review, storage, and frontend highlighting.
- **FR-004**: The system MUST derive full text and structure-aware chunks from UnifiedDocument rather than reparsing the PDF for each consumer.
- **FR-005**: The ingestion pipeline MUST preserve `document_id`, `parser`, `parser_version`, source file hash, page dimensions, and parse warnings.
- **FR-006**: The review context MUST provide evidence-bearing block/span IDs to the LLM and require returned evidence IDs to be selected from that context.
- **FR-007**: Review results MUST support evidence containing multiple spans and multiple page locations.
- **FR-008**: The PDF display API MUST return normalized coordinates and coordinate-system metadata sufficient for PDF.js and server-side highlighting.
- **FR-009**: The current fuzzy locator MUST remain available only as a fallback for legacy or unresolved evidence and MUST record its match type and confidence.
- **FR-010**: The system MUST classify pages as text, scan, hybrid, or unsupported before selecting OCR or complex-layout parsing.
- **FR-011**: The system MUST support parser adapters with Docling as the planned primary structural parser, MinerU as a complex-layout fallback, PyMuPDF as the geometry/span engine, and a Linux-compatible Chinese OCR adapter.
- **FR-012**: The system MUST apply a parse quality gate using text coverage, character quality, reading-order/layout signals, OCR confidence, and table integrity where available.
- **FR-013**: Failed parsing, fallback decisions, quality scores, and warnings MUST be persisted and observable for a document version.
- **FR-014**: Existing upload, review, RAG, PDF.js rendering, tenant isolation, and result APIs MUST remain compatible during the migration, with additive fields preferred over breaking changes.
- **FR-015**: The ingestion implementation MUST work in the Railway Linux runtime and MUST NOT depend on Windows-only OCR paths.
- **FR-016**: The retrieval pipeline MUST support lexical BM25-style and vector candidate retrieval in parallel, followed by deterministic rank fusion.
- **FR-017**: Hybrid retrieval MUST use Reciprocal Rank Fusion or an equivalent documented fusion method and preserve lexical, vector, fused, and rerank scores.
- **FR-018**: The review context MUST be built from reranked candidates, bounded by a configured top-K, and retain document/version/chunk/block/span provenance.
- **FR-019**: Retrieval evaluation MUST report Recall@K, MRR or nDCG@K, duplicate rate, and P95 retrieval latency on a labeled fixture set.
- **FR-020**: Production vector storage MUST use PostgreSQL with pgvector as the system of record; Chroma MAY remain only as an explicitly configured compatibility fallback. Existing Chroma records MUST have a repeatable migration, validation, and rollback-safe cutover path.
- **FR-021**: Contract review MUST retrieve structure-aware chunks from the current document version using BM25 and vector recall, RRF, and reranking before constructing the LLM review context. If the embedding provider or vector index is unavailable, the system MAY use BM25-only fallback, but MUST expose that degraded mode in retrieval diagnostics.
- **FR-022**: Review findings MUST carry a stable `evidence_id` and one or more resolved evidence locations; frontend PDF navigation MUST use this identity rather than re-searching `original_text` as the primary path.
- **FR-023**: Evidence locations MUST include zero-based page number, normalized top-left coordinates, document/version IDs, and a resolution status; unresolved or fuzzy fallback locations MUST be visibly marked and MUST NOT default to the first location.
- **FR-024**: The system MUST expose an opinion export operation separate from the existing full review report, with deterministic content selection and source/evidence references. The default downloadable format MUST be UTF-8 HTML with `Content-Type: text/html; charset=utf-8` and filename `审查意见_{contract_name}.html`; JSON MAY be requested for API preview.
- **FR-025**: The system MUST export a valid `.docx` opinion document for completed reviews, including risks, missing clauses, recommendations, and evidence citations.
- **FR-026**: The system MUST support creating and updating an email draft without sending it. Drafts MUST store recipient, subject, body, review/version IDs, provider, provider draft ID, sync status, and idempotency key.
- **FR-027**: Mail provider credentials MUST be supplied through deployment secrets; the default QQ Mail adapter MUST use an IMAP Drafts append/update flow or an approved provider API and MUST never log credentials or full email bodies.
- **FR-028**: Email draft synchronization MUST be tenant-scoped, retryable, idempotent, and observable through a status endpoint; local development MUST provide a dry-run/mock provider.

### Key Entities

- **UnifiedDocument**: Versioned normalized representation of one uploaded document, including parser provenance, metadata, pages, blocks, spans, tables, and derived text.
- **DocumentPage**: One page with dimensions, page classification, parse quality, blocks, and optional OCR metadata.
- **DocumentBlock**: Reading-order unit such as heading, paragraph, list, table, or footer; includes text offsets, parent ID, and one-to-many span locations.
- **DocumentSpan**: Lowest-level text/geometry unit used for precise evidence and highlighting.
- **DocumentChunk**: Structure-aware retrieval unit linked to document, section, blocks, pages, and embedding metadata.
- **ReviewEvidence**: A finding's source reference containing document/chunk/block/span IDs, quote, confidence, and one or more page locations.
- **EvidenceLocation**: A normalized page/bbox target with resolution status and coordinate metadata used by PDF.js navigation.
- **ReviewOpinion**: A delivery-oriented projection of a completed review containing prioritized findings and recommendations.
- **EmailDraft**: A saved, unsent message linked to a review and optionally synchronized to a mailbox provider.
- **MailProviderSync**: Provider, remote draft ID, idempotency key, status, retry count, and last error for an email draft.
- **ParseAttempt**: Record of parser selection, version, status, quality score, warnings, and fallback lineage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least 95% of benchmark text-PDF risk findings resolve to the correct page and source region without fuzzy matching.
- **SC-002**: At least 90% of multi-line and cross-page benchmark clauses retain complete multi-location evidence.
- **SC-003**: The review, RAG, and PDF display paths consume the same document version and do not independently reparse the source PDF.
- **SC-004**: Text PDFs do not invoke full-document OCR; hybrid PDFs invoke OCR only for pages classified as scan/low-quality.
- **SC-005**: A parser failure or fallback decision is visible in persisted ingestion metadata and can be diagnosed without reading raw process logs.
- **SC-006**: Existing contract review E2E flows continue to pass after Phase 1 migration.
- **SC-007**: Hybrid retrieval improves labeled-clause Recall@10 over vector-only retrieval without exceeding the configured P95 latency budget.
- **SC-008**: Every reranked context item exposes its lexical rank, vector rank, fused score, rerank score, and provenance IDs for audit.
- **SC-009**: A completed review exposes contract-chunk retrieval diagnostics and every selected contract chunk links back to its document version and page range.
- **SC-010**: Re-running vector migration and switching document versions never exposes chunks from a non-current version and does not duplicate embeddings.
- **SC-011**: At least 95% of clickable benchmark findings navigate to the correct page and first source region using evidence IDs; no unresolved finding jumps to an unrelated first location.
- **SC-012**: Opinion and Word exports contain the same finding counts and evidence IDs as the on-screen completed review.
- **SC-013**: Saving the same email draft operation repeatedly creates one remote draft and one local draft record, without sending mail.
- **SC-014**: Provider failures remain retryable and visible; credentials and full message bodies are absent from logs.

## Assumptions

- PostgreSQL remains the system of record; the document AST may initially be stored as JSON plus relational provenance tables.
- PyMuPDF and PDF.js remain in the stack for geometry and browser rendering.
- Phase 1 uses the existing PyMuPDF span extraction to establish provenance before Docling integration.
- Docling, MinerU, and OCR engines are introduced behind adapters and may be feature-flagged during rollout.
- The first production deployment runs on Railway Linux; Windows-only OCR paths are out of scope.
- Existing legacy review results are not retroactively reprocessed unless explicitly requested.
- Human correction tooling and multi-provider cloud OCR are later phases, not prerequisites for the first migration.
