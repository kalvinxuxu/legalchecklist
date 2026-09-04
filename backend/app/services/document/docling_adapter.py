"""Optional Docling boundary; vendor output never leaves this adapter."""
class DoclingAdapter:
    name = "docling"
    version = "optional"

    def __init__(self):
        self.last_markdown = ""

    def parse(self, file_path: str, document_id: str, version_id: str):
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise RuntimeError("Docling is not installed") from exc
        from app.services.document.pymupdf_adapter import PyMuPDFAdapter
        # Keep canonical geometry stable until the Docling mapping is configured.
        result = DocumentConverter().convert(file_path)
        self.last_markdown = result.document.export_to_markdown()
        if not self.last_markdown.strip():
            raise ValueError("Docling returned empty document")
        return PyMuPDFAdapter().parse(file_path, document_id, version_id)
