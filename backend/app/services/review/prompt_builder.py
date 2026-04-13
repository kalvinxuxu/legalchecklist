"""
增强型 Prompt 构建器 - 支持法律依据和政策依据双分区
"""
from typing import Dict, List, Any, Optional


class EnhancedPromptBuilder:
    """增强型 Prompt 构建器"""

    @staticmethod
    def build_review_prompt(
        contract_text: str,
        contract_type: str,
        law_context: str,
        policy_context: str,
        rules: List[Dict[str, Any]]
    ) -> str:
        """
        构建审查 Prompt - 法律依据和政策依据分区展示

        Args:
            contract_text: 合同文本
            contract_type: 合同类型
            law_context: 法律依据上下文字符串
            policy_context: 公司政策上下文字符串
            rules: 审查规则列表
        """
        rules_text = ""
        if rules:
            rules_text = "\n\n## 审查规则参考\n"
            rules_text += "请根据以下审查规则进行检查：\n\n"
            for rule in rules[:10]:
                rules_text += f"- {rule['name']}（{rule['risk_type']}）：{rule['check_prompt']}\n"
            if len(rules) > 10:
                rules_text += f"... 等共 {len(rules)} 条规则"

        return f"""你是一位专业律师，请审查以下{contract_type}合同。

## 法律依据
{law_context}

## 公司政策（如有）
{policy_context}

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
   - legal_reference: 引用的法条（如《民法典》第153条）
   - policy_reference: **必须**引用的公司政策条款（如违反《采购管理政策》第5条）

2. **missing_clauses** (缺失条款数组):
   - title: 缺失的条款名称
   - description: 说明为何需要此条款
   - suggestion: 具体的修改/添加建议
   - legal_reference: 引用的法条（如有）
   - policy_reference: **必须**引用的公司政策条款（如有）

3. **suggestions** (综合修改建议数组):
   - title: 建议标题
   - content: 具体建议内容
   - reason: 建议理由

4. **legal_references** (引用的法律法规数组):
   - law_name: 法律名称
   - article: 条款号
   - content: 法条内容摘要

5. **policy_references** (引用的公司政策数组):
   - policy_name: 政策名称
   - section: 具体条款
   - content: 政策内容摘要

## 重要提示
- **公司政策优先级**：当合同条款与公司政策冲突时，**必须**在 policy_reference 中明确引用相关公司政策规定
- **综合建议**：suggestions 中的每条建议如果涉及公司政策，也应说明依据的政策条款
- **政策引用格式**：《政策名称》第X条：具体要求内容

输出 JSON 格式示例：
{{
  "risk_clauses": [
    {{
      "original_text": "付款期限为交货后 360 天",
      "risk_level": "high",
      "risk_description": "付款期限超过公司政策规定的 180 天上限，违反公司财务管理制度",
      "suggestion": "建议将付款期限修改为 180 天以内",
      "legal_reference": "",
      "policy_reference": "《采购管理政策》第5条：付款周期不超过180天"
    }}
  ],
  "missing_clauses": [
    {{
      "title": "知识产权归属条款",
      "description": "合同未明确约定技术成果的知识产权归属",
      "suggestion": "建议添加条款明确知识产权归属",
      "legal_reference": "《民法典》第八百二十三条",
      "policy_reference": "《知识产权管理办法》第七条：技术成果归属按贡献比例分配"
    }}
  ],
  "suggestions": [...],
  "legal_references": [
    {{"law_name": "民法典", "article": "第153条", "content": "..."}}
  ],
  "policy_references": [
    {{"policy_name": "采购管理政策", "section": "第5条", "content": "付款周期不超过180天"}},
    {{"policy_name": "知识产权管理办法", "section": "第7条", "content": "技术成果归属按贡献比例分配"}}
  ]
}}
"""
