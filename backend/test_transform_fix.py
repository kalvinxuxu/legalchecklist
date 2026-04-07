"""
直接测试 review_service 的转换功能
"""
import asyncio
import sys
import json
sys.path.append('.')

from app.services.review.service import review_service

# 模拟 LLM 返回的审查结果（旧格式，没有 title）
mock_llm_result = {
    "risk_clauses": [
        {
            "original_text": "这是一段很长的原文超过 50 个字符所以会被截断作为标题显示出来看看效果怎么样",
            "risk_description": "这个条款存在法律风险因为...",
            "risk_level": "high",
            "suggestion": "建议修改为...",
            "legal_reference": "《民法典》第 XXX 条"
        },
        {
            "original_text": "",
            "risk_description": "",
            "risk_level": "medium",
            "suggestion": "建议添加违约责任条款",
            "legal_reference": ""
        },
        {
            "original_text": "",
            "risk_description": "缺少保密期限约定",
            "risk_level": "low",
            "suggestion": "建议添加 2-5 年的保密期限",
            "legal_reference": "《民法典》第 XXX 条"
        }
    ],
    "missing_clauses": [
        {
            "title": "保密期限条款",
            "description": "合同未规定保密期限",
            "suggestion": "建议添加 2-5 年的保密期限",
            "legal_reference": "《民法典》第 XXX 条"
        }
    ],
    "suggestions": [
        {
            "title": "添加违约责任条款",
            "content": "建议在合同中添加违约责任条款",
            "reason": "明确违约责任有助于合同纠纷的解决"
        }
    ],
    "legal_references": [
        {
            "law_name": "民法典",
            "article": "第 500 条",
            "content": "当事人一方不履行合同义务..."
        }
    ]
}

print("原始 LLM 结果（risk_clauses 没有 title）:")
print(json.dumps(mock_llm_result["risk_clauses"][0], ensure_ascii=False, indent=2))
print()

# 调用转换方法
transformed = review_service._transform_review_result(mock_llm_result)

print("转换后的结果（risk_clauses 应该有 title）:")
print(json.dumps(transformed["risk_clauses"][0], ensure_ascii=False, indent=2))
print()
print("第二条（original_text 为空，使用 risk_description 生成 title）:")
print(json.dumps(transformed["risk_clauses"][1], ensure_ascii=False, indent=2))
print()
print("第三条（original_text 和 risk_description 都为空，使用默认标题）:")
print(json.dumps(transformed["risk_clauses"][2], ensure_ascii=False, indent=2))
