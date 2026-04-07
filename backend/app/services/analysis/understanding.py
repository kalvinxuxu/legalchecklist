"""
合同理解分析服务
协调结构分析和条款摘要生成（并行执行）
"""
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.client import zhipu_llm
from app.services.analysis.structure import structure_analysis_service
from app.services.analysis.summary import clause_summary_service
from app.db.session import db
from app.models.contract_understanding import ContractUnderstanding


class UnderstandingService:
    """合同理解分析服务"""

    async def generate_understanding(
        self,
        contract_id: str,
        contract_text: str,
        contract_type: str = "NDA",
        review_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        生成合同理解分析结果

        并行执行结构分析和条款摘要

        Args:
            contract_id: 合同 ID
            contract_text: 合同文本
            contract_type: 合同类型
            review_result: 审查结果（可选）

        Returns:
            理解分析结果
        """
        # 并行执行结构分析和条款摘要
        structure_task = structure_analysis_service.analyze_structure(
            contract_text, contract_type
        )
        summary_task = clause_summary_service.generate_summary(
            contract_text, contract_type, review_result
        )

        # 等待两者完成
        structure_result, summary_result = await asyncio.gather(
            structure_task,
            summary_task,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(structure_result, Exception):
            print(f"结构分析失败: {structure_result}")
            structure_result = {"sections": [], "structure_summary": "", "total_chapters": 0}

        if isinstance(summary_result, Exception):
            print(f"条款摘要失败: {summary_result}")
            summary_result = {"key_clauses": [], "payment_terms": {}, "breach_liability": {}, "quick_cards": {}}

        # 组合结果
        understanding_result = {
            "contract_id": contract_id,
            "contract_type": contract_type,
            "structure": {
                "sections": structure_result.get("sections", []),
                "structure_summary": structure_result.get("structure_summary", ""),
                "total_chapters": structure_result.get("total_chapters", 0),
            },
            "summary": {
                "key_clauses": summary_result.get("key_clauses", []),
                "payment_terms": summary_result.get("payment_terms", {}),
                "breach_liability": summary_result.get("breach_liability", {}),
            },
            "quick_cards": summary_result.get("quick_cards", {}),
        }

        # 保存到数据库
        await self._save_understanding(contract_id, understanding_result)

        return understanding_result

    async def get_understanding(
        self,
        contract_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取合同理解分析结果

        Args:
            contract_id: 合同 ID

        Returns:
            理解分析结果，如果不存在返回 None
        """
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(ContractUnderstanding)
                .where(ContractUnderstanding.contract_id == contract_id)
            )
            understanding = result.scalar_one_or_none()

            if not understanding:
                return None

            return {
                "contract_id": understanding.contract_id,
                "contract_type": understanding.contract_type,
                "structure": understanding.structure,
                "summary": understanding.summary,
                "quick_cards": understanding.quick_cards,
                "created_at": understanding.created_at.isoformat() if understanding.created_at else None,
            }

    async def _save_understanding(
        self,
        contract_id: str,
        understanding_result: Dict[str, Any]
    ) -> None:
        """保存理解分析结果到数据库"""
        async with db.async_session_maker() as session:
            # 检查是否已存在
            result = await session.execute(
                select(ContractUnderstanding)
                .where(ContractUnderstanding.contract_id == contract_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新
                existing.structure = understanding_result["structure"]
                existing.summary = understanding_result["summary"]
                existing.quick_cards = understanding_result["quick_cards"]
            else:
                # 创建
                understanding = ContractUnderstanding(
                    contract_id=contract_id,
                    contract_type=understanding_result["contract_type"],
                    structure=understanding_result["structure"],
                    summary=understanding_result["summary"],
                    quick_cards=understanding_result["quick_cards"],
                )
                session.add(understanding)

            await session.commit()


# 全局服务实例
understanding_service = UnderstandingService()
