from app.services.document.preflight import inspect_pdf
from app.services.document.quality_gate import score_page

class ParserRouter:
    """Selects page strategy without coupling business code to vendor ASTs."""
    def route(self, file_path: str) -> list[dict]:
        return [{"page": m.page, "classification": m.classification,
                 "parser": "pymupdf" if m.classification in ("text", "hybrid") else "ocr",
                 "ocr_required": m.classification in ("scan", "hybrid"),
                 "quality_score": score_page(m.text_chars, m.image_area_ratio, m.has_fonts)} for m in inspect_pdf(file_path)]
