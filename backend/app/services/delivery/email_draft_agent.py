"""Company legal counsel agent for concise, evidence-grounded email drafts."""
import json
from typing import Any
from app.services.llm.client import zhipu_llm

SYSTEM_PROMPT = """你是公司法务部的合同审查邮件草拟专员。
请把输入的已完成审查结果整理成发给业务方的邮件。
只使用输入事实，不得编造风险、法条或合同内容；语气严谨、简练；正文必须使用 bullet points，分别列出主要风险和修改意见；有 evidence_id 时保留引用。
严格输出 JSON：{"subject":"...","body_text":"..."}，不要输出代码围栏。"""


def _fallback(contract_name: str, opinion: dict[str, Any]) -> dict[str, str]:
    risks = opinion.get("risk_clauses", [])
    recommendations = opinion.get("recommendations", [])
    lines = ["您好，", "", f"关于《{contract_name}》的合同审查意见如下：", "", "主要风险："]
    for item in risks[:8]:
        title = item.get("title") or "未命名风险条款"
        detail = item.get("risk_description") or item.get("description") or "请结合原文核查。"
        evidence = f"（证据：{item['evidence_id']}）" if item.get("evidence_id") else ""
        lines.append(f"- {title}：{detail}{evidence}")
    if not risks:
        lines.append("- 未发现需要重点说明的风险条款，请结合完整审查报告复核。")
    lines.append("")
    lines.append("修改意见：")
    for item in recommendations[:8]:
        title = item.get("title") or "合同修改建议"
        content = item.get("content") or item.get("suggestion") or "请根据审查报告调整相关条款。"
        lines.append(f"- {title}：{content}")
    if not recommendations:
        lines.append("- 请根据上述风险条款逐项完成修改并复核。")
    lines.extend(["", "请查收附件《审查意见》并据此修改合同。", "如需进一步讨论，请联系法务。"])
    return {"subject": f"《{contract_name}》合同审查意见", "body_text": "\n".join(lines)}


async def draft_email(contract_name: str, opinion: dict[str, Any]) -> dict[str, str]:
    fallback = _fallback(contract_name, opinion)
    prompt = json.dumps({"contract_name": contract_name, "overall_risk_level": opinion.get("overall_risk_level"),
                         "risk_clauses": opinion.get("risk_clauses", [])[:8],
                         "recommendations": opinion.get("recommendations", [])[:8],
                         "missing_clauses": opinion.get("missing_clauses", [])[:5]}, ensure_ascii=False)
    try:
        result = await zhipu_llm.chat_with_json_output([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], temperature=0.2)
        subject, body = str(result.get("subject", "")).strip(), str(result.get("body_text", "")).strip()
        if subject and body and "主要风险" in body and "修改意见" in body:
            return {"subject": subject, "body_text": body}
    except Exception:
        pass
    return fallback
