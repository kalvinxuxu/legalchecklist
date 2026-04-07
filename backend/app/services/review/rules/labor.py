"""
劳动合同审查规则库
使用 LLM 生成 + 人工审核
"""

LABOR_CONTRACT_REVIEW_RULES = [
    {
        "id": "labor_001",
        "name": "用人单位信息是否完整",
        "category": "basic_info",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确记载了用人单位的名称、住所和法定代表人",
        "risk_level": "medium",
        "suggestion_template": "建议补充完整的用人单位信息，包括名称、住所和法定代表人"
    },
    {
        "id": "labor_002",
        "name": "劳动者信息是否完整",
        "category": "basic_info",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确记载了劳动者的姓名、住址和身份证件号码",
        "risk_level": "medium",
        "suggestion_template": "建议补充完整的劳动者信息，包括姓名、住址和身份证件号码"
    },
    {
        "id": "labor_003",
        "name": "劳动合同期限是否明确",
        "category": "contract_term",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确了劳动合同期限（固定期限/无固定期限/以完成一定工作任务为期限）",
        "risk_level": "high",
        "suggestion_template": "建议明确劳动合同期限类型和具体时间"
    },
    {
        "id": "labor_004",
        "name": "工作内容是否明确",
        "category": "work_content",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确了工作内容和工作岗位",
        "risk_level": "high",
        "suggestion_template": "建议明确工作内容和工作岗位"
    },
    {
        "id": "labor_005",
        "name": "工作地点是否明确",
        "category": "work_content",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确了工作地点",
        "risk_level": "medium",
        "suggestion_template": "建议明确工作地点，如约定多个工作地点应列明"
    },
    {
        "id": "labor_006",
        "name": "工作时间制度是否明确",
        "category": "work_time",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确了工作时间制度（标准工时制/综合计算工时制/不定时工时制）",
        "risk_level": "high",
        "suggestion_template": "建议明确工作时间制度"
    },
    {
        "id": "labor_007",
        "name": "休息休假条款是否完备",
        "category": "work_time",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否规定了休息休假条款",
        "risk_level": "medium",
        "suggestion_template": "建议补充休息休假条款，包括周休日、法定节假日、年休假等"
    },
    {
        "id": "labor_008",
        "name": "劳动报酬是否明确",
        "category": "salary",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否明确了劳动报酬的具体数额和支付方式",
        "risk_level": "high",
        "suggestion_template": "建议明确劳动报酬的具体数额、支付时间和支付方式"
    },
    {
        "id": "labor_009",
        "name": "试用期工资是否合法",
        "category": "probation",
        "risk_type": "risk_clause",
        "legal_basis": "《劳动合同法》第 20 条",
        "check_prompt": "检查试用期工资是否不低于约定工资的 80% 且不低于当地最低工资标准",
        "risk_level": "high",
        "suggestion_template": "试用期工资不得低于约定工资的 80% 且不低于当地最低工资标准"
    },
    {
        "id": "labor_010",
        "name": "试用期期限是否合法",
        "category": "probation",
        "risk_type": "risk_clause",
        "legal_basis": "《劳动合同法》第 19 条",
        "check_prompt": "检查试用期期限是否符合法律规定（合同期 3 月 -1 年≤1 月；1 年 -3 年≤2 月；3 年以上≤6 月）",
        "risk_level": "high",
        "suggestion_template": "建议将试用期期限调整为符合劳动合同法规定的范围"
    },
    {
        "id": "labor_011",
        "name": "社会保险条款是否完备",
        "category": "social_insurance",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否规定了社会保险条款",
        "risk_level": "high",
        "suggestion_template": "建议补充社会保险条款，明确用人单位依法为劳动者缴纳社会保险"
    },
    {
        "id": "labor_012",
        "name": "劳动保护条款是否完备",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 17 条",
        "check_prompt": "检查合同是否规定了劳动保护、劳动条件和职业危害防护条款",
        "risk_level": "medium",
        "suggestion_template": "建议补充劳动保护、劳动条件和职业危害防护条款"
    },
    {
        "id": "labor_013",
        "name": "竞业限制条款是否合法",
        "category": "non_compete",
        "risk_type": "risk_clause",
        "legal_basis": "《劳动合同法》第 23-24 条",
        "check_prompt": "检查竞业限制条款是否符合法律规定（人员范围、期限≤2 年、经济补偿）",
        "risk_level": "high",
        "suggestion_template": "竞业限制仅适用于高管、高技等负有保密义务的人员，期限不得超过 2 年，并应约定经济补偿"
    },
    {
        "id": "labor_014",
        "name": "竞业限制经济补偿是否明确",
        "category": "non_compete",
        "risk_type": "incomplete_clause",
        "legal_basis": "《劳动合同法》第 23 条",
        "check_prompt": "检查竞业限制条款是否约定了经济补偿的具体数额和支付方式",
        "risk_level": "medium",
        "suggestion_template": "建议明确竞业限制经济补偿的具体数额和支付方式"
    },
    {
        "id": "labor_015",
        "name": "违约金条款是否合法",
        "category": "liability",
        "risk_type": "risk_clause",
        "legal_basis": "《劳动合同法》第 25 条",
        "check_prompt": "检查违约金条款是否仅限于服务期和竞业限制两种情形",
        "risk_level": "high",
        "suggestion_template": "除服务期和竞业限制外，用人单位不得与劳动者约定由劳动者承担违约金"
    },
    {
        "id": "labor_016",
        "name": "服务期约定是否合法",
        "category": "other",
        "risk_type": "risk_clause",
        "legal_basis": "《劳动合同法》第 22 条",
        "check_prompt": "检查服务期约定是否基于用人单位提供专项培训费用进行专业技术培训",
        "risk_level": "medium",
        "suggestion_template": "服务期约定应基于用人单位提供专项培训费用进行专业技术培训"
    },
    {
        "id": "labor_017",
        "name": "加班费约定是否明确",
        "category": "salary",
        "risk_type": "incomplete_clause",
        "legal_basis": "《劳动法》第 44 条",
        "check_prompt": "检查合同是否明确了加班费的计算基数和支付标准",
        "risk_level": "medium",
        "suggestion_template": "建议明确加班费的计算基数和支付标准"
    },
    {
        "id": "labor_018",
        "name": "劳动合同解除条件是否明确",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》相关规定",
        "check_prompt": "检查合同是否明确了劳动合同解除的条件和程序",
        "risk_level": "medium",
        "suggestion_template": "建议明确劳动合同解除的条件和程序"
    },
    {
        "id": "labor_019",
        "name": "经济补偿条款是否完备",
        "category": "other",
        "risk_type": "incomplete_clause",
        "legal_basis": "《劳动合同法》第 46-47 条",
        "check_prompt": "检查合同是否规定了经济补偿的相关条款",
        "risk_level": "medium",
        "suggestion_template": "建议补充经济补偿条款，明确补偿标准和支付条件"
    },
    {
        "id": "labor_020",
        "name": "争议解决方式是否明确",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动争议调解仲裁法》",
        "check_prompt": "检查合同是否约定了劳动争议解决方式",
        "risk_level": "low",
        "suggestion_template": "建议明确劳动争议解决方式，包括协商、调解、仲裁、诉讼等"
    },
    {
        "id": "labor_021",
        "name": "规章制度告知确认",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 4 条",
        "check_prompt": "检查合同是否有劳动者确认已知悉用人单位规章制度的条款",
        "risk_level": "low",
        "suggestion_template": "建议添加劳动者确认已知悉用人单位规章制度的条款"
    },
    {
        "id": "labor_022",
        "name": "合同变更条款是否完备",
        "category": "other",
        "risk_type": "missing_clause",
        "legal_basis": "《劳动合同法》第 35 条",
        "check_prompt": "检查合同是否约定了合同变更的方式",
        "risk_level": "low",
        "suggestion_template": "建议明确合同变更需采用书面形式"
    }
]
