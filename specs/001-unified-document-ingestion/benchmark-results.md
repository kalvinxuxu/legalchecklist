# Benchmark Results

The deterministic smoke fixture currently reports:

| Metric | Result |
|---|---:|
| Recall@10 | 1.00 |
| MRR | 0.75 |
| nDCG@10 | 0.75 |
| Duplicate rate | 0.00 |

This is a smoke test, not a production quality claim. Production acceptance requires labeled legal-clause data and a real PostgreSQL/Chroma latency run.

## Real sample preflight

The four local sample contracts were inspected without copying their contents into the repository:

| Sample | Pages | Text-layer pages | Route |
|---|---:|---:|---|
| 2018年三批次2标合同 | 44 | 0 | scan → OCR |
| 20220425-保利大连中车厂项目合同 | 24 | 0 | scan → OCR |
| 20220916联合体协议书final | 7 | 7 | text/structural |
| 产权交易合同样本 | 10 | 0 | scan → OCR |

The structural sample exposed and verified the span-offset robustness fix in the PyMuPDF adapter.
# Reranker upgrade validation - 2026-09-02

## Labeled provider comparison - 2026-09-03

Command: `PYTHONPATH=backend python backend/scripts/benchmark_rag_retrieval.py`

| Provider | Status | Cases | Recall@10 | MRR | nDCG@10 | Duplicate rate | Authority violations | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| vector-only | ok | 2 | 1.00 | 0.50 | 0.50 | 0.00 | 0 | 0.017 |
| legacy feature | ok | 2 | 1.00 | 1.00 | 1.00 | 0.00 | 0 | 0.033 |
| BGE local offline fixture | ok | 2 | 1.00 | 1.00 | 1.00 | 0.00 | 0 | 0.033 |
| Jina | unavailable | - | - | - | - | - | - | - |

Jina was correctly marked unavailable because `JINA_API_KEY` was not configured. The
offline BGE row is a deterministic fixture substitute, not a claim about the real
cross-encoder. Run with `--live` after downloading BGE and configuring Jina for
production-provider measurements.

## Live provider comparison - 2026-09-03

Command: `PYTHONPATH=backend python backend/scripts/benchmark_rag_retrieval.py --live`

The local BGE model was available and executed successfully on six labeled cases:

| Provider | Status | Cases | Recall@10 | MRR | nDCG@10 | Duplicate rate | Authority violations | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| vector-only | ok | 6 | 1.00 | 0.50 | 0.50 | 0.00 | 1 | 0.016 |
| legacy feature | ok | 6 | 1.00 | 1.00 | 1.00 | 0.00 | 0 | 0.067 |
| BGE local real | ok | 6 | 1.00 | 1.00 | 1.00 | 0.00 | 0 | 3106.010 |
| Jina | unavailable | - | - | - | - | - | - | - |

The real BGE CPU P95 exceeds the configured 1200ms target. It should not be the
default Railway provider without resource/candidate tuning; Jina requires a
configured `JINA_API_KEY` before its latency can be measured.

## Local deterministic smoke

- `backend/test_contract.docx`: parsing and retrieval audit passed; provider reported `deterministic_fallback` as configured.
- `示范文件/2018年三批次2标合同.pdf`: first page rendered successfully; text extraction returned empty because the sample is scan/image-based and the local Chinese OCR language pack is not enabled.

## Labeled retrieval fixture

Command: `PYTHONPATH=backend python backend/scripts/benchmark_rag_retrieval.py backend/tests/fixtures/rag/retrieval.json`

| Provider | Cases | Recall@10 | MRR | nDCG@10 | Duplicate rate |
|---|---:|---:|---:|---:|---:|
| deterministic_fallback | 2 | 1.00 | 0.75 | 0.75 | 0.00 |

## Real-contract OCR smoke

With `TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe`, `TESSDATA_PREFIX=C:\\Program Files\\Tesseract-OCR\\tessdata`, and `RAG_RERANKER_PROVIDER=deterministic_fallback`:

| File | Pages | Extracted chars | Result |
|---|---:|---:|---|
| `20220425-保利大连中车厂项目合同.pdf` | 24 | 24,971 | Tesseract + `chi_sim` passed |
| `20220907联合体协议书(final） (003)-法务意见.docx` | 1 | 4,423 | python-docx passed |
| `20220916联合体协议书final.pdf` | 7 | 5,388 | PyMuPDF AST + exact evidence passed |
| `2018年三批次2标合同.pdf` | 44 | 53,647 | Tesseract + `chi_sim` passed |

The OCR result is text-only legacy provenance; exact PDF span evidence is available for the text PDF, while OCR pages require page-level evidence unless OCR boxes are persisted. This remains a smoke baseline, not a production quality claim. BGE/Jina comparison remains pending until the BGE model is downloaded and a labeled candidate fixture is available.
