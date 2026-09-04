from app.services.document.coordinates import normalize_bbox
from app.services.document.identity import stable_id, validate_offsets

def test_bbox_is_clamped_and_ordered():
    box = normalize_bbox((110, 90, -2, -1), 100, 80)
    assert box.x0 == 0 and box.y0 == 0 and box.x1 == 100 and box.y1 == 80

def test_ids_are_deterministic_and_offsets_are_bounded():
    assert stable_id("a") == stable_id("a")
    validate_offsets("abc", 0, 3)
