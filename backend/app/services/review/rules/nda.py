"""
NDA 审查规则库
使用 LLM 生成 + 人工审核
"""

# NDA 审查规则库
# 每个规则包含：id, name, category, risk_type, legal_basis, check_prompt, risk_level, suggestion_template

NDA_REVIEW_RULES = [
    {
        "id": "nda_001",
        "name": "当事人信息是否完整",
        "category": "basic_info",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 470 条",
        "check_prompt": "检查合同是否明确记载了双方当事人的姓名/名称和住所",
        "risk_level": "medium",
        "suggestion_template": "建议补充完整的当事人信息，包括姓名/名称和住所"
    },
    {
        "id": "nda_002",
        "name": "保密信息范围定义是否清晰",
        "category": "confidential_info",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 470 条",
        "check_prompt": "检查合同是否明确定义了保密信息的具体范围和内容",
        "risk_level": "high",
        "suggestion_template": "建议明确保密信息的具体范围，可列举保密信息的类型或提供判断标准"
    },
    {
        "id": "nda_003",
        "name": "保密信息例外情况是否明确",
        "category": "confidential_info",
        "risk_type": "missing_clause",
        "legal_basis": "行业惯例",
        "check_prompt": "检查合同是否规定了保密信息的例外情况（如公开信息、独立开发等）",
        "risk_level": "medium",
        "suggestion_template": "建议补充保密信息的例外情形，如：已公开信息、接收方独立开发的信息、从第三方合法获得的信息等"
    },
    {
        "id": "nda_004",
        "name": "保密期限是否合理",
        "category": "term",
        "risk_type": "risk_clause",
        "legal_basis": "《民法典》相关规定",
        "check_prompt": "检查保密期限是否过长（如永久保密）或过短，一般建议 2-5 年",
        "risk_level": "medium",
        "suggestion_template": "建议将保密期限调整为 2-5 年，永久保密可能因不合理而不被支持"
    },
    {
        "id": "nda_005",
        "name": "保密义务是否明确",
        "category": "obligation",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 509 条",
        "check_prompt": "检查合同是否明确规定了保密义务的具体内容",
        "risk_level": "high",
        "suggestion_template": "建议明确保密义务的具体内容，包括不得泄露、不得使用、限制访问范围等"
    },
    {
        "id": "nda_006",
        "name": "返还或销毁条款是否完备",
        "category": "obligation",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 558 条",
        "check_prompt": "检查合同是否规定了合同终止后保密材料的返还或销毁义务",
        "risk_level": "medium",
        "suggestion_template": "建议补充合同终止后保密材料的返还或销毁条款"
    },
    {
        "id": "nda_007",
        "name": "违约责任是否明确",
        "category": "liability",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 577 条",
        "check_prompt": "检查合同是否明确规定了违约责任",
        "risk_level": "high",
        "suggestion_template": "建议明确违约责任，包括赔偿范围、计算方式等"
    },
    {
        "id": "nda_008",
        "name": "违约金是否过高或过低",
        "category": "liability",
        "risk_type": "risk_clause",
        "legal_basis": "《民法典》第 585 条",
        "check_prompt": "检查约定的违约金是否过分高于或低于实际损失",
        "risk_level": "medium",
        "suggestion_template": "建议将违约金调整为与实际损失相当的水平，过高可能被法院调减"
    },
    {
        "id": "nda_009",
        "name": "损失赔偿范围是否明确",
        "category": "liability",
        "risk_type": "incomplete_clause",
        "legal_basis": "《民法典》第 584 条",
        "check_prompt": "检查损失赔偿范围是否包括直接损失和可得利益损失",
        "risk_level": "medium",
        "suggestion_template": "建议明确损失赔偿范围包括直接损失和可得利益损失"
    },
    {
        "id": "nda_010",
        "name": "争议解决方式是否明确",
        "category": "dispute",
        "risk_type": "missing_clause",
        "legal_basis": "《民事诉讼法》",
        "check_prompt": "检查合同是否约定了争议解决方式（诉讼或仲裁）",
        "risk_level": "medium",
        "suggestion_template": "建议明确争议解决方式，如约定管辖法院或仲裁机构"
    },
    {
        "id": "nda_011",
        "name": "管辖法院约定是否有效",
        "category": "dispute",
        "risk_type": "risk_clause",
        "legal_basis": "《民事诉讼法》第 35 条",
        "check_prompt": "检查管辖法院约定是否符合法律规定（被告住所地、合同履行地、合同签订地、原告住所地、标的物所在地）",
        "risk_level": "low",
        "suggestion_template": "建议将管辖法院约定为与合同有实际联系的地点的法院"
    },
    {
        "id": "nda_012",
        "name": "商业秘密定义是否符合反不正当竞争法",
        "category": "confidential_info",
        "risk_type": "incomplete_clause",
        "legal_basis": "《反不正当竞争法》第 9 条",
        "check_prompt": "检查商业秘密定义是否符合反不正当竞争法规定的三要件（秘密性、价值性、保密措施）",
        "risk_level": "high",
        "suggestion_template": "建议按照反不正当竞争法的规定完善商业秘密的定义"
    },
    {
        "id": "nda_013",
        "name": "知识产权归属是否明确",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《著作权法》相关规定",
        "check_prompt": "检查合同是否明确了基于保密信息产生的知识产权归属",
        "risk_level": "medium",
        "suggestion_template": "建议明确基于保密信息产生的知识产权归属"
    },
    {
        "id": "nda_014",
        "name": "合同生效条件是否明确",
        "category": "basic_info",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 502 条",
        "check_prompt": "检查合同是否明确了生效条件（签字、盖章等）",
        "risk_level": "low",
        "suggestion_template": "建议明确合同生效条件"
    },
    {
        "id": "nda_015",
        "name": "合同期限是否明确",
        "category": "term",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 470 条",
        "check_prompt": "检查合同是否明确了合同期限",
        "risk_level": "medium",
        "suggestion_template": "建议明确合同期限"
    },
    {
        "id": "nda_016",
        "name": "单方解除权是否明确",
        "category": "other",
        "risk_type": "incomplete_clause",
        "legal_basis": "《民法典》第 563 条",
        "check_prompt": "检查合同是否约定了单方解除权的条件和程序",
        "risk_level": "low",
        "suggestion_template": "建议明确单方解除权的条件和程序"
    },
    {
        "id": "nda_017",
        "name": "通知送达方式是否明确",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》相关规定",
        "check_prompt": "检查合同是否约定了通知送达方式",
        "risk_level": "low",
        "suggestion_template": "建议明确通知送达方式，如书面通知、电子邮件等"
    },
    {
        "id": "nda_018",
        "name": "保密信息载体管理是否规范",
        "category": "obligation",
        "risk_type": "incomplete_clause",
        "legal_basis": "行业惯例",
        "check_prompt": "检查合同是否规定了保密信息载体的管理要求",
        "risk_level": "low",
        "suggestion_template": "建议补充保密信息载体的管理要求"
    },
    {
        "id": "nda_019",
        "name": "第三方披露限制是否明确",
        "category": "obligation",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 509 条",
        "check_prompt": "检查合同是否限制了向第三方披露保密信息",
        "risk_level": "high",
        "suggestion_template": "建议明确限制向第三方披露保密信息，确需披露的应事先获得书面同意"
    },
    {
        "id": "nda_020",
        "name": "合同变更方式是否明确",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 543 条",
        "check_prompt": "检查合同是否约定了合同变更的方式",
        "risk_level": "low",
        "suggestion_template": "建议明确合同变更需采用书面形式"
    },
    {
        "id": "nda_021",
        "name": "完整性条款是否存在",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "行业惯例",
        "check_prompt": "检查合同是否有完整性条款（取代先前所有约定）",
        "risk_level": "low",
        "suggestion_template": "建议添加完整性条款"
    },
    {
        "id": "nda_022",
        "name": "可分割性条款是否存在",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "行业惯例",
        "check_prompt": "检查合同是否有可分割性条款（部分无效不影响其他部分）",
        "risk_level": "low",
        "suggestion_template": "建议添加可分割性条款"
    }
]
