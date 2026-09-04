def score_page(text_chars: int, image_area_ratio: float, has_fonts: bool) -> float:
    score = min(1.0, text_chars / 500.0) * 0.7 + (0.2 if has_fonts else 0) + (0.1 if image_area_ratio < 0.8 else 0)
    return round(max(0.0, min(1.0, score)), 3)

def passes_quality(score: float, threshold: float = 0.75) -> bool:
    return score >= threshold
