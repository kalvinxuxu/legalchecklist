"""
智谱 AI Embedding 服务
"""
import httpx
from typing import List
from app.core.config import settings


class ZhipuEmbedder:
    """智谱 AI Embedding API 客户端"""

    def __init__(self):
        self.api_key = settings.ZHIPU_EMBEDDING_API_KEY
        self.base_url = settings.ZHIPU_EMBEDDING_BASE_URL
        self.model = settings.ZHIPU_EMBEDDING_MODEL
        self.timeout = 30.0

    async def embed(self, text: str) -> List[float]:
        """生成文本的向量嵌入"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """批量生成向量"""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": batch
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings.extend([d["embedding"] for d in data["data"]])
        return embeddings


# 全局嵌入服务实例
embedder = ZhipuEmbedder()
