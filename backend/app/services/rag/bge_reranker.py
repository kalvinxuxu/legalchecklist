"""Lazy local BGE cross-encoder provider.

The optional transformers dependency is loaded only when this provider is used.
"""
from typing import Sequence
from app.services.rag.reranker_providers import RerankScore, sigmoid


class BGEReranker:
    provider = "bge_local"
    version = "v2-m3"

    def __init__(self, model_name: str, batch_size: int = 8, cache_dir: str | None = None):
        self.model = model_name
        self.batch_size = batch_size
        self.cache_dir = cache_dir
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
            except ImportError as exc:
                raise RuntimeError("BGE provider requires optional transformers dependency") from exc
            kwargs = {"cache_dir": self.cache_dir} if self.cache_dir else {}
            tokenizer = AutoTokenizer.from_pretrained(self.model, **kwargs)
            model = AutoModelForSequenceClassification.from_pretrained(self.model, **kwargs)
            model.eval()
            self._model = (tokenizer, model)
        return self._model

    def score(self, query: str, passages: Sequence[str]) -> list[RerankScore]:
        import torch
        tokenizer, model = self._load()
        output: list[RerankScore] = []
        for start in range(0, len(passages), self.batch_size):
            batch = list(passages[start:start + self.batch_size])
            inputs = tokenizer([query] * len(batch), batch, padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                logits = model(**inputs).logits.view(-1).tolist()
            output.extend(RerankScore(start + offset, sigmoid(float(value))) for offset, value in enumerate(logits))
        return output
