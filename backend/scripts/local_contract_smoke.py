"""Local PDF/DOCX contract validation before cloud deployment.

Default mode is deterministic and offline: it validates parsing, provenance,
chunking, and evidence resolution without calling an LLM. Use --live only when
local PostgreSQL, model credentials, and the application dependencies are ready.
"""
import argparse, asyncio, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.document.parser import document_parser
from app.services.document.assembler import UnifiedDocumentAssembler
from app.services.document.evidence_resolver import resolve_quote
from app.services.document.identity import document_id, version_id
from app.services.rag.structure_chunker import chunk_document
from app.services.rag.reranker import reranker
from app.schemas.document import UnifiedDocument

async def inspect_file(path: Path, live: bool = False, retrieval_audit: bool = False) -> dict:
    suffix = path.suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise ValueError("只支持 .pdf 和 .docx")
    parsed = await (document_parser.parse_pdf(str(path)) if suffix == ".pdf" else document_parser.parse_word(str(path)))
    text = (parsed.get("text") or "").strip()
    if not text:
        raise ValueError("未提取到合同文本；扫描 PDF 需要启用 Linux OCR")
    result = {"file": str(path), "format": suffix[1:], "pages": parsed.get("pages", 1), "text_chars": len(text), "source": parsed.get("source")}
    if suffix == ".pdf" and parsed.get("unified_document"):
        ast = UnifiedDocument.model_validate(parsed["unified_document"])
        ast = UnifiedDocumentAssembler().assemble(ast)
        chunks = chunk_document(ast)
        quote = next((span.text for page in ast.pages for block in page.blocks for span in block.spans if len(span.text.strip()) >= 10), "")
        locations, match_type, confidence = resolve_quote(ast, quote) if quote else ([], "none", 0.0)
        result.update({"document_id": ast.document_id, "version_id": ast.version_id, "blocks": sum(len(p.blocks) for p in ast.pages), "spans": sum(len(b.spans) for p in ast.pages for b in p.blocks), "chunks": len(chunks), "evidence": {"quote": quote, "locations": [x.model_dump(mode="json") for x in locations], "match_type": match_type, "confidence": confidence}})
    else:
        result.update({"review_mode": "legacy_text", "paragraphs": len(parsed.get("paragraphs", [])), "note": "DOCX 当前保持兼容文本解析；PDF provenance 字段不适用于 DOCX"})
    if retrieval_audit:
        candidates = [{"id": f"local-{i}", "content": text[i:i + 1200], "authority_level": "article", "section_path": "local"}
                      for i in range(0, min(len(text), 40 * 1200), 1200)]
        result["retrieval_audit"] = {
            "candidate_count": min(len(candidates), 40),
            "items": reranker.rerank(text[:80], candidates, top_k=min(8, len(candidates))),
        }
    if live:
        from app.services.review.service import review_service
        live_result = await review_service.review_contract(
            contract_text=text, contract_type="其他", tenant_id=None,
            partitioned_context={"law": [], "company_policy": []})
        result["review"] = {"status": "live_passed", "risk_count": len(live_result.get("risk_clauses", [])),
                             "retrieval_diagnostics": live_result.get("retrieval_diagnostics")}
    else:
        result["review"] = {"status": "smoke_passed", "risk_clauses": [{"original_text": text[:160], "risk_level": "manual_review"}]}
    return result

async def main(paths: list[str], live: bool = False, retrieval_audit: bool = False) -> int:
    reports = []
    exit_code = 0
    for raw in paths:
        path = Path(raw)
        try:
            if not path.exists(): raise FileNotFoundError(path)
            reports.append(await inspect_file(path.resolve(), live, retrieval_audit))
        except Exception as exc:
            exit_code = 1; reports.append({"file": str(path), "status": "failed", "error": str(exc)})
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return exit_code

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate local PDF/DOCX contract review inputs")
    parser.add_argument("paths", nargs="+", help="合同文件路径")
    parser.add_argument("--live", action="store_true", help="标记为线上模型/API联调模式")
    parser.add_argument("--retrieval-audit", action="store_true", help="执行本地三阶段检索审计")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.paths, args.live, args.retrieval_audit)))
