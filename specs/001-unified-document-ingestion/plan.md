# Implementation Plan: Unified Document Ingestion and Provenance

**Branch**: `001-unified-document-ingestion` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-unified-document-ingestion/spec.md`

**Note**: This template is filled in by the `$speckit-plan` command; its definition describes the execution workflow.

## Summary

Introduce a versioned internal `UnifiedDocument` AST as the single source of truth for PDF text, page geometry, structure-aware chunks, LLM evidence, and frontend highlighting. This plan also closes the evidence-navigation gap and adds a delivery layer: findings use stable evidence IDs for deterministic PDF jumps, reviewers can export a concise opinion and Word document, and can save an unsent email draft through an idempotent mailbox-provider adapter. Existing review APIs remain compatible through additive fields.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11; TypeScript/Vue 3 frontend

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy async, PostgreSQL/pgvector, PyMuPDF, PDF.js, python-docx; parser adapters for Docling/MinerU/OCR and a QQ Mail IMAP/provider adapter introduced behind optional boundaries

**Storage**: PostgreSQL for business/provenance metadata, evidence locations, opinion/email drafts, BM25 full-text retrieval, LangGraph checkpoints, and pgvector production embeddings; Chroma is compatibility fallback only

**Testing**: pytest unit/integration tests, existing frontend Vitest and Playwright E2E flows, fixture-based parser benchmark

**Target Platform**: Railway Linux runtime and browser PDF.js client; local Windows development remains supported where dependencies permit

**Project Type**: Web application with asynchronous document-processing worker

**Performance Goals**: Avoid full-document OCR for text PDFs; keep ingestion asynchronous; make evidence-ID navigation deterministic; preserve current review UX; establish benchmark targets of >=95% direct evidence mapping and >=90% complete cross-page evidence

**Constraints**: Must preserve current API/UI behavior during migration; coordinates must normalize to a documented top-left page system; OCR must be Linux-compatible; no direct business dependency on vendor ASTs; vector migration must be repeatable and version-scoped

**Retrieval strategy**: Retrieve legal/policy and current-contract structure-aware chunks from PostgreSQL BM25 and pgvector in parallel. Fuse the top 40 candidates with Reciprocal Rank Fusion (RRF, configurable `k=60`), apply a configurable cross-encoder provider (`BAAI/bge-reranker-v2-m3` locally by default, Jina as an API provider), then apply deterministic legal metadata rules. The final score is `0.75 * semantic_score + 0.15 * authority_score + 0.10 * metadata_score`; effective-date and tenant/version filters are hard constraints, not score hints.

**Scale/Scope**: Existing SaaS MVP; text, scan, hybrid, table-heavy, malformed PDF fixtures, and representative DOCX contracts; local offline validation precedes Railway deployment. Reranking is applied to a bounded Top40 candidate set to control CPU/API latency.

**Rollout decisions**: PyMuPDF is the current production parser/geometry engine. Docling remains opt-in until its adapter passes AST parity, table integrity, evidence, and layout benchmarks. PostgreSQL pgvector is the production vector source of truth; Chroma data must be migrated before pgvector-only cutover. BM25-only is an explicit degraded mode and must never be reported as hybrid.

**Delivery decisions**: The existing full review report export remains backward compatible. Add a compact opinion projection and `.docx` exporter rather than making the frontend assemble document content. Save-draft is an unsent operation with a local outbox/status record; QQ Mail synchronization is provider-isolated and mockable locally. No send-email capability is included in this feature.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The repository constitution is still the default placeholder template, so no project-specific gates are defined. This plan adopts the intended safeguards implied by the feature: library boundaries, test-first contracts for the AST, integration tests for parser/review/UI handoff, structured logging, and additive/versioned changes. **Gate: PASS with no unresolved clarification.**

## Project Structure

### Documentation (this feature)

```text
specs/001-unified-document-ingestion/
├── plan.md              # This file ($speckit-plan command output)
├── research.md          # Phase 0 output ($speckit-plan command)
├── data-model.md        # Phase 1 output ($speckit-plan command)
├── quickstart.md        # Phase 1 output ($speckit-plan command)
├── contracts/           # Phase 1 output ($speckit-plan command)
└── tasks.md             # Phase 2 output ($speckit-tasks command - NOT created by $speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
backend/
├── app/
│   ├── models/                  # persisted provenance, review evidence, opinions, and mail drafts
│   ├── schemas/                 # API/AST validation models
│   ├── services/document/       # parser adapters and UnifiedDocument assembly
│   ├── services/pdf/            # geometry, coordinate normalization, evidence resolver
│   ├── services/delivery/       # opinion/Word export and mailbox draft providers
│   ├── services/rag/            # chunking, BM25/vector hybrid retrieval, reranking
│   ├── services/review/         # evidence-aware prompts/results
│   └── api/v1/endpoints/        # additive ingestion/status/evidence/delivery APIs
└── tests/
    ├── fixtures/                # representative PDFs and expected AST snapshots
    ├── unit/
    └── integration/

frontend/
├── src/
│   ├── components/              # PDF.js + bbox overlay + evidence navigation
│   ├── composables/              # additive evidence/ingestion queries
│   └── views/
└── e2e/
```

**Structure Decision**: Extend the existing backend service boundaries and retain the existing frontend PDF.js viewer. Introduce the AST and parser adapters in `backend/app/services/document`, persist provenance through backend models/services, add delivery services under `backend/app/services/delivery`, and expose additive API fields. Do not make review code import DoclingDocument or MinerU output directly. The frontend passes evidence IDs to the viewer; it does not perform text similarity matching for resolved findings.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | The design stays within the existing backend/frontend projects. |
