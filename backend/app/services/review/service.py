"""
合同审查服务核心逻辑
"""
from typing import Dict, Any, List, Optional
from app.services.llm.client import zhipu_llm
from app.services.rag.retriever import retriever
from app.services.review.rules.nda import NDA_REVIEW_RULES
from app.services.review.rules.labor import LABOR_CONTRACT_REVIEW_RULES


class ContractReviewService:
    """合同审查服务"""

    def __init__(self):
        self.llm = zhipu_llm
        self.rag = retriever
        self.rules_map = {
            "NDA": NDA_REVIEW_RULES,
            "劳动合同": LABOR_CONTRACT_REVIEW_RULES
        }

    async def review_contract(
        self,
        contract_text: str,
        contract_type: str = "NDA",
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        审查合同并生成报告

        Args:
            contract_text: 合同文本
            contract_type: 合同类型 (NDA/劳动合同/采购合同/等)
            tenant_id: 租户 ID（用于私有库检索）

        Returns:
            审查报告，包含：
            - risk_clauses: 风险条款 (original_text, risk_description, risk_level, suggestion, legal_reference)
            - missing_clauses: 缺失条款 (title, description, suggestion, legal_reference)
            - suggestions: 修改建议
            - legal_references: 法条引用
            - confidence_score: 置信度评分
        """
        # 1. 检索相关法律知识
        context = await self.rag.retrieve(
            query=f"{contract_type} 合同审查要点 法律规定",
            content_type="law",
            top_k=5,
            tenant_id=tenant_id
        )

        # 2. 获取对应规则库
        rules = self.rules_map.get(contract_type, [])

        # 3. 构建 Prompt
        prompt = self._build_review_prompt(
            contract_text=contract_text,
            contract_type=contract_type,
            context=context,
            rules=rules
        )

        # 4. 调用 LLM 生成审查报告
        review_result = await self.llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        # 5. 添加置信度评分
        review_result["confidence_score"] = self._calculate_confidence(context, review_result)

        # 6. 转换字段名称以匹配前端期望
        review_result = self._transform_review_result(review_result)

        return review_result

    def _transform_review_result(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换审查结果字段名称，确保与前端期望的格式匹配

        LLM 返回的格式（与前端期望一致）：
        - risk_clauses[].original_text -> 保留
        - risk_clauses[].risk_description -> 保留
        - risk_clauses[].title -> 从 original_text 截取生成
        - missing_clauses[].title -> 保留
        - missing_clauses[].description -> 保留
        - missing_clauses[].suggestion -> 保留
        - missing_clauses[].legal_reference -> 保留
        """
        transformed = review_result.copy()

        # 确保 risk_clauses 字段格式正确
        if "risk_clauses" in transformed and transformed["risk_clauses"]:
            transformed["risk_clauses"] = []
            for clause in review_result.get("risk_clauses", []):
                original_text = clause.get("original_text", "")
                # 从 original_text 生成 title（截取前 50 个字符）
                title = original_text[:50] + "..." if len(original_text) > 50 else original_text
                # 如果 original_text 为空，使用 risk_description 生成 title
                if not title and clause.get("risk_description"):
                    title = clause.get("risk_description")[:50] + "..." if len(clause.get("risk_description")) > 50 else clause.get("risk_description")
                # 如果都为空，使用默认标题
                if not title:
                    title = f"风险条款 #{len(transformed['risk_clauses']) + 1}"

                transformed_clause = {
                    "title": title,
                    "original_text": original_text,
                    "risk_description": clause.get("risk_description", ""),
                    "risk_level": clause.get("risk_level", "medium"),
                    "suggestion": clause.get("suggestion", ""),
                    "legal_reference": clause.get("legal_reference", "")
                }
                transformed["risk_clauses"].append(transformed_clause)

        # 确保 missing_clauses 字段格式正确
        if "missing_clauses" in transformed and transformed["missing_clauses"]:
            transformed["missing_clauses"] = []
            for clause in review_result.get("missing_clauses", []):
                transformed_clause = {
                    "title": clause.get("title", ""),
                    "description": clause.get("description", ""),
                    "suggestion": clause.get("suggestion", self._generate_missing_suggestion(clause)),
                    "legal_reference": clause.get("legal_reference", "")
                }
                transformed["missing_clauses"].append(transformed_clause)

        # 确保 suggestions 格式正确
        if "suggestions" in transformed and transformed["suggestions"]:
            transformed["suggestions"] = [
                {
                    "title": s.get("title", "修改建议"),
                    "content": s.get("content", ""),
                    "reason": s.get("reason", "")
                }
                for s in review_result.get("suggestions", [])
            ]

        return transformed

    def _generate_missing_suggestion(self, clause: Dict[str, Any]) -> str:
        """为缺失条款生成默认建议"""
        title = clause.get("title", "该条款")
        legal_ref = clause.get("legal_reference", "")
        description = clause.get("description", "")

        base_suggestion = f"建议在合同中添加{title}条款"
        if legal_ref:
            base_suggestion += f"，以符合{legal_ref}的要求"
        base_suggestion += "。"

        return base_suggestion

    def _build_review_prompt(
        self,
        contract_text: str,
        contract_type: str,
        context: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> str:
        """构建审查 Prompt"""

        # 法律依据
        context_text = "\n\n".join([
            f"【{item.get('title') or item['content'][:50]}】\n{item['content']}"
            for item in context
        ]) if context else "无相关法律依据"

        # 审查规则
        rules_text = ""
        if rules:
            rules_text = "\n\n## 审查规则参考\n"
            rules_text += "请根据以下审查规则进行检查：\n\n"
            for rule in rules[:10]:  # 限制规则数量，避免 prompt 过长
                rules_text += f"- {rule['name']}（{rule['risk_type']}）：{rule['check_prompt']}\n"
            if len(rules) > 10:
                rules_text += f"... 等共 {len(rules)} 条规则"

        return f"""你是一位专业律师，请审查以下{{contract_type}}合同。

## 参考法律依据
{context_text}
{rules_text}

## 待审查合同
{contract_text}

## 审查要求
请从以下维度审查合同，并以 JSON 格式输出：

1. **risk_clauses** (风险条款数组):
   - original_text: 原条款内容
   - risk_level: 风险等级 (high/medium/low)
   - risk_description: 风险原因描述
   - suggestion: 修改建议
   - legal_reference: 引用的法条

2. **missing_clauses** (缺失条款数组):
   - title: 缺失的条款名称
   - description: 说明为何需要此条款
   - suggestion: 具体的修改/添加建议
   - legal_reference: 引用的法条（如有）

3. **suggestions** (综合修改建议数组):
   - title: 建议标题
   - content: 具体建议内容
   - reason: 建议理由

4. **legal_references** (引用的法律法规数组):
   - law_name: 法律名称
   - article: 条款号
   - content: 法条内容

输出 JSON 格式示例：
{{
  "risk_clauses": [{{"original_text": "...", "risk_level": "high", "risk_description": "...", "suggestion": "...", "legal_reference": "《民法典》第 XXX 条"}}],
  "missing_clauses": [{{"title": "...", "description": "...", "suggestion": "...", "legal_reference": "《民法典》第 XXX 条"}}],
  "suggestions": [{{"title": "...", "content": "...", "reason": "..."}}],
  "legal_references": [{{"law_name": "...", "article": "...", "content": "..."}}]
}}
"""

    def _calculate_confidence(
        self,
        context: List[Dict[str, Any]],
        review_result: Dict[str, Any]
    ) -> float:
        """
        计算置信度评分

        基于以下因素：
        1. 检索结果数量和质量
        2. LLM 响应完整性
        """
        if not context:
            return 0.3

        # 基础置信度
        base_score = 0.5

        # 根据检索结果数量增加置信度（最多 0.3）
        count_bonus = min(0.3, len(context) * 0.06)

        # 平均质量分数（基于检索得分）
        avg_quality = sum(item.get("score", 0.5) for item in context) / len(context)
        # 归一化到 0-1 范围
        normalized_quality = min(1.0, avg_quality / 2.0)
        quality_bonus = normalized_quality * 0.2

        # 基于响应完整性
        completeness = self._check_response_completeness(review_result)
        completeness_bonus = completeness * 0.1

        return min(1.0, base_score + count_bonus + quality_bonus + completeness_bonus)

    def _check_response_completeness(self, review_result: Dict[str, Any]) -> float:
        """
        检查 LLM 响应的完整性

        返回 0-1 的完整性分数
        """
        required_keys = ["risk_clauses", "missing_clauses", "suggestions", "legal_references"]
        present_keys = sum(1 for key in required_keys if key in review_result and review_result[key])
        return present_keys / len(required_keys)


# 全局服务实例
review_service = ContractReviewService()
