"""
审查规则库生成器
使用 LLM 从法律法规中提取审查点
"""
from typing import List, Dict, Any
from app.services.llm.client import zhipu_llm
from app.services.rag.retriever import retriever


class RuleGenerator:
    """审查规则生成器"""

    def __init__(self):
        self.llm = zhipu_llm

    async def generate_nda_rules(self) -> List[Dict[str, Any]]:
        """
        生成 NDA 审查规则库

        基于《民法典》等相关法律法规自动生成 20+ 审查点
        """
        prompt = """你是一位专业律师，请根据以下法律法规生成 NDA（保密协议）审查规则库。

【相关法律法规】
1. 《民法典》第 470 条：合同的内容由当事人约定，一般包括下列条款：
   （一）当事人的姓名或者名称和住所；
   （二）标的；
   （三）数量；
   （四）质量；
   （五）价款或者报酬；
   （六）履行期限、地点和方式；
   （七）违约责任；
   （八）解决争议的方法。

2. 《民法典》第 509 条：当事人应当按照约定全面履行自己的义务。
   当事人应当遵循诚信原则，根据合同的性质、目的和交易习惯履行通知、协助、保密等义务。

3. 《民法典》第 577 条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。

4. 《民法典》第 584 条：当事人一方不履行合同义务或者履行合同义务不符合约定，造成对方损失的，损失赔偿额应当相当于因违约所造成的损失，包括合同履行后可以获得的利益。

5. 《民法典》第 585 条：当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。
   约定的违约金低于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以增加；约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。

6. 《反不正当竞争法》第 9 条：经营者不得实施下列侵犯商业秘密的行为：
   （一）以盗窃、贿赂、欺诈、胁迫、电子侵入或者其他不正当手段获取权利人的商业秘密；
   （二）披露、使用或者允许他人使用以前项手段获取的权利人的商业秘密；
   （三）违反保密义务或者违反权利人有关保守商业秘密的要求，披露、使用或者允许他人使用其所掌握的商业秘密；
   （四）教唆、引诱、帮助他人违反保密义务或者违反权利人有关保守商业秘密的要求，获取、披露、使用或者允许他人使用权利人的商业秘密。

【任务】
请生成 NDA 审查规则库，包含 20-25 个审查点。

【输出格式】
请以 JSON 数组格式输出，每个审查点包含以下字段：
- id: 规则 ID（格式 nda_001, nda_002...）
- name: 审查点名称
- category: 所属分类（必填：basic_info/confidential_info/term/obligation/liability/dispute/other）
- risk_type: 风险类型（missing_clause/risk_clause/incomplete_clause）
- legal_basis: 依据法条（包含法律名称和条款号）
- check_prompt: 检查提示（用于 LLM 判断该审查点）
- risk_level: 风险等级（high/medium/low）
- suggestion_template: 修改建议模板

【分类说明】
- basic_info: 基础信息（当事人、签署日期等）
- confidential_info: 保密信息相关（范围、定义、例外等）
- term: 期限相关（保密期限、生效日期等）
- obligation: 义务相关（保密义务、返还义务等）
- liability: 责任相关（违约责任、违约金等）
- dispute: 争议解决（管辖法院、适用法律等）
- other: 其他条款

示例输出：
[
  {
    "id": "nda_001",
    "name": "当事人信息是否完整",
    "category": "basic_info",
    "risk_type": "missing_clause",
    "legal_basis": "《民法典》第 470 条",
    "check_prompt": "检查合同是否明确记载了双方当事人的姓名/名称和住所",
    "risk_level": "medium",
    "suggestion_template": "建议补充完整的当事人信息，包括姓名/名称和住所"
  }
]
"""

        result = await self.llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        # 确保返回的是列表
        if isinstance(result, dict) and "rules" in result:
            return result["rules"]
        elif isinstance(result, list):
            return result
        else:
            raise ValueError("LLM 返回的数据格式不正确")

    async def generate_labor_contract_rules(self) -> List[Dict[str, Any]]:
        """
        生成劳动合同审查规则库

        基于《劳动合同法》等相关法律法规自动生成 20+ 审查点
        """
        prompt = """你是一位专业律师，请根据以下法律法规生成劳动合同审查规则库。

【相关法律法规】
1. 《劳动合同法》第 17 条：劳动合同应当具备以下条款：
   （一）用人单位的名称、住所和法定代表人或者主要负责人；
   （二）劳动者的姓名、住址和居民身份证或者其他有效身份证件号码；
   （三）劳动合同期限；
   （四）工作内容和工作地点；
   （五）工作时间和休息休假；
   （六）劳动报酬；
   （七）社会保险；
   （八）劳动保护、劳动条件和职业危害防护；
   （九）法律、法规规定应当纳入劳动合同的其他事项。

2. 《劳动合同法》第 19 条：劳动合同期限三个月以上不满一年的，试用期不得超过一个月；劳动合同期限一年以上不满三年的，试用期不得超过二个月；三年以上固定期限和无固定期限的劳动合同，试用期不得超过六个月。
   同一用人单位与同一劳动者只能约定一次试用期。
   以完成一定工作任务为期限的劳动合同或者劳动合同期限不满三个月的，不得约定试用期。
   试用期包含在劳动合同期限内。劳动合同仅约定试用期的，试用期不成立，该期限为劳动合同期限。

3. 《劳动合同法》第 20 条：劳动者在试用期的工资不得低于本单位相同岗位最低档工资或者劳动合同约定工资的百分之八十，并不得低于用人单位所在地的最低工资标准。

4. 《劳动合同法》第 23 条：用人单位与劳动者可以在劳动合同中约定保守用人单位的商业秘密和与知识产权相关的保密事项。
   对负有保密义务的劳动者，用人单位可以在劳动合同或者保密协议中与劳动者约定竞业限制条款，并约定在解除或者终止劳动合同后，在竞业限制期限内按月给予劳动者经济补偿。

5. 《劳动合同法》第 24 条：竞业限制的人员限于用人单位的高级管理人员、高级技术人员和其他负有保密义务的人员。竞业限制的范围、地域、期限由用人单位与劳动者约定，竞业限制的约定不得违反法律、法规的规定。
   在解除或者终止劳动合同后，前款规定的人员到与本单位生产或者经营同类产品、从事同类业务的有竞争关系的其他用人单位，或者自己开业生产或者经营同类产品、从事同类业务的竞业限制期限，不得超过二年。

6. 《劳动合同法》第 25 条：除本法第二十二条和第二十三条规定的情形外，用人单位不得与劳动者约定由劳动者承担违约金。

7. 《劳动合同法》第 31 条：用人单位应当严格执行劳动定额标准，不得强迫或者变相强迫劳动者加班。
   用人单位安排加班的，应当按照国家有关规定向劳动者支付加班费。

8. 《劳动法》第 36 条：国家实行劳动者每日工作时间不超过八小时、平均每周工作时间不超过四十四小时的工时制度。

9. 《劳动法》第 38 条：用人单位应当保证劳动者每周至少休息一日。

10. 《劳动法》第 44 条：有下列情形之一的，用人单位应当按照下列标准支付高于劳动者正常工作时间工资的工资报酬：
    （一）安排劳动者延长工作时间的，支付不低于工资的百分之一百五十的工资报酬；
    （二）休息日安排劳动者工作又不能安排补休的，支付不低于工资的百分之二百的工资报酬；
    （三）法定休假日安排劳动者工作的，支付不低于工资的百分之三百的工资报酬。

【任务】
请生成劳动合同审查规则库，包含 20-25 个审查点。

【输出格式】
请以 JSON 数组格式输出，每个审查点包含以下字段：
- id: 规则 ID（格式 labor_001, labor_002...）
- name: 审查点名称
- category: 所属分类（必填：basic_info/contract_term/work_content/work_time/salary/social_insurance/probation/non_compete/liability/other）
- risk_type: 风险类型（missing_clause/risk_clause/incomplete_clause）
- legal_basis: 依据法条（包含法律名称和条款号）
- check_prompt: 检查提示（用于 LLM 判断该审查点）
- risk_level: 风险等级（high/medium/low）
- suggestion_template: 修改建议模板

【分类说明】
- basic_info: 基础信息（用人单位信息、劳动者信息等）
- contract_term: 合同期限
- work_content: 工作内容和工作地点
- work_time: 工作时间和休息休假
- salary: 劳动报酬
- social_insurance: 社会保险
- probation: 试用期相关
- non_compete: 竞业限制
- liability: 违约责任
- other: 其他条款

示例输出：
[
  {
    "id": "labor_001",
    "name": "用人单位信息是否完整",
    "category": "basic_info",
    "risk_type": "missing_clause",
    "legal_basis": "《劳动合同法》第 17 条",
    "check_prompt": "检查合同是否明确记载了用人单位的名称、住所和法定代表人",
    "risk_level": "medium",
    "suggestion_template": "建议补充完整的用人单位信息"
  }
]
"""

        result = await self.llm.chat_with_json_output([
            {"role": "user", "content": prompt}
        ])

        # 确保返回的是列表
        if isinstance(result, dict) and "rules" in result:
            return result["rules"]
        elif isinstance(result, list):
            return result
        else:
            raise ValueError("LLM 返回的数据格式不正确")


# 全局生成器实例
rule_generator = RuleGenerator()
