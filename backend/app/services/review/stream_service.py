"""
合同审查服务 - 流式输出
"""
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
import logging

from app.services.llm.deepseek import deepseek_llm

logger = logging.getLogger(__name__)


class ReviewStreamService:
    """合同审查服务 - 支持流式输出"""

    def __init__(self):
        self.llm = deepseek_llm

    async def review_contract_stream(
        self,
        contract_text: str,
        contract_type: str = "其他",
        rules: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式审查合同，输出风险条款

        Yields:
            {
                "type": "risk_clause" | "missing_clause" | "suggestion" | "legal_ref" | "progress" | "done",
                ...
            }
        """
        # 1. 发送开始信号
        yield {
            "type": "progress",
            "stage": "analyzing",
            "message": "开始分析合同内容..."
        }
        await asyncio.sleep(0.1)

        # 2. 构建审查 prompt
        rules_text = ""
        if rules:
            rules_text = "\n\n审查规则：\n" + "\n".join([
                f"- {r.get('name', '规则')}: {r.get('check_prompt', '')}"
                for r in rules[:10]
            ])

        prompt = f"""你是一位专业律师，请审查以下{contract_type}合同。

## 审查要求
1. 识别风险条款
2. 指出缺失条款
3. 提供修改建议
4. 引用相关法律依据

{rules_text}

## 合同内容
{contract_text[:10000]}

## 输出格式
请按以下顺序输出，每发现一项就输出：

=== 风险条款 ===
{{"type": "risk_clause", "title": "条款名称", "original_text": "原条款内容", "risk_level": "high/medium/low", "risk_description": "风险描述", "suggestion": "修改建议", "legal_reference": "法条引用"}}

=== 缺失条款 ===
{{"type": "missing_clause", "title": "缺失条款名称", "description": "为什么需要此条款", "suggestion": "建议添加内容", "legal_reference": "法条引用"}}

=== 修改建议 ===
{{"type": "suggestion", "title": "建议标题", "content": "建议内容", "reason": "理由"}}

=== 法条引用 ===
{{"type": "legal_reference", "law_name": "法律名称", "article": "条款号", "content": "法条内容"}}

每条 JSON 占一行，只输出有效 JSON，不要其他文字。"""

        buffer = ""
        risk_count = 0
        missing_count = 0
        suggestion_count = 0

        async for token in self.llm.chat_stream([{"role": "user", "content": prompt}]):
            buffer += token

            # 尝试解析每行
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                # 跳过标记行
                if line.startswith("==="):
                    continue

                result = self._try_parse_json(line)
                if result:
                    result_type = result.get("type", "")
                    if result_type == "risk_clause":
                        risk_count += 1
                        yield {
                            "type": "risk_clause",
                            "index": risk_count,
                            **result
                        }
                    elif result_type == "missing_clause":
                        missing_count += 1
                        yield {
                            "type": "missing_clause",
                            "index": missing_count,
                            **result
                        }
                    elif result_type == "suggestion":
                        suggestion_count += 1
                        yield {
                            "type": "suggestion",
                            "index": suggestion_count,
                            **result
                        }
                    elif result_type == "legal_reference":
                        yield {
                            "type": "legal_reference",
                            **result
                        }

        # 发送完成信号
        yield {
            "type": "done",
            "summary": {
                "risk_count": risk_count,
                "missing_count": missing_count,
                "suggestion_count": suggestion_count
            }
        }

    async def review_contract_simple(
        self,
        contract_text: str,
        contract_type: str = "其他",
        rules: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        非流式审查（一次性返回结果）

        Returns:
            完整的审查报告
        """
        rules_text = ""
        if rules:
            rules_text = "\n\n审查规则：\n" + "\n".join([
                f"- {r.get('name', '规则')}: {r.get('check_prompt', '')}"
                for r in rules[:10]
            ])

        prompt = f"""你是一位专业律师，请审查以下{contract_type}合同。

{rules_text}

合同内容：
{contract_text[:10000]}

请输出完整的审查报告，JSON 格式：
{{
  "risk_clauses": [
    {{"title": "条款名称", "original_text": "原条款", "risk_level": "high/medium/low", "risk_description": "风险描述", "suggestion": "修改建议", "legal_reference": "法条引用"}}
  ],
  "missing_clauses": [
    {{"title": "缺失条款", "description": "说明", "suggestion": "建议", "legal_reference": "法条引用"}}
  ],
  "suggestions": [
    {{"title": "建议标题", "content": "建议内容", "reason": "理由"}}
  ],
  "legal_references": [
    {{"law_name": "法律", "article": "条款号", "content": "法条内容"}}
  ]
}}

只输出 JSON，不要其他文字。"""

        result = await self.llm.chat_with_json_output([{"role": "user", "content": prompt}])

        # 确保字段存在
        result.setdefault("risk_clauses", [])
        result.setdefault("missing_clauses", [])
        result.setdefault("suggestions", [])
        result.setdefault("legal_references", [])

        return result

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """尝试解析 JSON"""
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None


# 全局实例
review_stream_service = ReviewStreamService()
