"""
LLM 客户端 - DeepSeek
"""
import httpx
from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeepSeekLLMClient:
    """DeepSeek API 客户端"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL  # deepseek-chat
        self.timeout = 180.0  # 180 秒超时，合同审查需要更长时间

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
        logger.info(f"[LLM] Calling DeepSeek API: {self.base_url}/chat/completions")

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

    async def chat_with_json_output(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek 并期望 JSON 格式输出
        通过 system prompt 强制 JSON 输出
        """
        import json
        import re

        # 添加 JSON 输出指令
        system_message = {
            "role": "system",
            "content": "你是一个专业的法律审查助手。请严格按照 JSON 格式输出审查结果，不要包含任何解释性文字，不要使用 markdown 代码块。确保 JSON 格式正确，所有字符串都正确转义。输出示例：{\"risk_clauses\":[],\"missing_clauses\":[],\"suggestions\":[],\"legal_references\":[]}"
        }
        messages_with_system = [system_message] + messages

        logger.info(f"[LLM] Calling DeepSeek API with JSON output, model: {self.model}")

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
                    "max_tokens": 4096
                }
            )
            response.raise_for_status()
            data = response.json()
            response_text = data["choices"][0]["message"]["content"]

        logger.info(f"[LLM] Received response, length: {len(response_text)}")

        # 尝试解析 JSON
        try:
            # 清理可能的 markdown 标记
            clean_text = response_text.strip()

            # 移除 ```json 或 ``` 开头和结尾
            if clean_text.startswith("```"):
                clean_text = re.sub(r'^```(json)?\s*', '', clean_text)
                clean_text = re.sub(r'\s*```$', '', clean_text)

            clean_text = clean_text.strip()

            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM] JSON parse failed, trying to fix: {e}")
            # 尝试修复常见的 JSON 问题
            try:
                # 移除换行符和多余空格
                fixed_text = re.sub(r'\s+', ' ', clean_text)
                return json.loads(fixed_text)
            except:
                pass

            # 如果还是失败，尝试提取 JSON 部分
            try:
                json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if json_match:
                    logger.info("[LLM] Extracted JSON from response")
                    return json.loads(json_match.group())
            except:
                pass

            logger.error(f"[LLM] Failed to parse JSON response: {response_text[:500]}")
            raise ValueError(f"无法解析 JSON 响应：{response_text[:500]}...") from e


# 全局客户端实例
zhipu_llm = DeepSeekLLMClient()
