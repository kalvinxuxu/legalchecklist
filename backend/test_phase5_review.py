"""
Phase 5 合同审查功能端到端测试
测试审查服务是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.review.service import review_service
from app.services.llm.client import zhipu_llm
from app.db.session import db as database


async def test_llm_connection():
    """测试 LLM 连接"""
    print("=" * 50)
    print("Test 1: LLM Connection Test")
    print("=" * 50)

    try:
        messages = [{"role": "user", "content": "Hello, introduce yourself in one sentence"}]
        response = await zhipu_llm.chat(messages)
        print(f"[PASS] LLM connection successful: {response[:50]}...")
        return True
    except Exception as e:
        print(f"[FAIL] LLM connection failed: {e}")
        return False


async def test_review_service():
    """测试审查服务"""
    print("\n" + "=" * 50)
    print("Test 2: NDA Contract Review")
    print("=" * 50)

    # 简单的 NDA 合同样本（有缺陷的版本）
    nda_contract = """
Confidentiality Agreement

Party A: Zhang San
Party B: Li Si

1. Confidential Information
Party B agrees to keep Party A's business information confidential.

2. Confidentiality Period
Party B shall keep confidentiality permanently.

3. Breach Liability
In case of breach, Party B shall pay a penalty of 10 million yuan.

4. Dispute Resolution
Both parties shall negotiate in good faith. If negotiation fails, submit to the court at Party A's location.
"""

    try:
        print("Reviewing contract...")
        result = await review_service.review_contract(
            contract_text=nda_contract,
            contract_type="NDA"
        )

        print(f"[PASS] Review completed!")
        print(f"\nReview Summary:")
        print(f"  - Risk clauses: {len(result.get('risk_clauses', []))}")
        print(f"  - Missing clauses: {len(result.get('missing_clauses', []))}")
        print(f"  - Suggestions: {len(result.get('suggestions', []))}")
        print(f"  - Legal references: {len(result.get('legal_references', []))}")
        print(f"  - Confidence score: {result.get('confidence_score', 0):.2f}")

        # 显示部分结果
        if result.get('risk_clauses'):
            print(f"\nRisk clauses examples:")
            for clause in result['risk_clauses'][:2]:
                title = clause.get('title', 'N/A')
                level = clause.get('risk_level', 'N/A')
                print(f"  - {title[:50]}... (Level: {level})")

        if result.get('missing_clauses'):
            print(f"\nMissing clauses examples:")
            for clause in result['missing_clauses'][:2]:
                print(f"  - {clause.get('title', 'N/A')}")

        return True

    except Exception as e:
        print(f"[FAIL] Review failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_labor_contract_review():
    """测试劳动合同审查"""
    print("\n" + "=" * 50)
    print("Test 3: Labor Contract Review")
    print("=" * 50)

    labor_contract = """
Labor Contract

Party A: XX Technology Co., Ltd.
Party B: Wang Wu

1. Contract Term
The contract term is 3 years, from January 1, 2024 to December 31, 2026.

2. Work Content
Party B shall serve as a software engineer.

3. Salary
Monthly salary is 20,000 yuan, probation period is 6 months, probation salary is 10,000 yuan.

4. Working Hours
Work 6 days a week, 8 hours per day.
"""

    try:
        print("Reviewing labor contract...")
        result = await review_service.review_contract(
            contract_text=labor_contract,
            contract_type="劳动合同"
        )

        print(f"[PASS] Review completed!")
        print(f"\nReview Summary:")
        print(f"  - Risk clauses: {len(result.get('risk_clauses', []))}")
        print(f"  - Missing clauses: {len(result.get('missing_clauses', []))}")
        print(f"  - Suggestions: {len(result.get('suggestions', []))}")
        print(f"  - Confidence score: {result.get('confidence_score', 0):.2f}")

        # 显示风险条款
        if result.get('risk_clauses'):
            print(f"\nRisk clauses found:")
            for clause in result['risk_clauses'][:3]:
                level = clause.get('risk_level', 'N/A').upper()
                title = clause.get('title', 'N/A')[:50]
                print(f"  - [{level}] {title}...")

        return True

    except Exception as e:
        print(f"[FAIL] Review failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("Phase 5 Contract Review - End-to-End Test")
    print(f"API Key: {zhipu_llm.api_key[:10]}...{zhipu_llm.api_key[-10:]}")
    print()

    # Initialize database connection
    print("Initializing database connection...")
    database.connect()
    print("[OK] Database connected\n")

    # 测试 1: LLM 连接
    llm_ok = await test_llm_connection()

    if not llm_ok:
        print("\n[FAIL] LLM connection failed, cannot continue")
        return

    # 测试 2: NDA 审查
    nda_ok = await test_review_service()

    # 测试 3: 劳动合同审查
    labor_ok = await test_labor_contract_review()

    # 总结
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"LLM Connection: {'[PASS]' if llm_ok else '[FAIL]'}")
    print(f"NDA Review: {'[PASS]' if nda_ok else '[FAIL]'}")
    print(f"Labor Contract Review: {'[PASS]' if labor_ok else '[FAIL]'}")

    if llm_ok and nda_ok and labor_ok:
        print("\n[SUCCESS] All tests passed! Phase 5 review is working")
    else:
        print("\n[WARNING] Some tests failed, please check configuration and code")


if __name__ == "__main__":
    asyncio.run(main())
