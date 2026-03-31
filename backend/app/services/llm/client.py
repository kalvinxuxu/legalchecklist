"""
DeepSeek LLM 客户端
"""
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL
        self.timeout = 60.0

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> str:
        """
        调用 DeepSeek 对话 API

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度值，控制随机性
            max_tokens: 最大生成 token 数
            stream: 是否流式输出

        Returns:
            AI 回复的内容
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def chat_with_json_output(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek 并期望 JSON 格式输出

        Args:
            messages: 消息列表
            temperature: 较低温度以获得更稳定的 JSON

        Returns:
            解析后的 JSON 对象
        """
        import json

        # 添加 JSON 输出指令
        system_message = {
            "role": "system",
            "content": "请严格按照 JSON 格式输出，不要包含任何解释性文字。"
        }
        messages_with_system = [system_message] + messages

        response_text = await self.chat(
            messages=messages_with_system,
            temperature=temperature
        )

        # 尝试解析 JSON
        try:
            # 清理可能的 markdown 标记
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON 响应：{response_text[:200]}...") from e


# 全局客户端实例
deepseek_client = DeepSeekClient()
