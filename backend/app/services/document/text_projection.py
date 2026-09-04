from app.schemas.document import UnifiedDocument

def project_text(document: UnifiedDocument) -> dict:
    """Compatibility shape consumed by the existing review pipeline."""
    return {"text": document.text, "pages": len(document.pages), "elements": [],
            "source": f"ast:{document.parser_name}", "document_id": document.document_id,
            "version_id": document.version_id, "unified_document": document.model_dump(mode="json")}
