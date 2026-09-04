from typing import Protocol
from app.schemas.document import UnifiedDocument

class DocumentParserAdapter(Protocol):
    name: str
    version: str
    def parse(self, file_path: str, document_id: str, version_id: str) -> UnifiedDocument: ...

class AdapterResult:
    def __init__(self, document: UnifiedDocument, quality_score: float, warnings=None):
        self.document = document
        self.quality_score = quality_score
        self.warnings = warnings or []
