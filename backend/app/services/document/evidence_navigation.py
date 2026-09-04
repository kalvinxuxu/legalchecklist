"""Evidence-ID-first navigation helpers."""
from sqlalchemy import select

from app.db.session import db
from app.models.clause_location import ClauseLocation


async def get_evidence_locations(contract_id: str, evidence_id: str) -> dict:
    async with db.async_session_maker() as session:
        rows = (await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract_id)
            .where(ClauseLocation.extra_data["evidence_id"].as_string() == evidence_id)
            .order_by(ClauseLocation.page_number)
        )).scalars().all()
    if not rows:
        return {"evidence_id": evidence_id, "locations": [], "resolution_status": "unresolved"}
    first = rows[0].extra_data or {}
    return {
        "evidence_id": evidence_id,
        "document_id": first.get("document_id"),
        "version_id": first.get("version_id"),
        "resolution_status": "resolved" if any(row.bbox for row in rows) else "page_only",
        "locations": [{"page": row.page_number, "bbox": row.bbox, "coord_system": "pdf_top_left",
                       "resolution_status": "resolved" if row.bbox else "page_only"} for row in rows],
    }
