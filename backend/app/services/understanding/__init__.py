"""
合同理解服务 - 流式输出
"""
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
import logging

from app.services.llm.deepseek import deepseek_llm

logger = logging.getLogger(__name__)


class UnderstandingService:
    """合同理解服务 - 支持流式输出"""

    def __init__(self):
        self.llm = deepseek_llm

    async def generate_summary_stream(
        self,
        contract_text: str,
        contract_type: str = "其他"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成合同摘要

        Yields:
            {"type": "section", "title": "...", "content": "..."}
        """
        prompt = f"""你是一位专业的法律文档分析师。请对以下{contract_type}合同进行结构化分析。

合同内容：
{contract_text[:8000]}

请按以下结构输出摘要，每个部分流式输出：
1. 合同基本信息（双方名称、签订日期等）
2. 合同主要目的和范围
3. 关键权利义务
4. 重要条款摘要

使用 JSON 格式输出：
{{"type": "section", "title": "部分标题", "content": "部分内容"}}

只输出 JSON，不要其他文字。"""

        buffer = ""
        async for token in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            buffer += token
            # 尝试解析
            result = self._try_parse_json(buffer)
            if result:
                yield result
                buffer = ""

    async def extract_key_clauses_stream(
        self,
        contract_text: str,
        contract_type: str = "其他"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式提取关键条款

        Yields:
            {"type": "clause", "title": "条款名称", "summary": "条款摘要"}
        """
        prompt = f"""你是一位专业的法律文档分析师。请从以下{contract_type}合同中提取关键条款。

合同内容：
{contract_text[:8000]}

请提取以下关键条款：
1. 定义与解释条款
2. 各方权利义务
3. 付款/报酬条款
4. 保密条款
5. 知识产权条款
6. 违约责任
7. 争议解决
8. 其他重要条款

使用 JSON 格式输出每个条款：
{{"type": "clause", "title": "条款名称", "summary": "条款摘要", "importance": "high/medium/low"}}

只输出 JSON 数组，每条 JSON 占一行。不要其他文字。"""

        buffer = ""
        async for token in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            buffer += token
            # 尝试按行解析 JSON
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("{"):
                    result = self._try_parse_json(line)
                    if result:
                        yield result

    async def explain_term_stream(
        self,
        term: str,
        contract_text: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        流式解释术语

        Yields:
            术语解释的文本片段
        """
        context = f"\n\n参考合同内容：\n{contract_text[:2000]}" if contract_text else ""

        prompt = f"""请解释以下法律/合同术语，并给出在合同中的应用示例：{term}{context}

请用通俗易懂的语言解释，适合非法律专业人士理解。"""

        async for token in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            yield token

    async def answer_question(
        self,
        question: str,
        contract_text: str,
        contract_type: str = "其他"
    ) -> str:
        """
        回答关于合同的问题（非流式）

        Args:
            question: 问题
            contract_text: 合同文本
            contract_type: 合同类型

        Returns:
            回答内容
        """
        prompt = f"""你是一位专业的法律文档分析助手。请根据以下{contract_type}合同内容回答问题。

合同内容：
{contract_text[:8000]}

问题：{question}

请用中文回答，如果合同中没有相关信息，请说明"根据提供的合同内容，无法回答此问题"。"""

        return await self.llm.chat([{"role": "user", "content": prompt}])

    async def analyze_risk_factors_stream(
        self,
        contract_text: str,
        contract_type: str = "其他"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式分析合同风险因素

        Yields:
            {"type": "risk", "title": "风险名称", "description": "风险描述", "level": "high/medium/low"}
        """
        prompt = f"""你是一位专业的法律风险分析师。请分析以下{contract_type}合同的风险因素。

合同内容：
{contract_text[:8000]}

请识别以下风险：
1. 不平等条款（对一方过于有利）
2. 模糊或不明确的条款
3. 隐藏费用或义务
4. 过重的违约责任
5. 不合理的终止条款
6. 知识产权风险
7. 保密和数据安全风险

使用 JSON 格式输出每个风险：
{{"type": "risk", "title": "风险名称", "description": "风险描述", "level": "high/medium/low"}}

只输出 JSON 数组，每条 JSON 占一行。不要其他文字。"""

        buffer = ""
        async for token in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            buffer += token
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("{"):
                    result = self._try_parse_json(line)
                    if result:
                        yield result

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """尝试解析 JSON"""
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None


# 全局实例
understanding_service = UnderstandingService()
