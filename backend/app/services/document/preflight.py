from dataclasses import dataclass

@dataclass(frozen=True)
class PageMetrics:
    page: int
    width: float
    height: float
    text_chars: int
    image_area_ratio: float
    has_fonts: bool
    classification: str

def inspect_pdf(file_path: str) -> list[PageMetrics]:
    import fitz
    result = []
    with fitz.open(file_path) as pdf:
        for index, page in enumerate(pdf):
            text_chars = len(page.get_text().strip())
            images = page.get_images(full=True)
            area = sum((page.rect.width * page.rect.height for _ in images), 0.0)
            ratio = min(1.0, area / max(page.rect.width * page.rect.height, 1.0))
            classification = "text" if text_chars >= 100 else ("hybrid" if text_chars else "scan")
            result.append(PageMetrics(index, page.rect.width, page.rect.height, text_chars, ratio,
                                      bool(page.get_fonts()), classification))
    return result
