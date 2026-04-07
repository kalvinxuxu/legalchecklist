"""
初始化法律知识库脚本
将 NDA 和劳动合同审查规则以及相关法律法条存入数据库
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import db
from app.services.rag.retriever import retriever
from app.services.review.rules.nda import NDA_REVIEW_RULES
from app.services.review.rules.labor import LABOR_CONTRACT_REVIEW_RULES


# 基础法律知识库内容
LEGAL_KNOWLEDGE_BASE = [
    # 民法典相关
    {
        "title": "《民法典》第 470 条 - 合同内容",
        "content": "合同的内容由当事人约定，一般包括下列条款：（一）当事人的姓名或者名称和住所；（二）标的；（三）数量；（四）质量；（五）价款或者报酬；（六）履行期限、地点和方式；（七）违约责任；（八）解决争议的方法。当事人可以参照各类合同的示范文本订立合同。",
        "content_type": "law",
        "metadata": {"law": "民法典", "article": "470"}
    },
    {
        "title": "《民法典》第 509 条 - 合同履行原则",
        "content": "当事人应当按照约定全面履行自己的义务。当事人应当遵循诚信原则，根据合同的性质、目的和交易习惯履行通知、协助、保密等义务。",
        "content_type": "law",
        "metadata": {"law": "民法典", "article": "509"}
    },
    {
        "title": "《民法典》第 577 条 - 违约责任",
        "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
        "content_type": "law",
        "metadata": {"law": "民法典", "article": "577"}
    },
    {
        "title": "《民法典》第 584 条 - 损失赔偿范围",
        "content": "当事人一方不履行合同义务或者履行合同义务不符合约定，造成对方损失的，损失赔偿额应当相当于因违约所造成的损失，包括合同履行后可以获得的利益；但是，不得超过违约一方订立合同时预见到或者应当预见到的因违约可能造成的损失。",
        "content_type": "law",
        "metadata": {"law": "民法典", "article": "584"}
    },
    {
        "title": "《民法典》第 585 条 - 违约金",
        "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。约定的违约金低于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以增加；约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。",
        "content_type": "law",
        "metadata": {"law": "民法典", "article": "585"}
    },
    {
        "title": "《反不正当竞争法》第 9 条 - 商业秘密",
        "content": "经营者不得实施下列侵犯商业秘密的行为：（一）以盗窃、贿赂、欺诈、胁迫、电子侵入或者其他不正当手段获取权利人的商业秘密；（二）披露、使用或者允许他人使用以前项手段获取的权利人的商业秘密；（三）违反保密义务或者违反权利人有关保守商业秘密的要求，披露、使用或者允许他人使用其所掌握的商业秘密；（四）教唆、引诱、帮助他人违反保密义务或者违反权利人有关保守商业秘密的要求，获取、披露、使用或者允许他人使用权利人的商业秘密。",
        "content_type": "law",
        "metadata": {"law": "反不正当竞争法", "article": "9"}
    },
    # 劳动合同法相关
    {
        "title": "《劳动合同法》第 17 条 - 劳动合同必备条款",
        "content": "劳动合同应当具备以下条款：（一）用人单位的名称、住所和法定代表人或者主要负责人；（二）劳动者的姓名、住址和居民身份证或者其他有效身份证件号码；（三）劳动合同期限；（四）工作内容和工作地点；（五）工作时间和休息休假；（六）劳动报酬；（七）社会保险；（八）劳动保护、劳动条件和职业危害防护；（九）法律、法规规定应当纳入劳动合同的其他事项。",
        "content_type": "law",
        "metadata": {"law": "劳动合同法", "article": "17"}
    },
    {
        "title": "《劳动合同法》第 19 条 - 试用期规定",
        "content": "劳动合同期限三个月以上不满一年的，试用期不得超过一个月；劳动合同期限一年以上不满三年的，试用期不得超过二个月；三年以上固定期限和无固定期限的劳动合同，试用期不得超过六个月。同一用人单位与同一劳动者只能约定一次试用期。以完成一定工作任务为期限的劳动合同或者劳动合同期限不满三个月的，不得约定试用期。试用期包含在劳动合同期限内。劳动合同仅约定试用期的，试用期不成立，该期限为劳动合同期限。",
        "content_type": "law",
        "metadata": {"law": "劳动合同法", "article": "19"}
    },
    {
        "title": "《劳动合同法》第 20 条 - 试用期工资",
        "content": "劳动者在试用期的工资不得低于本单位相同岗位最低档工资或者劳动合同约定工资的百分之八十，并不得低于用人单位所在地的最低工资标准。",
        "content_type": "law",
        "metadata": {"law": "劳动合同法", "article": "20"}
    },
    {
        "title": "《劳动合同法》第 23 条 - 保密义务和竞业限制",
        "content": "用人单位与劳动者可以在劳动合同中约定保守用人单位的商业秘密和与知识产权相关的保密事项。对负有保密义务的劳动者，用人单位可以在劳动合同或者保密协议中与劳动者约定竞业限制条款，并约定在解除或者终止劳动合同后，在竞业限制期限内按月给予劳动者经济补偿。劳动者违反竞业限制约定的，应当按照约定向用人单位支付违约金。",
        "content_type": "law",
        "metadata": {"law": "劳动合同法", "article": "23"}
    },
    {
        "title": "《劳动合同法》第 24 条 - 竞业限制范围和期限",
        "content": "竞业限制的人员限于用人单位的高级管理人员、高级技术人员和其他负有保密义务的人员。竞业限制的范围、地域、期限由用人单位与劳动者约定，竞业限制的约定不得违反法律、法规的规定。在解除或者终止劳动合同后，前款规定的人员到与本单位生产或者经营同类产品、从事同类业务的有竞争关系的其他用人单位，或者自己开业生产或者经营同类产品、从事同类业务的竞业限制期限，不得超过二年。",
        "content_type": "law",
        "metadata": {"law": "劳动合同法", "article": "24"}
    },
    {
        "title": "《劳动合同法》第 25 条 - 违约金限制",
        "content": "除本法第二十二条和第二十三条规定的情形外，用人单位不得与劳动者约定由劳动者承担违约金。",
        "content_type": "law",
        "metadata": {"law": "劳动合同法", "article": "25"}
    },
    # 劳动法相关
    {
        "title": "《劳动法》第 36 条 - 工作时间",
        "content": "国家实行劳动者每日工作时间不超过八小时、平均每周工作时间不超过四十四小时的工时制度。",
        "content_type": "law",
        "metadata": {"law": "劳动法", "article": "36"}
    },
    {
        "title": "《劳动法》第 38 条 - 休息保障",
        "content": "用人单位应当保证劳动者每周至少休息一日。",
        "content_type": "law",
        "metadata": {"law": "劳动法", "article": "38"}
    },
    {
        "title": "《劳动法》第 44 条 - 加班费",
        "content": "有下列情形之一的，用人单位应当按照下列标准支付高于劳动者正常工作时间工资的工资报酬：（一）安排劳动者延长工作时间的，支付不低于工资的百分之一百五十的工资报酬；（二）休息日安排劳动者工作又不能安排补休的，支付不低于工资的百分之二百的工资报酬；（三）法定休假日安排劳动者工作的，支付不低于工资的百分之三百的工资报酬。",
        "content_type": "law",
        "metadata": {"law": "劳动法", "article": "44"}
    }
]


async def init_legal_knowledge():
    """初始化法律知识库"""
    print("开始初始化法律知识库...")

    # 1. 添加基础法律法条
    print("\n1. 添加基础法律法条...")
    knowledge_list = []
    for item in LEGAL_KNOWLEDGE_BASE:
        knowledge_list.append({
            "title": item["title"],
            "content": item["content"],
            "content_type": item["content_type"],
            "metadata": item["metadata"]
        })

    ids = await retriever.batch_add_knowledge(knowledge_list)
    print(f"   已添加 {len(ids)} 条法律法条")

    # 2. 添加 NDA 审查规则
    print("\n2. 添加 NDA 审查规则...")
    nda_knowledge = []
    for rule in NDA_REVIEW_RULES:
        nda_knowledge.append({
            "title": f"NDA 审查：{rule['name']}",
            "content": f"审查要点：{rule['check_prompt']}\n风险类型：{rule['risk_type']}\n风险等级：{rule['risk_level']}\n建议：{rule['suggestion_template']}",
            "content_type": "rule",
            "metadata": {
                "rule_id": rule["id"],
                "category": rule["category"],
                "legal_basis": rule["legal_basis"]
            }
        })

    ids = await retriever.batch_add_knowledge(nda_knowledge)
    print(f"   已添加 {len(ids)} 条 NDA 审查规则")

    # 3. 添加劳动合同审查规则
    print("\n3. 添加劳动合同审查规则...")
    labor_knowledge = []
    for rule in LABOR_CONTRACT_REVIEW_RULES:
        labor_knowledge.append({
            "title": f"劳动合同审查：{rule['name']}",
            "content": f"审查要点：{rule['check_prompt']}\n风险类型：{rule['risk_type']}\n风险等级：{rule['risk_level']}\n建议：{rule['suggestion_template']}",
            "content_type": "rule",
            "metadata": {
                "rule_id": rule["id"],
                "category": rule["category"],
                "legal_basis": rule["legal_basis"]
            }
        })

    ids = await retriever.batch_add_knowledge(labor_knowledge)
    print(f"   已添加 {len(ids)} 条劳动合同审查规则")

    print("\n法律知识库初始化完成！")
    print(f"总计添加：{len(knowledge_list) + len(nda_knowledge) + len(labor_knowledge)} 条知识")


if __name__ == "__main__":
    async def main():
        # 初始化数据库连接
        db.connect()
        await db.create_all_tables()

        # 运行初始化
        await init_legal_knowledge()

        # 关闭数据库连接
        await db.disconnect()

    asyncio.run(main())
