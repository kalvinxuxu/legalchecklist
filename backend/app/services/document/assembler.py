from app.schemas.document import UnifiedDocument

class UnifiedDocumentAssembler:
    """Validation boundary between parser adapters and application services."""
    def assemble(self, document: UnifiedDocument) -> UnifiedDocument:
        derived = []
        for page in document.pages:
            for block in page.blocks:
                if block.bbox and (block.bbox.x1 > page.width or block.bbox.y1 > page.height):
                    raise ValueError(f"block bbox outside page {page.page_number}")
                for span in block.spans:
                    if span.char_start < block.char_start or span.char_end > block.char_end + 1:
                        raise ValueError(f"span offset outside block {block.block_id}")
                derived.append(block.text)
        if not document.text:
            document.text = "\n\n".join(derived)
        if not document.pages:
            document.warnings.append({"code": "empty_document", "message": "No pages were produced"})
        return document
