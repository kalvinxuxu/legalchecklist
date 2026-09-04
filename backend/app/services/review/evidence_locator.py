"""Evidence location for completed review findings.

The active review workflow uses this module. Legacy Celery orchestration is
intentionally not part of the runtime path.
"""
from sqlalchemy import select
from app.db.session import db
from app.models.contract_understanding import ContractUnderstanding
from app.models.clause_location import ClauseLocation
from app.models.document import DocumentRecord, DocumentVersion
from app.models.document_provenance import ReviewEvidence
from app.services.document.evidence_resolver import resolve_quote
from app.services.document.identity import stable_id
from app.schemas.document import UnifiedDocument
from app.services.pdf.locator import clause_locator
from app.services.pdf.reader import pdf_reader


async def locate_clauses_in_pdf(contract_id: str, file_path: str, risk_clauses: list) -> dict[str, dict]:
    async with db.async_session_maker() as lookup:
        document = (await lookup.execute(select(DocumentRecord).where(DocumentRecord.contract_id == contract_id))).scalar_one_or_none()
        version = await lookup.get(DocumentVersion, document.current_version_id) if document and document.current_version_id else None
    locations_by_clause = []
    if version and version.status == "completed" and version.ast_snapshot:
        ast = UnifiedDocument.model_validate(version.ast_snapshot)
        locations_by_clause = [
            [{"page": loc.page, "bbox": loc.bbox.model_dump() if loc.bbox else None,
              "span_id": loc.span_id, "similarity": 1.0, "match_type": "exact"}
             for loc in resolve_quote(ast, clause.get("original_text", ""))[0]]
            for clause in risk_clauses[:10]
        ]
    if not locations_by_clause or not any(locations_by_clause):
        pdf_data = pdf_reader.extract_text_with_positions(file_path)
        if pdf_data and pdf_data.get("needs_ocr") and pdf_data.get("has_text") is False:
            pdf_data = await pdf_reader.extract_with_ocr(file_path)
        locations_by_clause = clause_locator.batch_locate(
            [c.get("original_text", "") for c in risk_clauses[:10]],
            pdf_data.get("text_positions", []) if pdf_data else [],
            is_ocr=bool(pdf_data and pdf_data.get("source") == "ocr"),
            ocr_result=pdf_data if pdf_data and pdf_data.get("source") == "ocr" else None,
        )
    evidence_by_index: dict[str, dict] = {}
    async with db.async_session_maker() as session:
        understanding = (await session.execute(select(ContractUnderstanding).where(ContractUnderstanding.contract_id == contract_id))).scalar_one_or_none()
        document = document or (await session.execute(select(DocumentRecord).where(DocumentRecord.contract_id == contract_id))).scalar_one_or_none()
        for index, clause in enumerate(risk_clauses[:10]):
            original_text = clause.get("original_text", "")
            evidence_id = stable_id(contract_id, original_text, prefix="ev")
            evidence_locations = []
            for loc in locations_by_clause[index] if index < len(locations_by_clause) else []:
                bbox = loc.get("bbox")
                evidence_locations.append({"page": loc.get("page"), "bbox": bbox, "span_id": loc.get("span_id")})
                session.add(ClauseLocation(
                    contract_id=contract_id, understanding_id=understanding.id if understanding else None,
                    clause_hash=str(abs(hash(clause.get("original_text", ""))))[:16],
                    clause_title=clause.get("title", ""), clause_text=clause.get("original_text", ""),
                    risk_level=clause.get("risk_level", "medium"), page_number=loc.get("page"),
                    bbox_x0=bbox.get("x0") if bbox else None, bbox_y0=bbox.get("y0") if bbox else None,
                    bbox_x1=bbox.get("x1") if bbox else None, bbox_y1=bbox.get("y1") if bbox else None,
                    similarity=loc.get("similarity"), match_type=loc.get("match_type"),
                    extra_data={"evidence_id": evidence_id, "document_id": document.id if document else None,
                                "version_id": document.current_version_id if document else None},
                ))
            has_bbox = any(location.get("bbox") for location in evidence_locations)
            evidence_by_index[str(index)] = {
                "evidence_id": evidence_id,
                "locations": evidence_locations,
                "resolution_status": "resolved" if has_bbox else "page_only" if evidence_locations else "unresolved",
            }
            if document and document.current_version_id and await session.get(ReviewEvidence, evidence_id) is None:
                session.add(ReviewEvidence(
                    id=evidence_id, review_run_id=None, risk_id=str(index), document_id=document.id,
                    version_id=document.current_version_id, quote=original_text,
                    locations=evidence_locations,
                    match_type="offset_exact" if has_bbox else "page_only",
                    confidence=max((float(loc.get("similarity") or 0.0) for loc in (locations_by_clause[index] if index < len(locations_by_clause) else [])), default=0.0),
                ))
        await session.commit()
    return evidence_by_index
