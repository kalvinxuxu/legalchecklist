"""
Word 文档建议生成引擎

调用 LLM 基于风险条款生成修改建议
"""
from typing import List, Dict, Any, Optional
from app.services.llm.client import zhipu_llm


class SuggestionEngine:
    """AI 建议生成引擎"""

    def __init__(self):
        self.llm = zhipu_llm

    async def generate_suggestion(
        self,
        risk_clause: Dict[str, Any],
        contract_type: str = "其他",
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        为单个风险条款生成修改建议

        Args:
            risk_clause: 风险条款信息
                {
                    "title": "条款标题",
                    "original_text": "原文内容",
                    "risk_level": "high/medium/low",
                    "risk_description": "风险描述"
                }
            contract_type: 合同类型
            context: 额外上下文（合同背景等）

        Returns:
            建议信息
            {
                "suggestion_text": "建议修改后的文本",
                "reason": "修改理由",
                "law_reference": "相关法律依据"
            }
        """
        prompt = self._build_suggestion_prompt(
            risk_clause, contract_type, context
        )

        response = await self.llm.chat([{"role": "user", "content": prompt}])

        return self._parse_suggestion_response(
            response, risk_clause
        )

    async def generate_suggestions_batch(
        self,
        risk_clauses: List[Dict[str, Any]],
        contract_type: str = "其他",
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量生成风险条款的修改建议

        Args:
            risk_clauses: 风险条款列表
            contract_type: 合同类型
            context: 额外上下文

        Returns:
            建议列表
        """
        suggestions = []

        for clause in risk_clauses:
            suggestion = await self.generate_suggestion(
                clause, contract_type, context
            )
            suggestions.append({
                "clause": clause,
                "suggestion": suggestion,
                "paragraph_index": clause.get("paragraph_index"),
                "accepted": False  # 默认未采纳
            })

        return suggestions

    def _build_suggestion_prompt(
        self,
        risk_clause: Dict[str, Any],
        contract_type: str,
        context: Optional[str]
    ) -> str:
        """构建建议生成的 Prompt"""
        title = risk_clause.get("title", "未知条款")
        original_text = risk_clause.get("original_text", "")
        risk_level = risk_clause.get("risk_level", "medium")
        risk_desc = risk_clause.get("risk_description", "")

        risk_level_map = {
            "high": "高风险",
            "medium": "中风险",
            "low": "低风险"
        }
        risk_text = risk_level_map.get(risk_level, "未知风险")

        context_part = f"\n\n合同背景：{context}" if context else ""

        prompt = f"""你是一位专业的法律顾问，正在帮助用户修改合同中的风险条款。

合同类型：{contract_type}
条款类型：{title}
风险等级：{risk_text}
风险描述：{risk_desc}
{context_part}

原始条款内容：
---
{original_text}
---

请为上述风险条款提供修改建议。

要求：
1. 给出修改后的条款文本（尽量保留原意，但消除风险）
2. 解释修改的主要理由
3. 如有相关法律依据，请引用

请以 JSON 格式回复：
{{
    "suggestion_text": "修改后的条款文本",
    "reason": "修改理由",
    "law_reference": "相关法律依据（可选）"
}}

请直接返回 JSON，不要有其他内容："""

        return prompt

    def _parse_suggestion_response(
        self,
        response: str,
        risk_clause: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析 LLM 响应，提取建议"""
        import json
        import re

        # 尝试从响应中提取 JSON
        json_match = re.search(
            r'\{[^{}]*"suggestion_text"[^{}]*"reason"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            response,
            re.DOTALL
        )

        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "suggestion_text": result.get("suggestion_text", ""),
                    "reason": result.get("reason", ""),
                    "law_reference": result.get("law_reference", "")
                }
            except json.JSONDecodeError:
                pass

        # 如果无法解析 JSON，返回默认结构
        return {
            "suggestion_text": "",
            "reason": "建议生成失败，请手动修改",
            "law_reference": ""
        }

    async def map_clause_to_paragraph(
        self,
        contract_text: str,
        clause_text: str
    ) -> Optional[int]:
        """
        将风险条款映射到 Word 文档的段落索引

        Args:
            contract_text: 合同全文（用于搜索）
            clause_text: 条款文本

        Returns:
            段落索引，未找到返回 None
        """
        # 简单匹配：找到 clause_text 在 contract_text 中的位置
        # 然后估算段落索引

        # 更准确的方式是在前端通过文字匹配返回 paragraph_index
        # 这里只是预留接口

        return None


# 全局实例
suggestion_engine = SuggestionEngine()
