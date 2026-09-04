"""Cross-encoder provider contracts used by the legal RAG reranker."""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class RerankScore:
    index: int
    score: float


class RerankerProvider(Protocol):
    provider: str
    model: str
    version: str

    def score(self, query: str, passages: Sequence[str]) -> list[RerankScore]:
        """Return one normalized [0, 1] score per passage."""


def sigmoid(value: float) -> float:
    import math
    value = max(min(value, 40.0), -40.0)
    return 1.0 / (1.0 + math.exp(-value))
