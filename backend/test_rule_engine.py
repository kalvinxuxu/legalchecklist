"""
测试规则判定功能
直接调用审查服务，测试新的规则判定输出
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.review.service import review_service


async def test_rule_judgment():
    """测试规则判定功能"""

    # 测试合同文本 - 包含违反政策的条款
    test_contract = """
    联合体协议书

    第一条 联合体组成
    甲乙双方自愿组成联合体，共同参与项目投标。

    第二条 付款周期
    付款期限为交货后360天。

    第三条 违约金
    任何一方违约，应向守约方支付合同总金额的30%作为违约金。

    第四条 保密期限
    本协议保密期限为永久保密。

    第五条 合同金额
    本合同总金额为人民币500万元。

    第六条 违约责任
    若一方违约，除支付违约金外，还应赔偿对方因此遭受的全部损失。
    """

    print("=" * 60)
    print("测试合同审查 - 规则判定功能")
    print("=" * 60)
    print("\n合同内容摘要:")
    print("- 付款周期: 360天 (政策上限30天) [VIOLATION]")
    print("- 违约金比例: 30% (审批阈值20%) [APPROVAL]")
    print("- 保密期限: 永久 (建议<=5年) [APPROVAL]")
    print("- 合同金额: 500万元")
    print()

    print("正在调用审查服务...")
    try:
        result = await review_service.review_contract(
            contract_text=test_contract,
            contract_type="NDA",
            tenant_id=None
        )

        print("\n" + "=" * 60)
        print("审查结果")
        print("=" * 60)

        # 规则判定结果
        print("\n[规则判定]")
        if "rule_judgments" in result:
            rj = result["rule_judgments"]

            violations = rj.get("violations", [])
            approvals = rj.get("approvals_needed", [])
            compliant = rj.get("compliant", [])

            print(f"\n[VIOLATIONS] 违反政策 ({len(violations)} 项):")
            for v in violations:
                print(f"   - {v.get('clause_type')}: {v.get('judgment', '')[:50]}...")

            print(f"\n[APPROVALS] 需要审批 ({len(approvals)} 项):")
            for a in approvals:
                print(f"   - {a.get('clause_type')}: {a.get('judgment', '')[:50]}...")

            print(f"\n[COMPLIANT] 合规 ({len(compliant)} 项):")
            for c in compliant:
                print(f"   - {c.get('clause_type')}: {c.get('judgment', '')[:50]}...")

        print("\n[审批流程]")
        print(f"审批建议: {result.get('approval_flow_description', 'N/A')}")
        print(f"风险等级: {result.get('overall_risk_level', 'N/A')}")

        # 风险条款
        risk_clauses = result.get("risk_clauses", [])
        print(f"\n[风险条款] 共 {len(risk_clauses)} 条")
        for i, clause in enumerate(risk_clauses[:3], 1):
            print(f"  {i}. [{clause.get('risk_level', 'medium')}] {clause.get('title', '')[:40]}")
            if clause.get('policy_reference'):
                print(f"     政策引用: {clause.get('policy_reference', '')[:50]}...")

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_rule_judgment())
