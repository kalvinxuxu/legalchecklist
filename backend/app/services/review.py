"""
合同审查服务
"""
from typing import Dict, Any, List
from app.services.llm.client import deepseek_client
from app.services.rag.retriever import retriever


class ContractReviewService:
    """合同审查服务"""

    def __init__(self):
        self.llm = deepseek_client
        self.rag = retriever

    async def review_contract(
        self,
        contract_text: str,
        contract_type: str = "NDA"
    ) -> Dict[str, Any]:
        """
        审查合同并生成报告

        Args:
            contract_text: 合同文本
            contract_type: 合同类型 (NDA/劳动合同/采购合同/等)

        Returns:
            审查报告，包含：
            - risk_clauses: 风险条款
            - missing_clauses: 缺失条款
            - suggestions: 修改建议
            - legal_references: 法条引用
            - confidence_score: 置信度评分
        """
        # 1. 检索相关法律知识
        context = await self.rag.retrieve(
            query=f"{contract_type} 合同审查要点 法律规定",
            content_type="law",
            top_k=5
        )

        # 2. 构建 Prompt
        prompt = self._build_review_prompt(
            contract_text=contract_text,
            contract_type=contract_type,
            context=context
        )

        # 3. 调用 LLM 生成审查报告
        review_result = await self.llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        # 4. 添加置信度评分
        review_result["confidence_score"] = self._calculate_confidence(context)

        return review_result

    def _build_review_prompt(
        self,
        contract_text: str,
        contract_type: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """构建审查 Prompt"""

        context_text = "\n\n".join([
            f"【{item['title'] or item['content'][:50]}】\n{item['content']}"
            for item in context
        ]) if context else "无相关法律依据"

        return f"""你是一位专业的合同审查律师，请审查以下{contract_type}合同。

## 参考法律依据
{context_text}

## 待审查合同
{contract_text}

## 审查要求
请从以下维度审查合同，并以 JSON 格式输出：

1. **risk_clauses** (风险条款数组):
   - clause: 原条款内容
   - risk_level: 风险等级 (high/medium/low)
   - reason: 风险原因
   - suggestion: 修改建议
   - legal_reference: 引用的法条

2. **missing_clauses** (缺失条款数组):
   - clause_name: 缺失的条款名称
   - importance: 重要程度 (high/medium/low)
   - description: 说明为何需要此条款

3. **suggestions** (综合修改建议数组):
   - suggestion: 具体建议

4. **legal_references** (引用的法律法规数组):
   - law_name: 法律名称
   - article: 条款号
   - content: 法条内容

输出 JSON 格式示例：
{{
  "risk_clauses": [{{"clause": "...", "risk_level": "high", "reason": "...", "suggestion": "...", "legal_reference": "《民法典》第 XXX 条"}}],
  "missing_clauses": [{{"clause_name": "...", "importance": "high", "description": "..."}}],
  "suggestions": [{{"suggestion": "..."}}],
  "legal_references": [{{"law_name": "...", "article": "...", "content": "..."}}]
}}
"""

    def _calculate_confidence(self, context: List[Dict[str, Any]]) -> float:
        """
        计算置信度评分

        基于检索到的上下文数量和质量
        """
        if not context:
            return 0.3

        # 基础置信度
        base_score = 0.5

        # 根据检索结果数量增加置信度
        count_bonus = min(0.3, len(context) * 0.06)

        # 平均质量分数
        avg_quality = sum(item.get("score", 0.5) for item in context) / len(context)
        quality_bonus = avg_quality * 0.2

        return min(1.0, base_score + count_bonus + quality_bonus)


# 全局服务实例
review_service = ContractReviewService()
