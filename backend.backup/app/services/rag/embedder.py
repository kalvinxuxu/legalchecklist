"""
DeepSeek Embedding 服务
"""
import httpx
from typing import List
from app.core.config import settings


class DeepSeekEmbedder:
    """DeepSeek Embedding API 客户端"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_EMBEDDING_MODEL  # deepseek-embedding
        self.timeout = 30.0

    async def embed(self, text: str) -> List[float]:
        """
        生成文本的向量嵌入

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
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
        """
        批量生成向量

        Args:
            texts: 文本列表
            batch_size: 批量大小

        Returns:
            向量列表
        """
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
embedder = DeepSeekEmbedder()
