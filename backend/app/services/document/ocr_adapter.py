"""Linux-safe OCR adapter. Coordinates are page-only when engine has no boxes."""
class LinuxOCRAdapter:
    name = "linux-ocr"
    version = "tesseract"
    def parse_page(self, image, language: str = "chi_sim+eng") -> dict:
        try:
            import pytesseract
        except ImportError as exc:
            raise RuntimeError("pytesseract is not installed") from exc
        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
        text = " ".join(v for v in data.get("text", []) if v.strip())
        return {"text": text, "confidence": self._confidence(data), "bbox": None}

    @staticmethod
    def _confidence(data: dict) -> float:
        values = [float(v) for v in data.get("conf", []) if str(v).strip() not in ("", "-1")]
        return round(max(0.0, min(1.0, sum(values) / len(values) / 100)), 3) if values else 0.0
