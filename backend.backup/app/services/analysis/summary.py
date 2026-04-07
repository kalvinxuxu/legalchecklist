"""
合同条款摘要生成服务
提取关键条款并标记风险/利好点
"""
from typing import Dict, Any, List
from app.services.llm.client import zhipu_llm


class ClauseSummaryService:
    """条款摘要生成服务"""

    # 不同合同类型需要关注的条款
    CLAUSE_TEMPLATES = {
        "NDA": ["保密范围", "保密义务", "保密期限", "违约责任", "双方权利义务", "终止条款"],
        "劳动合同": ["合同期限", "工作内容", "劳动报酬", "社会保险", "工作时间", "休息休假", "违约责任", "解除条款"],
        "采购合同": ["标的物", "价格与支付", "交付验收", "质量保证", "违约责任", "退货条款"],
        "销售合同": ["标的物", "价格与支付", "交付验收", "质量保证", "违约责任", "售后条款"],
        "服务合同": ["服务内容", "服务费用", "服务期限", "双方义务", "违约责任", "服务验收"],
    }

    # 支付相关关键词
    PAYMENT_KEYWORDS = ["支付", "付款", "金额", "费用", "报酬", "价款", "租金", "利息", "违约金", "赔偿"]
    # 违约相关关键词
    BREACH_KEYWORDS = ["违约", "违约金", "赔偿", "损失", "责任", "补偿", "罚款", "解约", "终止"]

    async def generate_summary(
        self,
        contract_text: str,
        contract_type: str = "NDA",
        review_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        生成条款摘要

        Args:
            contract_text: 合同文本
            contract_type: 合同类型
            review_result: 审查结果（用于获取风险条款）

        Returns:
            摘要结果，包含：
            - key_clauses: 关键条款 [{title, summary, category, risk_benefit}]
            - payment_terms: 支付条款（金额、方式、时间）
            - breach_liability: 违约责任摘要
            - quick_cards: 快速理解卡片数据
        """
        prompt = self._build_summary_prompt(contract_text, contract_type, review_result)

        result = await zhipu_llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        return self._transform_result(result, contract_type)

    def _build_summary_prompt(
        self,
        contract_text: str,
        contract_type: str,
        review_result: Dict[str, Any] = None
    ) -> str:
        """构建摘要生成 Prompt"""

        # 获取该合同类型需要关注的条款
        focus_clauses = self.CLAUSE_TEMPLATES.get(
            contract_type,
            self.CLAUSE_TEMPLATES["NDA"]
        )
        focus_hint = "、".join(focus_clauses)

        # 如果有审查结果，加入风险条款信息
        risk_info = ""
        if review_result and review_result.get("risk_clauses"):
            risk_clauses = review_result["risk_clauses"][:5]  # 只取前5条
            risk_info = "\n\n## 已识别的风险条款（供参考）\n"
            for i, c in enumerate(risk_clauses, 1):
                risk_info += f"{i}. [{c.get('risk_level', 'unknown')}] {c.get('original_text', '')[:100]}...\n"

        return f"""你是一位专业律师，请分析以下{contract_type}合同的关键条款。

## 需要重点关注的条款类型
{focus_hint}

## 待分析合同
{contract_text[:8000]}

{risk_info}

## 输出要求
请提取关键条款并生成摘要，以 JSON 格式输出：

{{
  "key_clauses": [
    {{
      "title": "条款名称",
      "summary": "条款核心内容（50字以内）",
      "category": "payment|breach|obligation|term|other",
      "risk_benefit": "risk|benefit|neutral"
    }}
  ],
  "payment_terms": {{
    "amount": "金额相关信息（如有）",
    "payment_method": "支付方式",
    "payment_time": "支付时间节点",
    "currency": "货币类型"
  }},
  "breach_liability": {{
    "default_definitions": "违约情形定义",
    "liability_content": "违约责任内容",
    "compensation_range": "赔偿范围（如有）"
  }},
  "quick_cards": {{
    "contract_purpose": "合同目的/用途",
    "key_dates": ["关键日期列表"],
    "payment_summary": "支付条款概要",
    "breach_summary": "违约责任概要",
    "core_obligations": ["双方核心义务列表"]
  }}
}}

注意：
1. 只关注实际存在的条款，不要虚构
2. 如果某类条款不存在于合同中，对应字段填空字符串或空数组
3. 只输出 JSON，不要有其他文字
"""

    def _transform_result(
        self,
        result: Dict[str, Any],
        contract_type: str
    ) -> Dict[str, Any]:
        """转换结果格式"""
        return {
            "contract_type": contract_type,
            "key_clauses": result.get("key_clauses", []),
            "payment_terms": result.get("payment_terms", {}),
            "breach_liability": result.get("breach_liability", {}),
            "quick_cards": result.get("quick_cards", {}),
        }


# 全局服务实例
clause_summary_service = ClauseSummaryService()
