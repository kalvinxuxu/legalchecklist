/**
 * 预制示例数据 - 用于 Demo 页面展示
 * 包含三种常见合同类型的示例审查结果
 */

export interface DemoRiskClause {
  title: string
  original_text: string
  risk_description: string
  risk_level: 'high' | 'medium' | 'low'
  suggestion?: string
}

export interface DemoMissingClause {
  title: string
  description: string
  suggestion: string
}

export interface DemoQuickCards {
  contract_purpose?: string
  key_dates?: string[]
  payment_summary?: string
  breach_summary?: string
  core_obligations?: string[]
}

export interface DemoSample {
  id: string
  file_name: string
  contract_type: string
  risk_level: 'high' | 'medium' | 'low'
  confidence_score: number
  risk_clauses: DemoRiskClause[]
  missing_clauses: DemoMissingClause[]
  quick_cards: DemoQuickCards
}

export const demoSamples: DemoSample[] = [
  // ===== 示例 1: NDA（保密协议）=====
  {
    id: 'demo-nda',
    file_name: '软件开发保密协议.pdf',
    contract_type: 'NDA',
    risk_level: 'medium',
    confidence_score: 0.94,
    risk_clauses: [
      {
        title: '保密期限条款不明确',
        original_text: '协议双方应在合作期间及合作结束后三年内对对方商业秘密进行保密。',
        risk_description: '保密期限的起算点模糊，"合作结束后"可能产生争议。',
        risk_level: 'medium',
        suggestion: '明确保密期限的起算点和终止条件。',
      },
      {
        title: '违约赔偿条款过重',
        original_text: '任何一方违反本协议，应向对方支付人民币500万元作为违约金。',
        risk_description: '固定违约金金额过高，可能因显失公平而被法院调整。',
        risk_level: 'high',
        suggestion: '建议改为实际损失赔偿或设定赔偿上限。',
      },
      {
        title: '保密信息定义过宽',
        original_text: '本协议所称保密信息包括但不限于：技术资料、商业计划、客户名单、财务信息等。',
        risk_description: '定义未排除公知信息，可能导致义务范围不当扩大。',
        risk_level: 'low',
        suggestion: '增加"公知信息"例外条款。',
      },
    ],
    missing_clauses: [
      {
        title: '竞业限制条款',
        description: '缺少对离职后竞业限制的规定。',
        suggestion: '如需保护商业利益，建议增加竞业限制条款。',
      },
    ],
    quick_cards: {
      contract_purpose: '规范软件开发过程中的保密义务，保护双方商业秘密和技术信息。',
      payment_summary: '本协议不涉及费用支付，属于无偿保密约定。',
      breach_summary: '违约方需支付固定违约金500万元。',
      core_obligations: [
        '甲方：提供技术资料、履行保密义务',
        '乙方：使用保密信息、不得泄露第三方',
      ],
    },
  },

  // ===== 示例 2: 劳动合同 =====
  {
    id: 'demo-labor',
    file_name: '标准劳动合同.pdf',
    contract_type: '劳动合同',
    risk_level: 'high',
    confidence_score: 0.91,
    risk_clauses: [
      {
        title: '试用期工资低于法定标准',
        original_text: '乙方试用期工资为每月3000元，不低于当地最低工资标准的70%。',
        risk_description: '试用期工资低于法定标准（当地最低工资80%），存在违法风险。',
        risk_level: 'high',
        suggestion: '将试用期工资调整为不低于当地最低工资标准的80%。',
      },
      {
        title: '加班条款约定模糊',
        original_text: '乙方同意根据甲方生产经营需要加班，甲方依法支付加班费或安排调休。',
        risk_description: '"依法支付"表述模糊，未明确加班费计算基数和标准。',
        risk_level: 'medium',
        suggestion: '明确加班费计算基数（通常为劳动合同约定工资）。',
      },
      {
        title: '单方解除权条款过宽',
        original_text: '甲方有权因生产经营需要调整乙方工作岗位，乙方同意服从安排。',
        risk_description: '该条款赋予用人单位过大的单方调岗权，可能被认定为无效。',
        risk_level: 'high',
        suggestion: '增加"合理性"限制，确需调整时应协商一致。',
      },
      {
        title: '竞业限制补偿金缺失',
        original_text: '乙方离职后两年内不得从事与甲方有竞争关系的业务。',
        risk_description: '约定竞业限制但未约定补偿金，该条款可能被认定为无效。',
        risk_level: 'high',
        suggestion: '增加竞业限制补偿金条款（通常为离职前12个月平均工资的30%）。',
      },
    ],
    missing_clauses: [
      {
        title: '社会保险缴纳条款',
        description: '合同未明确约定社会保险缴纳方式和基数。',
        suggestion: '依法为员工缴纳社会保险是用人单位的法定义务。',
      },
    ],
    quick_cards: {
      contract_purpose: '建立劳动关系，明确双方权利义务。',
      payment_summary: '月工资8000元，每月10日发放；试用期工资3000元。',
      breach_summary: '违约方需赔偿对方实际损失。',
      core_obligations: [
        '甲方：支付劳动报酬、缴纳社保、提供劳动条件',
        '乙方：服从管理、遵守制度、完成工作任务',
      ],
    },
  },

  // ===== 示例 3: 采购合同 =====
  {
    id: 'demo-purchase',
    file_name: '设备采购合同.pdf',
    contract_type: '采购合同',
    risk_level: 'low',
    confidence_score: 0.97,
    risk_clauses: [
      {
        title: '质量标准约定不具体',
        original_text: '乙方提供的设备应符合国家相关质量标准。',
        risk_description: '仅笼统提及"国家相关标准"，未明确具体执行标准编号。',
        risk_level: 'low',
        suggestion: '列明具体的国家标准编号（如GB/T 19001）。',
      },
      {
        title: '验收条款缺少异议期',
        original_text: '甲方应在收到设备后5个工作日内完成验收。',
        risk_description: '5个工作日验收期较短，大型设备可能来不及全面检测。',
        risk_level: 'medium',
        suggestion: '建议将验收期延长至10-15个工作日。',
      },
    ],
    missing_clauses: [
      {
        title: '知识产权侵权条款',
        description: '缺少设备侵权责任承担条款。',
        suggestion: '增加第三方侵权时的责任承担和赔偿机制。',
      },
    ],
    quick_cards: {
      contract_purpose: '采购办公设备，明确设备规格、交货期限和付款方式。',
      payment_summary: '合同总价15万元，预付30%，交货验收后付70%。',
      breach_summary: '逾期交货每日按合同总价0.5%支付违约金。',
      core_obligations: [
        '甲方：按时付款、配合验收',
        '乙方：按时交货、保证质量',
      ],
    },
  },
]
