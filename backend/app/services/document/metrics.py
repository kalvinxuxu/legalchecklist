from collections import Counter

class IngestionMetrics:
    def __init__(self): self._counts = Counter()
    def inc(self, name: str, value: int = 1): self._counts[name] += value
    def snapshot(self) -> dict: return dict(self._counts)

ingestion_metrics = IngestionMetrics()
