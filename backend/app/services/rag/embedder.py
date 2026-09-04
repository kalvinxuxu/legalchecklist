"""Provider-neutral embedding service for legal text."""
import asyncio
import math
from typing import List
import httpx
from app.core.config import settings


def _normalize(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def _validate_dimension(vector: List[float]) -> List[float]:
    expected = settings.EMBEDDING_DIMENSION
    if len(vector) != expected:
        raise RuntimeError(
            f"embedding dimension mismatch: expected {expected}, got {len(vector)}"
        )
    return vector


class ZhipuEmbedder:
    provider = "zhipu"

    def __init__(self):
        self.api_key = settings.ZHIPU_EMBEDDING_API_KEY
        self.base_url = settings.ZHIPU_EMBEDDING_BASE_URL
        self.model = settings.ZHIPU_EMBEDDING_MODEL
        self.version = settings.EMBEDDING_MODEL_VERSION
        self.timeout = 30.0

    async def _request(self, payload):
        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.base_url}/embeddings", headers={
                        "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.25 * (2 ** attempt))
        raise last_error

    async def embed(self, text: str) -> List[float]:
        data = await self._request({"model": self.model, "input": text})
        vector = data["data"][0]["embedding"]
        return _validate_dimension(_normalize(vector) if settings.EMBEDDING_NORMALIZE else vector)

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        embeddings = []
        for start in range(0, len(texts), batch_size):
            data = await self._request({"model": self.model, "input": texts[start:start + batch_size]})
            vectors = [item["embedding"] for item in data["data"]]
            embeddings.extend(
                _validate_dimension(_normalize(vector) if settings.EMBEDDING_NORMALIZE else vector)
                for vector in vectors
            )
        return embeddings


class LocalSentenceTransformerEmbedder:
    provider = "local_sentence_transformer"

    def __init__(self):
        self.model = settings.LOCAL_EMBEDDING_MODEL
        self.version = settings.EMBEDDING_MODEL_VERSION
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError("local embedding requires sentence-transformers") from exc
            self._model = SentenceTransformer(self.model)
        return self._model

    async def embed(self, text: str) -> List[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        vectors = await asyncio.to_thread(self._load().encode, texts, batch_size=batch_size, normalize_embeddings=settings.EMBEDDING_NORMALIZE)
        return [_validate_dimension(list(map(float, vector))) for vector in vectors]


class EmbeddingService:
    def __init__(self):
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = LocalSentenceTransformerEmbedder() if settings.EMBEDDING_PROVIDER.lower() == "local" else ZhipuEmbedder()
        return self._provider

    @property
    def model(self): return self.provider.model

    @property
    def provider_name(self): return self.provider.provider

    async def embed(self, text: str) -> List[float]: return await self.provider.embed(text)

    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        return await self.provider.embed_batch(texts, batch_size)


embedder = EmbeddingService()
