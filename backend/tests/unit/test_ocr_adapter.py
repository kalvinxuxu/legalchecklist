from app.services.document.ocr_adapter import LinuxOCRAdapter

def test_ocr_confidence_is_normalized():
    assert LinuxOCRAdapter._confidence({"conf": ["80", "-1", "60"]}) == .7
