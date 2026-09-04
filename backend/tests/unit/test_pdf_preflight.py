from app.services.document.quality_gate import score_page, passes_quality

def test_quality_gate_distinguishes_text_and_scan_pages():
    text_score=score_page(600, 0.1, True); scan_score=score_page(0, 1.0, False)
    assert passes_quality(text_score) and scan_score < text_score
