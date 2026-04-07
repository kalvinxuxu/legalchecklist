"""
Celery 异步任务 - 合同审查
"""
import asyncio
import re
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.db.session import db
from app.models.contract import Contract, ReviewStatus as ReviewStatusEnum
from app.services.document.parser import document_parser
from app.services.review.service import review_service
from app.services.analysis.understanding import understanding_service
from app.services.pdf.reader import pdf_reader
from app.services.pdf.locator import clause_locator


def detect_contract_type(text: str) -> str:
    """
    从合同文本中自动检测合同类型

    Args:
        text: 合同文本内容

    Returns:
        检测到的合同类型
    """
    if not text:
        return "其他"

    # 转为小写用于关键词匹配
    text_lower = text.lower()

    # NDA/保密协议 检测
    nda_keywords = ["保密协议", "保密条款", "nda", "non-disclosure", "confidential", "保密义务", "商业秘密", "竞业限制"]
    if any(kw in text_lower for kw in nda_keywords):
        return "NDA"

    # 劳动合同 检测
    labor_keywords = ["劳动合同", "聘用合同", "雇佣合同", "员工", "雇主", "工资", "社会保险", "加班费", "年假", "试用期", "劳动合同法"]
    if any(kw in text_lower for kw in labor_keywords):
        return "劳动合同"

    # 采购合同 检测
    purchase_keywords = ["采购合同", "采购协议", "供货合同", "供货商", "货物买卖", "采购方", "供货方", "交货", "验收标准"]
    if any(kw in text_lower for kw in purchase_keywords):
        return "采购合同"

    # 销售合同 检测
    sales_keywords = ["销售合同", "销售协议", "买卖合同", "销售方", "购买方", "商品", "销售渠道", "代理商"]
    if any(kw in text_lower for kw in sales_keywords):
        return "销售合同"

    # 服务合同 检测
    service_keywords = ["服务合同", "服务协议", "咨询服务", "委托合同", "代理合同", "服务费", "服务内容", "服务质量"]
    if any(kw in text_lower for kw in service_keywords):
        return "服务合同"

    # 租赁合同 检测
    rental_keywords = ["租赁合同", "租赁协议", "房租", "租金", "出租人", "承租人", "租赁物", "押金"]
    if any(kw in text_lower for kw in rental_keywords):
        return "租赁合同"

    # 借款合同 检测
    loan_keywords = ["借款合同", "借款协议", "贷款合同", "借款人", "贷款人", "利息", "还款", "本金", "利率"]
    if any(kw in text_lower for kw in loan_keywords):
        return "借款合同"

    # 投资合同 检测
    investment_keywords = ["投资合同", "投资协议", "股权投资", "股权转让", "合伙人", "分红", "投资收益", "退出机制"]
    if any(kw in text_lower for kw in investment_keywords):
        return "投资合同"

    # 合作协议 检测
    cooperation_keywords = ["合作协议", "合作合同", "联合体", "合作方", "合作关系", "合作项目", "合作协议书"]
    if any(kw in text_lower for kw in cooperation_keywords):
        return "合作协议"

    return "其他"


@celery_app.task(bind=True, max_retries=3)
def process_contract_review_task(
    self,
    contract_id: str,
    file_path: str
) -> Dict[str, Any]:
    """
    处理合同审查异步任务

    Args:
        contract_id: 合同 ID
        file_path: 文件路径

    Returns:
        审查结果摘要
    """
    # 确保数据库连接已初始化
    if db.async_session_maker is None:
        db.connect()

    try:
        # 运行异步代码
        result = asyncio.run(_process_contract_review(contract_id, file_path))
        return result
    except Exception as exc:
        # 重试逻辑
        try:
            raise self.retry(exc=exc, countdown=60)
        except Exception as retry_exc:
            # 重试失败后，标记为失败
            asyncio.run(_mark_contract_as_failed(contract_id, str(retry_exc)))
            raise


async def _process_contract_review(
    contract_id: str,
    file_path: str
) -> Dict[str, Any]:
    """处理合同审查（异步内部实现）"""

    async with db.async_session_maker() as session:
        try:
            # 查询合同
            result = await session.execute(
                select(Contract).where(Contract.id == contract_id)
            )
            contract = result.scalar_one_or_none()

            if not contract:
                return {"error": "Contract not found"}

            # 1. 更新状态为 processing
            contract.review_status = ReviewStatusEnum.processing
            await session.commit()

            # 2. 解析文档
            if file_path.endswith(".pdf"):
                parse_result = await document_parser.parse_pdf(file_path)
            else:
                parse_result = await document_parser.parse_word(file_path)

            # 3. 更新合同内容
            contract.content_text = parse_result.get("text", "")

            # 4. 自动检测合同类型（如果未设置或为"其他"）
            original_type = contract.contract_type.value if contract.contract_type else "其他"
            if original_type == "其他":
                detected_type = detect_contract_type(contract.content_text)
                # 更新合同类型
                from app.models.contract import ContractType as ContractTypeEnum
                contract.contract_type = ContractTypeEnum(detected_type)
                contract_type_str = detected_type
            else:
                contract_type_str = original_type

            await session.commit()

            # 5. 执行审查
            review_result = await review_service.review_contract(
                contract_text=contract.content_text,
                contract_type=contract_type_str
            )

            # 6. 启动理解分析（传入审查结果以便更好地生成摘要）
            # 使用 create_task 并添加错误处理，避免静默失败
            async def run_understanding_with_logging():
                try:
                    print(f"[理解分析] 开始为合同 {contract_id} 生成理解分析...")
                    result = await understanding_service.generate_understanding(
                        contract_id=contract_id,
                        contract_text=contract.content_text,
                        contract_type=contract_type_str,
                        review_result=review_result
                    )
                    print(f"[理解分析] 完成合同 {contract_id} 的理解分析")
                    return result
                except Exception as e:
                    print(f"[理解分析] 合同 {contract_id} 理解分析失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return None

            asyncio.create_task(run_understanding_with_logging())

            # 7. 确定风险等级
            risk_clauses = review_result.get("risk_clauses", [])
            if any(c.get("risk_level") == "high" for c in risk_clauses):
                risk_level = "high"
            elif any(c.get("risk_level") == "medium" for c in risk_clauses):
                risk_level = "medium"
            else:
                risk_level = "low"

            # 8. 保存审查结果
            contract.review_result = review_result
            contract.risk_level = risk_level
            contract.review_status = ReviewStatusEnum.completed

            await session.commit()

            # 9. PDF 条款定位（仅 PDF 文件，且审查有风险条款）
            if file_path.endswith(".pdf") and risk_clauses:
                asyncio.create_task(
                    _locate_clauses_in_pdf(contract_id, file_path, risk_clauses)
                )

            return {
                "contract_id": contract_id,
                "status": "completed",
                "risk_level": risk_level,
                "risk_clauses_count": len(risk_clauses),
                "missing_clauses_count": len(review_result.get("missing_clauses", []))
            }

        except Exception as e:
            # 处理失败
            if contract:
                contract.review_status = ReviewStatusEnum.failed
                contract.review_error = str(e)
                await session.commit()
            raise e


async def _locate_clauses_in_pdf(
    contract_id: str,
    file_path: str,
    risk_clauses: list
) -> None:
    """在 PDF 中定位风险条款"""
    try:
        # 提取 PDF 文本和位置
        pdf_data = pdf_reader.extract_text_with_positions(file_path)

        # 检查是否需要 OCR
        if pdf_data.get("needs_ocr") and pdf_data.get("has_text") is False:
            # 尝试 OCR
            pdf_data = await pdf_reader.extract_with_ocr(file_path)

        text_positions = pdf_data.get("text_positions", [])
        is_ocr = pdf_data.get("source") == "ocr"

        # 批量定位条款
        clause_texts = [c.get("original_text", "") for c in risk_clauses[:10]]  # 限制前10条
        locations = clause_locator.batch_locate(
            clause_texts,
            text_positions,
            is_ocr=is_ocr,
            ocr_result=pdf_data if is_ocr else None
        )

        # 保存定位结果
        from app.models.clause_location import ClauseLocation
        from app.models.contract_understanding import ContractUnderstanding

        async with db.async_session_maker() as session:
            # 获取理解分析结果 ID
            result = await session.execute(
                select(ContractUnderstanding)
                .where(ContractUnderstanding.contract_id == contract_id)
            )
            understanding = result.scalar_one_or_none()
            understanding_id = understanding.id if understanding else None

            for i, clause in enumerate(risk_clauses[:10]):
                clause_locations = locations[i] if i < len(locations) else []

                for loc in clause_locations:
                    bbox = loc.get("bbox")
                    clause_loc = ClauseLocation(
                        contract_id=contract_id,
                        understanding_id=understanding_id,
                        clause_hash=str(abs(hash(clause.get("original_text", "")))[:16]),
                        clause_title=clause.get("title", ""),
                        clause_text=clause.get("original_text", ""),
                        risk_level=clause.get("risk_level", "medium"),
                        page_number=loc.get("page"),
                        bbox_x0=bbox.get("x0") if bbox else None,
                        bbox_y0=bbox.get("y0") if bbox else None,
                        bbox_x1=bbox.get("x1") if bbox else None,
                        bbox_y1=bbox.get("y1") if bbox else None,
                        similarity=loc.get("similarity"),
                        match_type=loc.get("match_type"),
                    )
                    session.add(clause_loc)

            await session.commit()

    except Exception as e:
        print(f"条款定位失败: {e}")


async def _mark_contract_as_failed(contract_id: str, error: str) -> None:
    """标记合同审查失败"""
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = result.scalar_one_or_none()

        if contract:
            contract.review_status = ReviewStatusEnum.failed
            contract.review_error = error
            await session.commit()
