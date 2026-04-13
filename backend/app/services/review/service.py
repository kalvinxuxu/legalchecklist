"""
合同审查服务核心逻辑
"""
from typing import Dict, Any, List, Optional
from app.services.rag.retriever import retriever
from app.services.review.rules.nda import NDA_REVIEW_RULES
from app.services.review.rules.labor import LABOR_CONTRACT_REVIEW_RULES
from app.services.review.knowledge_manager import KnowledgeRetrievalManager
from app.services.review.context_builder import PartitionedContextBuilder
from app.services.review.prompt_builder import EnhancedPromptBuilder


class ContractReviewService:
    """合同审查服务"""

    def __init__(self):
        self.rag = retriever
        self.knowledge_manager = KnowledgeRetrievalManager()
        self.context_builder = PartitionedContextBuilder()
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
            - risk_clauses: 风险条款
            - missing_clauses: 缺失条款
            - suggestions: 修改建议
            - legal_references: 法条引用
            - policy_references: 公司政策引用
            - confidence_score: 置信度评分
        """
        # 1. 分区检索法律知识和公司政策
        partitioned_context = await self.knowledge_manager.retrieve_all(
            contract_type=contract_type,
            tenant_id=tenant_id
        )

        # 2. 构建分区上下文
        law_context = self.context_builder.build_law_context(
            partitioned_context.get("law", [])
        )
        policy_context = self.context_builder.build_policy_context(
            partitioned_context.get("company_policy", [])
        )

        # 3. 获取对应规则库
        rules = self.rules_map.get(contract_type, [])

        # 4. 构建 Prompt
        prompt = EnhancedPromptBuilder.build_review_prompt(
            contract_text=contract_text,
            contract_type=contract_type,
            law_context=law_context,
            policy_context=policy_context,
            rules=rules
        )

        # 5. 调用 LLM 生成审查报告
        from app.services.llm.client import zhipu_llm
        review_result = await zhipu_llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        # 6. 计算置信度评分（含政策参考）
        review_result["confidence_score"] = self._calculate_confidence(
            partitioned_context, review_result
        )

        # 7. 转换字段名称以匹配前端期望
        review_result = self._transform_review_result(review_result)

        return review_result

    def _transform_review_result(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """转换审查结果字段名称"""
        transformed = review_result.copy()

        if "risk_clauses" not in transformed or transformed["risk_clauses"] is None:
            transformed["risk_clauses"] = []
        elif transformed["risk_clauses"]:
            risk_clauses_new = []
            for clause in review_result.get("risk_clauses", []):
                original_text = clause.get("original_text", "")
                title = original_text[:50] + "..." if len(original_text) > 50 else original_text
                if not title and clause.get("risk_description"):
                    title = clause.get("risk_description")[:50] + "..." if len(clause.get("risk_description")) > 50 else clause.get("risk_description")
                if not title:
                    title = f"风险条款 #{len(risk_clauses_new) + 1}"

                transformed_clause = {
                    "title": title,
                    "original_text": original_text,
                    "risk_description": clause.get("risk_description", ""),
                    "risk_level": clause.get("risk_level", "medium"),
                    "suggestion": clause.get("suggestion", ""),
                    "legal_reference": clause.get("legal_reference", ""),
                    "policy_reference": clause.get("policy_reference", "")
                }
                risk_clauses_new.append(transformed_clause)
            transformed["risk_clauses"] = risk_clauses_new

        if "missing_clauses" not in transformed or transformed["missing_clauses"] is None:
            transformed["missing_clauses"] = []
        elif transformed["missing_clauses"]:
            missing_clauses_new = []
            for clause in review_result.get("missing_clauses", []):
                transformed_clause = {
                    "title": clause.get("title", ""),
                    "description": clause.get("description", ""),
                    "suggestion": clause.get("suggestion", self._generate_missing_suggestion(clause)),
                    "legal_reference": clause.get("legal_reference", ""),
                    "policy_reference": clause.get("policy_reference", "")
                }
                missing_clauses_new.append(transformed_clause)
            transformed["missing_clauses"] = missing_clauses_new

        if "suggestions" not in transformed or transformed["suggestions"] is None:
            transformed["suggestions"] = []
        elif transformed["suggestions"]:
            transformed["suggestions"] = [
                {
                    "title": s.get("title", "修改建议"),
                    "content": s.get("content", ""),
                    "reason": s.get("reason", "")
                }
                for s in review_result.get("suggestions", [])
            ]

        # 确保 policy_references 字段存在
        if "policy_references" not in transformed:
            transformed["policy_references"] = []
        elif transformed["policy_references"]:
            transformed["policy_references"] = [
                {
                    "policy_name": p.get("policy_name", ""),
                    "section": p.get("section", ""),
                    "content": p.get("content", "")
                }
                for p in review_result.get("policy_references", [])
            ]

        return transformed

    def _generate_missing_suggestion(self, clause: Dict[str, Any]) -> str:
        """为缺失条款生成默认建议"""
        title = clause.get("title", "该条款")
        legal_ref = clause.get("legal_reference", "")
        policy_ref = clause.get("policy_reference", "")
        base_suggestion = f"建议在合同中添加{title}条款"
        if legal_ref:
            base_suggestion += f"，以符合{legal_ref}的要求"
        if policy_ref:
            base_suggestion += f"；同时需满足公司政策：{policy_ref}"
        return base_suggestion + "。"

    def _calculate_confidence(
        self,
        partitioned_context: Dict[str, List[Dict[str, Any]]],
        review_result: Dict[str, Any]
    ) -> float:
        """计算置信度评分 - 考虑法律和政策两种依据"""
        total_items = sum(len(items) for items in partitioned_context.values())
        if total_items == 0:
            return 0.3

        base_score = 0.5

        # 知识覆盖度奖励
        coverage_bonus = min(0.3, total_items * 0.05)

        # 质量奖励（基于平均相似度）
        all_scores = []
        for items in partitioned_context.values():
            all_scores.extend([item.get("score", 0.5) for item in items])

        if all_scores:
            avg_quality = sum(all_scores) / len(all_scores)
            quality_bonus = min(0.15, avg_quality / 5)
        else:
            quality_bonus = 0

        # 完整性奖励
        completeness = self._check_response_completeness(review_result)
        completeness_bonus = completeness * 0.05

        return min(1.0, base_score + coverage_bonus + quality_bonus + completeness_bonus)

    def _check_response_completeness(self, review_result: Dict[str, Any]) -> float:
        """检查响应完整性"""
        required_keys = [
            "risk_clauses", "missing_clauses", "suggestions",
            "legal_references", "policy_references"
        ]
        present_keys = sum(
            1 for key in required_keys
            if key in review_result and review_result[key]
        )
        return present_keys / len(required_keys)


# 全局服务实例
review_service = ContractReviewService()
