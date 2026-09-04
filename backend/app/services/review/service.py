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

def validate_evidence_ids(result: Dict[str, Any], allowed_ids: set[str]) -> Dict[str, Any]:
    """Drop fabricated evidence references while preserving legacy text fields."""
    for clause in result.get("risk_clauses", []) or []:
        evidence_id = clause.get("evidence_id")
        if evidence_id and evidence_id not in allowed_ids:
            clause.pop("evidence_id", None)
            clause["evidence_warning"] = "unknown_evidence_id"
    return result


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
        tenant_id: Optional[str] = None,
        party_position: Optional[str] = None,
        contract_amount: Optional[float] = None,
        risk_preference: Optional[str] = None,
        partitioned_context: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        contract_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        审查合同并生成报告

        Args:
            contract_text: 合同文本
            contract_type: 合同类型 (NDA/劳动合同/采购合同/等)
            tenant_id: 租户 ID（用于私有库检索）
            party_position: 甲乙方立场 ("party_a" | "party_b")
            contract_amount: 合同金额（元）
            risk_preference: 风险偏好 ("low" | "medium" | "high")

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
        if partitioned_context is None:
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
        contract_chunk_context = self.context_builder.build_contract_context(contract_context or [])

        # 3. 获取对应规则库
        rules = self.rules_map.get(contract_type, [])

        # 4. 构建 Prompt（支持甲乙方立场、金额、风险偏好）
        prompt = EnhancedPromptBuilder.build_review_prompt(
            contract_text=contract_text,
            contract_type=contract_type,
            law_context=law_context,
            policy_context=policy_context,
            contract_chunk_context=contract_chunk_context,
            rules=rules,
            party_position=party_position,
            contract_amount=contract_amount,
            risk_preference=risk_preference
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
        diagnostics = self._retrieval_diagnostics(partitioned_context)
        diagnostics["contract_chunks"] = len(contract_context or [])
        diagnostics["contract_top_candidates"] = [
            {key: item.get(key) for key in ("chunk_id", "document_version_id", "page_start", "page_end",
                                             "bm25_rank", "vector_rank", "fused_score", "rerank_score",
                                             "retrieval_mode", "reranker_provider", "fallback_reason")}
            for item in (contract_context or [])[:10]
        ]
        review_result["retrieval_diagnostics"] = diagnostics

        return review_result

    @staticmethod
    def _retrieval_diagnostics(partitioned_context: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        items = [item for values in partitioned_context.values() for item in values]
        modes = sorted({item.get("retrieval_mode") for item in items if item.get("retrieval_mode")})
        return {"modes": modes or ["legacy_or_unknown"], "candidate_count": len(items),
                "top_candidates": [{key: item.get(key) for key in (
                    "id", "bm25_rank", "vector_rank", "fused_rank", "rerank_rank", "bm25_score",
                    "vector_score", "fused_score", "semantic_score", "authority_score", "metadata_score",
                    "rerank_score", "reranker_provider", "reranker_model", "fallback_reason")}
                    for item in items[:10]]}

    def _transform_review_result(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """转换审查结果字段名称 + 解析规则判定结果"""
        transformed = review_result.copy()

        # ========== 新增：解析规则判定结果 ==========
        transformed = self._parse_rule_judgments(transformed)

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

    def _parse_rule_judgments(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 LLM 返回的规则判定结果

        提取 violations、approvals_needed、compliant
        并计算 approval_flow 和 overall_risk_level
        """
        rule_judgments = review_result.get("rule_judgments", {})
        if not rule_judgments:
            # 如果 LLM 没有返回 rule_judgments，尝试从 risk_clauses 推导
            return self._infer_rule_judgments_from_risk_clauses(review_result)

        # 解析 violations（违反政策 - ❌ 必须修改）
        violations = rule_judgments.get("violations", [])
        transformed_violations = []
        for v in violations:
            transformed_violations.append({
                "clause_type": v.get("clause_type", ""),
                "original_text": v.get("original_text", ""),
                "extracted_value": v.get("extracted_value", ""),
                "policy_limit": v.get("policy_limit", ""),
                "judgment": v.get("judgment", "❌ 违反政策"),
                "suggestion": v.get("suggestion", ""),
                "risk_level": "high"
            })

        # 解析 approvals_needed（需要审批 - ⚠️）
        approvals_needed = rule_judgments.get("approvals_needed", [])
        transformed_approvals = []
        for a in approvals_needed:
            transformed_approvals.append({
                "clause_type": a.get("clause_type", ""),
                "original_text": a.get("original_text", ""),
                "extracted_value": a.get("extracted_value", ""),
                "threshold": a.get("threshold", ""),
                "judgment": a.get("judgment", "⚠️ 需要审批"),
                "suggestion": a.get("suggestion", "建议走法务审批流程"),
                "risk_level": "medium"
            })

        # 解析 compliant（合规 - ✅）
        compliant = rule_judgments.get("compliant", [])
        transformed_compliant = []
        for c in compliant:
            transformed_compliant.append({
                "clause_type": c.get("clause_type", ""),
                "original_text": c.get("original_text", ""),
                "extracted_value": c.get("extracted_value", ""),
                "policy_standard": c.get("policy_standard", ""),
                "judgment": c.get("judgment", "✅ 合规"),
                "risk_level": "low"
            })

        # 更新 review_result
        review_result["rule_judgments"] = {
            "violations": transformed_violations,
            "approvals_needed": transformed_approvals,
            "compliant": transformed_compliant
        }

        # 计算审批流程
        if transformed_violations:
            review_result["approval_flow"] = "executive_approval"  # 高风险：上级审批+法务复核
            review_result["overall_risk_level"] = "high"
        elif transformed_approvals:
            review_result["approval_flow"] = "legal_review"  # 中风险：法务审核
            review_result["overall_risk_level"] = "medium"
        else:
            review_result["approval_flow"] = "auto"  # 低风险：自动通过
            review_result["overall_risk_level"] = "low"

        # 添加审批流程说明
        approval_flow_map = {
            "auto": "✅ 自动通过 - 所有条款符合公司政策",
            "legal_review": "⚠️ 法务审核 - 部分条款需要法务审批",
            "executive_approval": "❌ 上级审批 - 存在违反政策的条款，需要上级审批+法务复核"
        }
        review_result["approval_flow_description"] = approval_flow_map.get(
            review_result["approval_flow"],
            "⚠️ 需要审核"
        )

        return review_result

    def _infer_rule_judgments_from_risk_clauses(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        如果 LLM 没有返回 rule_judgments，从 risk_clauses 推导

        这是向后兼容的处理方式
        """
        risk_clauses = review_result.get("risk_clauses", [])
        if not risk_clauses:
            # 没有任何风险条款，所有都合规
            review_result["rule_judgments"] = {
                "violations": [],
                "approvals_needed": [],
                "compliant": [{"clause_type": "整体合同", "judgment": "✅ 合规", "risk_level": "low"}]
            }
            review_result["approval_flow"] = "auto"
            review_result["overall_risk_level"] = "low"
            review_result["approval_flow_description"] = "✅ 自动通过 - 所有条款符合公司政策"
            return review_result

        # 根据 risk_level 分类
        violations = []
        approvals_needed = []
        compliant = []

        for clause in risk_clauses:
            risk_level = clause.get("risk_level", "medium")
            judgment = {
                "clause_type": clause.get("title", "风险条款"),
                "original_text": clause.get("original_text", ""),
                "judgment": clause.get("risk_description", ""),
                "suggestion": clause.get("suggestion", ""),
                "policy_reference": clause.get("policy_reference", ""),
                "risk_level": risk_level
            }

            if risk_level == "high":
                violations.append(judgment)
            elif risk_level == "medium":
                approvals_needed.append(judgment)
            else:
                compliant.append(judgment)

        review_result["rule_judgments"] = {
            "violations": violations,
            "approvals_needed": approvals_needed,
            "compliant": compliant
        }

        # 重新计算审批流程
        if violations:
            review_result["approval_flow"] = "executive_approval"
            review_result["overall_risk_level"] = "high"
        elif approvals_needed:
            review_result["approval_flow"] = "legal_review"
            review_result["overall_risk_level"] = "medium"
        else:
            review_result["approval_flow"] = "auto"
            review_result["overall_risk_level"] = "low"

        approval_flow_map = {
            "auto": "✅ 自动通过 - 所有条款符合公司政策",
            "legal_review": "⚠️ 法务审核 - 部分条款需要法务审批",
            "executive_approval": "❌ 上级审批 - 存在违反政策的条款，需要上级审批+法务复核"
        }
        review_result["approval_flow_description"] = approval_flow_map.get(
            review_result["approval_flow"],
            "⚠️ 需要审核"
        )

        return review_result

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
