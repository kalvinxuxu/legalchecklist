"""Coordinate normalization to PDF top-left points."""
from app.schemas.document import BBox

def normalize_bbox(bbox: tuple[float, float, float, float], width: float, height: float) -> BBox:
    if width <= 0 or height <= 0:
        raise ValueError("page dimensions must be positive")
    x0, y0, x1, y1 = bbox
    values = (x0, y0, x1, y1)
    if any(v != v or v in (float("inf"), float("-inf")) for v in values):
        raise ValueError("bbox contains non-finite coordinates")
    left, right = sorted((max(0.0, x0), max(0.0, x1)))
    top, bottom = sorted((max(0.0, y0), max(0.0, y1)))
    return BBox(x0=min(left, width), y0=min(top, height), x1=min(right, width), y1=min(bottom, height))
