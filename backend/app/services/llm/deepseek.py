"""
DeepSeek LLM 客户端 - 支持流式输出
"""
import httpx
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeepSeekLLM:
    """DeepSeek API 客户端 - 支持流式 SSE"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL  # deepseek-chat
        self.timeout = 300.0  # 5分钟超时

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> str:
        """
        非流式对话

        Args:
            messages: 消息列表
            temperature: 温度
            max_tokens: 最大 token 数
            stream: 是否流式

        Returns:
            AI 回复内容
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
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

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncGenerator[str, None]:
        """
        流式对话 - 生成 SSE 格式

        Args:
            messages: 消息列表
            temperature: 温度
            max_tokens: 最大 token 数

        Yields:
            每个 token 的文本片段
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def chat_with_json_output(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        返回 JSON 格式输出（用于审查等场景）
        """
        import re

        system_message = {
            "role": "system",
            "content": "你是一个专业的法律审查助手。请严格按照 JSON 格式输出，不要包含任何解释性文字。"
        }
        messages_with_system = [system_message] + messages

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages_with_system,
                    "temperature": temperature,
                    "max_tokens": 8192
                }
            )
            response.raise_for_status()
            data = response.json()
            response_text = data["choices"][0]["message"]["content"]

        # 解析 JSON
        try:
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                clean_text = re.sub(r'^```(json)?\s*', '', clean_text)
                clean_text = re.sub(r'\s*```$', '', clean_text)
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # 尝试修复
            try:
                fixed = re.sub(r'\s+', ' ', clean_text)
                return json.loads(fixed)
            except:
                # 提取 JSON 部分
                match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if match:
                    return json.loads(match.group())
                raise ValueError(f"无法解析 JSON: {response_text[:200]}")

    async def stream_json_output(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式输出 JSON（边生成边解析）

        用于审查报告等需要结构化输出的场景
        """
        import re

        system_message = {
            "role": "system",
            "content": """你是一个专业的法律审查助手。请严格按照 JSON 格式输出。
输出示例：
{"risk_clauses": [{"original_text": "...", "risk_level": "high", "risk_description": "...", "suggestion": "..."}]}
只输出有效 JSON，不要 markdown 代码块。"""
        }
        messages_with_system = [system_message] + messages

        buffer = ""
        json_depth = 0
        in_string = False
        escape_next = False

        async for token in self.chat_stream(messages, temperature, 8192):
            buffer += token

            # 尝试解析当前 buffer
            result = self._try_parse_json_stream(buffer)
            if result:
                yield result

    def _try_parse_json_stream(self, buffer: str) -> Optional[Dict[str, Any]]:
        """尝试解析流式 JSON"""
        import json as json_lib

        # 移除非 JSON 前缀
        buffer = buffer.strip()
        if buffer.startswith("data: "):
            buffer = buffer[6:]

        # 尝试找到有效的 JSON 对象
        try:
            # 尝试解析整个 buffer
            return json_lib.loads(buffer)
        except json_lib.JSONDecodeError:
            # 检查是否以 { 开头
            if buffer.startswith("{"):
                # 可能还在接收中，返回部分结果
                # 简单检查括号平衡
                open_braces = buffer.count("{")
                close_braces = buffer.count("}")
                if open_braces > close_braces:
                    return None  # 还在接收中
            return None


# 全局实例
deepseek_llm = DeepSeekLLM()
