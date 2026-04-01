"""
Celery 异步任务 - 合同审查
"""
import asyncio
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.db.session import db
from app.models.contract import Contract, ReviewStatusEnum
from app.services.document.parser import document_parser
from app.services.review.service import review_service


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

            # 4. 执行审查
            contract_type_str = contract.contract_type.value if contract.contract_type else "其他"
            review_result = await review_service.review_contract(
                contract_text=contract.content_text,
                contract_type=contract_type_str
            )

            # 5. 确定风险等级
            risk_clauses = review_result.get("risk_clauses", [])
            if any(c.get("risk_level") == "high" for c in risk_clauses):
                risk_level = "high"
            elif any(c.get("risk_level") == "medium" for c in risk_clauses):
                risk_level = "medium"
            else:
                risk_level = "low"

            # 6. 保存审查结果
            contract.review_result = review_result
            contract.risk_level = risk_level
            contract.review_status = ReviewStatusEnum.completed

            await session.commit()

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
