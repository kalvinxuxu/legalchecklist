"""
增强型 Prompt 构建器 - 支持法律依据和政策依据双分区 + 规则裁判模式
支持甲乙方立场、合同金额、风险偏好动态调整审查标准
"""
from typing import Dict, List, Any, Optional
from app.services.review.rules.dynamic_thresholds import DynamicThresholds


class EnhancedPromptBuilder:
    """增强型 Prompt 构建器"""

    @staticmethod
    def _build_position_config(
        party_position: Optional[str],
        contract_amount: Optional[float],
        risk_preference: Optional[str]
    ) -> str:
        """
        构建审查立场配置文本

        Args:
            party_position: 甲乙方立场
            contract_amount: 合同金额
            risk_preference: 风险偏好

        Returns:
            配置文本
        """
        lines = []

        # 甲乙方立场
        if party_position == "party_a":
            lines.append("- **你的立场**：甲方（买方/发包方）- 严格保护甲方利益，倾向于更严格的付款条件和更高的违约金保护")
        elif party_position == "party_b":
            lines.append("- **你的立场**：乙方（卖方/承包方）- 平衡乙方权益，倾向于更宽松的付款条件和更低的违约金压力")
        else:
            lines.append("- **你的立场**：中立 - 使用标准审查规则")

        # 风险偏好
        if risk_preference == "low":
            lines.append("- **风险偏好**：低风险 - 零容忍策略，严格保护公司利益，宁可错过机会也不承担风险")
        elif risk_preference == "medium":
            lines.append("- **风险偏好**：中风险 - 平衡策略，在保护和机会之间寻求平衡")
        elif risk_preference == "high":
            lines.append("- **风险偏好**：高风险 - 开放策略，可接受合理风险以换取商业机会")
        else:
            lines.append("- **风险偏好**：中等 - 使用标准风险容忍度")

        # 合同金额
        if contract_amount is not None:
            amount_str = f"{contract_amount:,.0f}元"
            if contract_amount >= 10000000:
                lines.append(f"- **合同金额**：{amount_str}（特大额合同 - 需要最严格审查）")
            elif contract_amount >= 5000000:
                lines.append(f"- **合同金额**：{amount_str}（重大合同 - 需要严格审查）")
            elif contract_amount >= 1000000:
                lines.append(f"- **合同金额**：{amount_str}（大额合同 - 需要加强审查）")
            else:
                lines.append(f"- **合同金额**：{amount_str}（标准合同 - 使用标准审查）")
        else:
            lines.append("- **合同金额**：未指定 - 使用标准审查")

        # 动态阈值说明
        if party_position and risk_preference:
            thresholds = DynamicThresholds()
            payment = thresholds.get_payment_period_thresholds(party_position, risk_preference)
            penalty = thresholds.get_penalty_rate_thresholds(party_position, risk_preference)
            confidentiality = thresholds.get_confidentiality_period_thresholds(party_position, risk_preference)

            lines.append("")
            lines.append("**动态判定阈值**（根据你的立场和风险偏好自动调整）：")
            lines.append(f"- 付款周期：≤{payment['compliant_max']}天✅合规 | {payment['compliant_max']}-{payment['approval_max']}天⚠️审批 | >{payment['violation_above']}天❌违规")

            if party_position == "party_a":
                lines.append(f"- 违约金：≥{penalty['compliant_min']}%✅充足 | {penalty['approval_min']}-{penalty['compliant_min']}%⚠️不足 | <{penalty['violation_below']}%❌严重不足")
            else:
                lines.append(f"- 违约金：≤{penalty['compliant_max']}%✅合理 | {penalty['compliant_max']}-{penalty['approval_max']}%⚠️偏高 | >{penalty['violation_above']}%❌过高")

            lines.append(f"- 保密期限：≤{confidentiality['compliant_max']}年✅ | {confidentiality['compliant_max']}-{confidentiality['approval_max']}年⚠️ | >{confidentiality['violation_above']}年❌")

        return "\n".join(lines)

    @staticmethod
    def build_review_prompt(
        contract_text: str,
        contract_type: str,
        law_context: str,
        policy_context: str,
        rules: List[Dict[str, Any]],
        contract_chunk_context: str = "未生成合同条款候选区",
        party_position: Optional[str] = None,
        contract_amount: Optional[float] = None,
        risk_preference: Optional[str] = None
    ) -> str:
        """
        构建审查 Prompt - 法律依据和政策依据分区展示 + 规则裁判判定

        Args:
            contract_text: 合同文本
            contract_type: 合同类型
            law_context: 法律依据上下文字符串
            policy_context: 公司政策上下文字符串
            rules: 审查规则列表
            party_position: 甲乙方立场 ("party_a" | "party_b")
            contract_amount: 合同金额（元）
            risk_preference: 风险偏好 ("low" | "medium" | "high")
        """
        # 构建审查立场配置文本
        position_config_text = EnhancedPromptBuilder._build_position_config(
            party_position, contract_amount, risk_preference
        )

        rules_text = ""
        if rules:
            rules_text = "\n\n## 审查规则参考\n"
            rules_text += "请根据以下审查规则进行检查：\n\n"
            for rule in rules[:10]:
                rules_text += f"- {rule['name']}（{rule['risk_type']}）：{rule['check_prompt']}\n"
            if len(rules) > 10:
                rules_text += f"... 等共 {len(rules)} 条规则"

        return f"""你是一位专业律师兼合同审查规则裁判，请审查以下{contract_type}合同。

## 审查立场配置
{position_config_text}

## 法律依据
{law_context}

## 公司政策（如有）
{policy_context}

## 已召回并重排的合同条款候选区
{contract_chunk_context}

{rules_text}

## 待审查合同
{contract_text}

## 审查要求

### 第一步：提取关键数值
请从合同中提取以下关键数值（如果合同中未明确写出，标注为"未明确"）：

- **付款周期**（天）：从付款期限条款中提取
- **违约金比例**（%）：从违约金条款中提取
- **保密期限**（年）：从保密期限条款中提取
- **合同总金额**（元）：从金额条款中提取
- **折扣率**（%）：从折扣条款中提取
- **合同期限**（月）：从合同期限条款中提取

### 第二步：规则判定（核心输出）

根据公司政策和法律法规，对每个关键条款进行以下判定：

**判定符号说明**：
- ❌ **violations** - 违反公司强制政策（必须修改才能签署）
- ⚠️ **approvals_needed** - 需要审批才能签署
- ✅ **compliant** - 符合政策，可以签署

**常见判定规则**（如公司政策中有明确规定，以政策为准）：
| 条款类型 | 判定条件 | 判定结果 |
|---------|---------|---------|
| 付款周期 | >30天 | ❌ violations |
| 付款周期 | 15-30天 | ⚠️ approvals_needed |
| 付款周期 | ≤15天 | ✅ compliant |
| 违约金 | >合同总额20% | ❌ violations |
| 违约金 | 10%-20% | ⚠️ approvals_needed |
| 违约金 | ≤10% | ✅ compliant |
| 保密期限 | >5年 | ⚠️ approvals_needed |
| 保密期限 | ≤5年 | ✅ compliant |

### 第三步：综合审查

请从以下维度审查合同，并以 JSON 格式输出。合同条款候选区、法律依据和公司政策上下文中的 source_id 是唯一允许引用的证据来源；不得编造 source_id。每个风险条款如使用外部依据，必须保留对应 source_id，供后续证据校验：

1. **rule_judgments** (规则判定 - 核心新增):
   - violations: 违反公司政策的条款数组
     - clause_type: 条款类型（如"付款周期"、"违约金"等）
     - original_text: 原条款内容
     - extracted_value: 提取的数值
     - policy_limit: 公司政策规定的上限/下限
     - judgment: "❌ 违反政策" + 原因说明
     - suggestion: 修改建议
   - approvals_needed: 需要审批的条款数组
     - clause_type: 条款类型
     - original_text: 原条款内容
     - extracted_value: 提取的数值
     - threshold: 触发审批的阈值
     - judgment: "⚠️ 需要审批" + 审批级别建议
     - suggestion: 建议的审批流程
   - compliant: 符合政策的条款数组
     - clause_type: 条款类型
     - original_text: 原条款内容
     - extracted_value: 提取的数值
     - policy_standard: 符合的政策标准
     - judgment: "✅ 合规"

2. **risk_clauses** (风险条款数组):
   - original_text: 原条款内容
   - risk_level: 风险等级 (high/medium/low)
   - risk_description: 风险原因描述
   - suggestion: 修改建议
   - legal_reference: 引用的法条（如《民法典》第153条）
   - policy_reference: **必须**引用的公司政策条款（如违反《采购管理政策》第5条）

3. **missing_clauses** (缺失条款数组):
   - title: 缺失的条款名称
   - description: 说明为何需要此条款
   - suggestion: 具体的修改/添加建议
   - legal_reference: 引用的法条（如有）
   - policy_reference: **必须**引用的公司政策条款（如有）

4. **suggestions** (综合修改建议数组):
   - title: 建议标题
   - content: 具体建议内容
   - reason: 建议理由

5. **legal_references** (引用的法律法规数组):
   - law_name: 法律名称
   - article: 条款号
   - content: 法条内容摘要

6. **policy_references** (引用的公司政策数组):
   - policy_name: 政策名称
   - section: 具体条款
   - content: 政策内容摘要

7. **approval_flow** (新增 - 审批流程建议):
   - 基于规则判定结果，建议的审批流程：
     - "auto": 所有条款合规，自动通过
     - "legal_review": 有需要审批的条款，法务审核
     - "executive_approval": 有违反政策的条款，上级审批+法务复核

8. **overall_risk_level** (新增 - 综合风险等级):
   - "low": 所有条款合规或仅有轻微问题
   - "medium": 有需要审批的条款
   - "high": 有违反政策必须修改的条款

## 重要提示
- **规则判定优先级最高**：首先完成规则判定，这是合同能否签署的关键
- **公司政策优先级**：当合同条款与公司政策冲突时，**必须**在 policy_reference 中明确引用相关公司政策规定
- **综合建议**：suggestions 中的每条建议如果涉及公司政策，也应说明依据的政策条款
- **政策引用格式**：《政策名称》第X条：具体要求内容
- **数值提取**：尽可能从合同中提取具体数值，无法提取时标注"未明确"但仍进行定性分析

输出 JSON 格式示例：
{{
  "rule_judgments": {{
    "violations": [
      {{
        "clause_type": "付款周期",
        "original_text": "付款期限为交货后360天",
        "extracted_value": "360天",
        "policy_limit": "不超过30天",
        "judgment": "❌ 违反政策：付款周期360天超过公司规定的30天上限制",
        "suggestion": "建议将付款期限修改为30天以内"
      }}
    ],
    "approvals_needed": [
      {{
        "clause_type": "违约金",
        "original_text": "违约金为合同总额的25%",
        "extracted_value": "25%",
        "threshold": "超过20%需审批",
        "judgment": "⚠️ 需要审批：违约金25%超过20%审批阈值",
        "suggestion": "建议走法务审批流程"
      }}
    ],
    "compliant": [
      {{
        "clause_type": "保密期限",
        "original_text": "保密期限为2年",
        "extracted_value": "2年",
        "policy_standard": "不超过5年",
        "judgment": "✅ 合规"
      }}
    ]
  }},
  "approval_flow": "executive_approval",
  "overall_risk_level": "high",
  "risk_clauses": [
    {{
      "original_text": "付款期限为交货后 360 天",
      "risk_level": "high",
      "risk_description": "付款期限超过公司政策规定的 30 天上限，违反公司财务管理制度",
      "suggestion": "建议将付款期限修改为 30 天以内",
      "legal_reference": "",
      "policy_reference": "《采购管理政策》第5条：付款周期不超过30天"
    }}
  ],
  "missing_clauses": [...],
  "suggestions": [...],
  "legal_references": [...],
  "policy_references": [...]
}}
"""
