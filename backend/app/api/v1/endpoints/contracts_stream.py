"""
合同审查 API - 流式输出
"""
import asyncio
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db, db
from app.schemas import ContractResponse, ContractType
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant_isolation import verify_contract_access
from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum
from app.models.workspace import Workspace
from app.models.user import User as UserModel
from app.core.config import settings
from app.services.review.stream_service import review_stream_service
from app.services.understanding import understanding_service
from app.services.streaming import streaming_service

router = APIRouter()


def calculate_file_hash(file_bytes: bytes) -> str:
    """计算文件哈希值（用于去重）"""
    return hashlib.sha256(file_bytes).hexdigest()


@router.get("/{contract_id}/review-stream")
async def stream_contract_review(
    contract: Contract = Depends(verify_contract_access)
):
    """
    流式获取合同审查报告

    使用 SSE (Server-Sent Events) 流式输出审查结果
    """
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    if not contract.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同内容为空，请先上传文件"
        )

    contract_type = contract.contract_type.value if contract.contract_type else "其他"

    # 使用流式审查服务
    async def generate():
        try:
            async for event in review_stream_service.review_contract_stream(
                contract_text=contract.content_text,
                contract_type=contract_type
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    import json
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{contract_id}/understand-stream")
async def stream_contract_understanding(
    contract: Contract = Depends(verify_contract_access)
):
    """
    流式获取合同理解分析

    包括：摘要、关键条款、风险因素
    """
    if not contract.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同内容为空"
        )

    contract_type = contract.contract_type.value if contract.contract_type else "其他"

    import json

    async def generate():
        try:
            # 1. 发送摘要
            yield f"data: {json.dumps({'type': 'section', 'title': 'start', 'content': '开始分析合同结构...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            async for section in understanding_service.generate_summary_stream(
                contract_text=contract.content_text,
                contract_type=contract_type
            ):
                yield f"data: {json.dumps(section, ensure_ascii=False)}\n\n"

            # 2. 发送关键条款
            yield f"data: {json.dumps({'type': 'section', 'title': 'clauses', 'content': '正在提取关键条款...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            async for clause in understanding_service.extract_key_clauses_stream(
                contract_text=contract.content_text,
                contract_type=contract_type
            ):
                yield f"data: {json.dumps(clause, ensure_ascii=False)}\n\n"

            # 3. 发送风险因素
            yield f"data: {json.dumps({'type': 'section', 'title': 'risks', 'content': '正在分析风险因素...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            async for risk in understanding_service.analyze_risk_factors_stream(
                contract_text=contract.content_text,
                contract_type=contract_type
            ):
                yield f"data: {json.dumps(risk, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{contract_id}/qa")
async def ask_contract_question(
    contract: Contract = Depends(verify_contract_access),
    question: str = Query(..., min_length=1, max_length=500),
    db: AsyncSession = Depends(get_db)
):
    """
    问答接口 - 基于合同内容回答问题
    """
    if not contract.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同内容为空"
        )

    contract_type = contract.contract_type.value if contract.contract_type else "其他"

    try:
        answer = await understanding_service.answer_question(
            question=question,
            contract_text=contract.content_text,
            contract_type=contract_type
        )
        return {"question": question, "answer": answer}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"问答生成失败: {str(e)}"
        )


# 保留原有的非流式端点以兼容
@router.get("/{contract_id}/review")
async def get_review_result(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取合同审查结果（非流式）
    """
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    if not contract.review_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到审查结果"
        )

    return contract.review_result
