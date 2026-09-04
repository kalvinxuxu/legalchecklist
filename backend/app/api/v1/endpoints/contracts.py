"""
合同管理 API

使用租户隔离中间件确保所有操作都在当前租户范围内。
"""
import asyncio
import uuid
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db, db
from app.schemas import ContractResponse, ContractCreate, ReviewStatus, ContractType
from app.schemas import ReviewConfig  # 审查立场配置
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant_isolation import verify_contract_access, verify_workspace_access
from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum
from app.models.workspace import Workspace
from app.models.user import User as UserModel
from app.models.review_run import ReviewRun, ReviewStep, ReviewRunStatus, ReviewStepStatus
from app.core.config import settings
from app.services.review import review_service

router = APIRouter()


def _review_run_payload(run: ReviewRun, steps: list) -> dict:
    from app.services.review.durable_graph import STAGE_LABELS
    return {
        "run_id": run.id,
        "status": run.status.value,
        "current_stage": run.current_stage,
        "stage_label": STAGE_LABELS.get(run.current_stage) if run.current_stage else None,
        "progress": 100 if run.status == ReviewRunStatus.completed else run.progress,
        "attempt": run.attempt,
        "last_heartbeat_at": run.last_heartbeat_at,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "last_error": run.last_error,
        "resumable_from": run.current_stage if run.status in {ReviewRunStatus.failed, ReviewRunStatus.stalled} else None,
        "steps": [
            {
                "stage": step.stage,
                "stage_label": STAGE_LABELS.get(step.stage),
                "status": step.status.value,
                "attempt": step.attempt,
                "started_at": step.started_at,
                "completed_at": step.completed_at,
                "error": step.error,
                "metadata": step.step_metadata,
            }
            for step in steps
        ],
    }



def resolve_contract_file_path(file_path: str) -> Path:
    """
    解析合同文件路径，支持相对路径和绝对路径

    相对路径：相对于 STORAGE_PATH
    绝对路径：直接使用
    """
    path_obj = Path(file_path)
    if path_obj.is_absolute():
        return path_obj

    # 检查是否已经包含 STORAGE_PATH（避免双重路径）
    normalized_path = path_obj.as_posix() if hasattr(path_obj, 'as_posix') else str(path_obj)
    storage_posix = Path(settings.STORAGE_PATH).as_posix()

    if normalized_path.startswith(storage_posix):
        # 路径已经包含 STORAGE_PATH，直接返回
        return path_obj

    return Path(settings.STORAGE_PATH) / file_path


def calculate_file_hash(file_bytes: bytes) -> str:
    """计算文件哈希值（用于去重）"""
    return hashlib.sha256(file_bytes).hexdigest()


def detect_contract_type(text: str) -> str:
    """
    从合同文本中自动检测合同类型
    """
    if not text:
        return "其他"

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


@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    contract_type: str | None = Form(None),
    # 审查立场配置
    party_position: str | None = Form(None),
    contract_amount: float | None = Form(None),
    risk_preference: str | None = Form(None),
    # 是否自动触发审查，默认为 True（保持向后兼容）
    # 注意：FormData 发送的是字符串，需要手动转换布尔值
    auto_review_str: str = Form('true'),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传合同文件"""
    # 将字符串 'true'/'false' 转换为布尔值
    auto_review = auto_review_str.lower() == 'true'

    # 验证文件扩展名
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    allowed_extensions = ["pdf", "docx"]
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式，请上传 .pdf 或 .docx 格式文件（不支持 .doc 格式）"
        )

    # 验证文件 MIME 类型
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，请上传 PDF 或 Word 文件"
        )

    # 验证工作区权限
    result = await db.execute(
        select(Workspace)
        .join(UserModel, UserModel.tenant_id == Workspace.tenant_id)
        .where(Workspace.id == workspace_id, UserModel.id == current_user.id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该工作区"
        )

    # 读取文件内容
    file_bytes = await file.read()
    file_hash = calculate_file_hash(file_bytes)

    # 检查是否已存在相同文件
    result = await db.execute(
        select(Contract).where(
            Contract.file_hash == file_hash,
            Contract.workspace_id == workspace_id
        )
    )
    existing_contract = result.scalar_one_or_none()
    if existing_contract:
        # 如果旧合同未完成审查，重新启动审查
        if existing_contract.review_status != ReviewStatusEnum.completed:
            from app.services.review.durable_graph import create_review_run
            await create_review_run(existing_contract.id)
        return existing_contract

    # 保存文件（本地存储，生产环境使用 OSS）
    # 使用相对路径存储在数据库中，确保在不同环境下都能正确解析
    upload_dir = Path(settings.STORAGE_PATH) / workspace_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    file_path = upload_dir / f"{file_id}.{file_extension}"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 存储相对路径（相对于 STORAGE_PATH），便于跨环境迁移
    # 例如：workspace_id/file_id.ext
    relative_file_path = str(Path(workspace_id) / f"{file_id}.{file_extension}")

    # 解析合同类型
    contract_type_enum = None
    if contract_type:
        try:
            contract_type_enum = ContractTypeEnum(contract_type)
        except ValueError:
            contract_type_enum = ContractTypeEnum.other

    # 审查立场配置
    review_config = {}
    if party_position or contract_amount or risk_preference:
        review_config = {
            "party_position": party_position,
            "contract_amount": contract_amount,
            "risk_preference": risk_preference
        }

    # 创建合同记录
    contract = Contract(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        user_id=current_user.id,
        file_name=file.filename,
        file_path=relative_file_path,  # 使用相对路径，便于跨环境迁移
        file_hash=file_hash,
        contract_type=contract_type_enum,
        review_status=ReviewStatusEnum.pending,
        review_config=review_config,  # 保存审查立场配置
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

# 根据 auto_review 参数决定是否创建持久化审查任务
    if auto_review:
        from app.services.review.durable_graph import create_review_run
        await create_review_run(contract.id)

    return contract


@router.get("/", response_model=list[ContractResponse])
async def list_contracts(
    limit: int = 20,
    offset: int = 0,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前租户下的所有合同"""
    result = await db.execute(
        select(Contract)
        .join(Workspace, Contract.workspace_id == Workspace.id)
        .where(
            Workspace.tenant_id == current_user.tenant_id
        )
        .order_by(Contract.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    contracts = result.scalars().all()
    return contracts


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同详情"""
    return contract


@router.get("/{contract_id}/file")
async def get_contract_file(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同原始文件（用于PDF预览）"""
    from fastapi.responses import FileResponse, StreamingResponse

    if not contract.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )

    # 解析文件路径（使用公共函数）
    file_path = resolve_contract_file_path(contract.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {file_path}"
        )

    # 根据文件扩展名确定 media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=contract.file_name
    )


@router.delete("/{contract_id}")
async def delete_contract(
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """删除合同"""
    await db.delete(contract)
    await db.commit()
    return {"message": "删除成功"}


@router.patch("/{contract_id}/type")
async def update_contract_type(
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db),
    contract_type: str = None
):
    """更新合同类型"""
    if contract_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="合同类型不能为空"
        )

    try:
        contract_type_enum = ContractTypeEnum(contract_type)
    except ValueError:
        # 如果不是预定义类型，设置为 other
        contract_type_enum = ContractTypeEnum.other

    contract.contract_type = contract_type_enum
    await db.commit()
    await db.refresh(contract)
    return {"message": "更新成功", "contract_type": contract.contract_type.value}


@router.post("/{contract_id}/review-config")
async def update_review_config(
    config: ReviewConfig,
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """
    更新审查立场配置（甲乙方立场、合同金额、风险偏好）

    配置后将用于 AI 审查，实现「站在你这边的 AI 法务」功能
    """
    # 保存配置到数据库
    config_dict = {
        "party_position": config.party_position,
        "contract_amount": config.contract_amount,
        "risk_preference": config.risk_preference
    }
    contract.review_config = config_dict
    await db.commit()

    return {
        "message": "配置已保存",
        "config": config_dict
    }


@router.get("/{contract_id}/review-config")
async def get_review_config(
    contract: Contract = Depends(verify_contract_access)
):
    """获取审查立场配置"""
    return {
        "party_position": contract.review_config.get("party_position") if contract.review_config else None,
        "contract_amount": contract.review_config.get("contract_amount") if contract.review_config else None,
        "risk_preference": contract.review_config.get("risk_preference") if contract.review_config else None
    }


@router.post("/{contract_id}/review/start")
async def start_review(
    contract: Contract = Depends(verify_contract_access),
    db_session: AsyncSession = Depends(get_db),
):
    """Create a durable review run; execution is owned by review_worker."""
    from app.services.review.durable_graph import create_review_run
    run = await create_review_run(contract.id, force_new=contract.review_status == ReviewStatusEnum.completed)
    contract.review_status = ReviewStatusEnum.pending
    contract.review_error = None
    await db_session.commit()
    return {"message": "审查任务已排队", "status": run.status.value, "run_id": run.id}


@router.post("/{contract_id}/review/resume")
async def resume_review(
    contract: Contract = Depends(verify_contract_access),
    db_session: AsyncSession = Depends(get_db),
):
    """Resume the latest failed or stalled review from its LangGraph checkpoint."""
    from app.services.review.durable_graph import create_review_run
    run = await create_review_run(contract.id)
    if run.status not in {ReviewRunStatus.failed, ReviewRunStatus.stalled, ReviewRunStatus.queued}:
        raise HTTPException(status_code=409, detail="当前审查任务正在运行")
    run.status = ReviewRunStatus.queued
    run.last_error = None
    contract.review_status = ReviewStatusEnum.pending
    contract.review_error = None
    await db_session.commit()
    return {"message": "已从断点排队恢复", "status": run.status.value, "run_id": run.id}


@router.post("/{contract_id}/review/retry-stage")
async def retry_review_stage(
    contract_id: str,
    stage: str,
    contract: Contract = Depends(verify_contract_access),
    db_session: AsyncSession = Depends(get_db),
):
    """Retry the current failed/stalled stage without discarding earlier checkpoints."""
    from app.services.review.durable_graph import STAGES, create_review_run
    if stage not in STAGES:
        raise HTTPException(status_code=400, detail="无效的审查阶段")
    run = await create_review_run(contract.id)
    if run.status not in {ReviewRunStatus.failed, ReviewRunStatus.stalled}:
        raise HTTPException(status_code=409, detail="当前任务不可重试阶段")
    step_result = await db_session.execute(select(ReviewStep).where(ReviewStep.run_id == run.id))
    steps = {step.stage: step for step in step_result.scalars().all()}
    selected = steps.get(stage)
    if not selected or selected.status not in {ReviewStepStatus.failed, ReviewStepStatus.waiting}:
        raise HTTPException(status_code=400, detail="只能重试失败或待执行阶段")
    run.status = ReviewRunStatus.queued
    run.current_stage = stage
    run.last_error = None
    for name in STAGES[STAGES.index(stage):]:
        if name in steps:
            steps[name].status = ReviewStepStatus.waiting
            steps[name].error = None
            steps[name].started_at = None
            steps[name].completed_at = None
    contract.review_status = ReviewStatusEnum.pending
    contract.review_error = None
    await db_session.commit()
    return {"message": "阶段已重新排队", "status": run.status.value, "run_id": run.id, "stage": stage}


@router.post("/{contract_id}/rerun-review")
async def rerun_review(
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """
    重新审查合同（使用当前配置的立场）
    """
    import logging
    import os
    from app.services.review.durable_graph import create_review_run
    logger = logging.getLogger(__name__)

    # 检查文件是否存在
    file_path = str(resolve_contract_file_path(contract.file_path))
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件不存在或已被删除，无法重新审查"
        )

    # 更新状态为 pending，并交给持久化 worker 执行
    contract.review_status = ReviewStatusEnum.pending
    contract.review_result = None  # 清除旧结果
    contract.review_error = None
    await db.commit()

    run = await create_review_run(contract.id)
    logger.info(f"[Rerun] Review queued for contract {contract.id}, run={run.id}")
    return {"message": "重新审查已排队", "status": run.status.value, "run_id": run.id}


@router.get("/{contract_id}/review", response_model=dict)
async def get_review_result(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同审查结果"""
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


@router.get("/{contract_id}/review-status")
async def get_review_status(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取合同审查详细状态（用于调试）

    返回审查进度、错误信息等
    """
    async with db.async_session_maker() as session:
        from app.models.document import DocumentRecord, DocumentVersion
        document_record = (await session.execute(select(DocumentRecord).where(DocumentRecord.contract_id == contract.id))).scalar_one_or_none()
        document_version = await session.get(DocumentVersion, document_record.current_version_id) if document_record and document_record.current_version_id else None
        run_result = await session.execute(
            select(ReviewRun)
            .where(ReviewRun.contract_id == contract.id)
            .order_by(ReviewRun.created_at.desc())
            .limit(1)
        )
        run = run_result.scalars().first()
        if run:
            step_result = await session.execute(
                select(ReviewStep).where(ReviewStep.run_id == run.id).order_by(ReviewStep.created_at)
            )
            payload = _review_run_payload(run, step_result.scalars().all())
            if run.started_at:
                payload["elapsed_seconds"] = max(0, int(((run.completed_at or datetime.utcnow()) - run.started_at).total_seconds()))
            else:
                payload["elapsed_seconds"] = 0
            payload.update({
                "contract_id": contract.id,
                "file_name": contract.file_name,
                "review_status": contract.review_status.value,
                "content_text_length": len(contract.content_text) if contract.content_text else 0,
                "review_result_keys": list(contract.review_result.keys()) if contract.review_result else None,
                "review_error": contract.review_error or run.last_error,
                "contract_type": contract.contract_type.value if contract.contract_type else None,
                "document_id": document_record.id if document_record else None,
                "document_version_id": document_version.id if document_version else None,
                "document_status": document_version.status if document_version else "not_started",
            })
            return payload

    # Legacy contracts created before durable runs existed.
    return {
        "contract_id": contract.id,
        "file_name": contract.file_name,
        "file_path": contract.file_path,
        "review_status": contract.review_status.value,
        "risk_level": contract.risk_level.value if contract.risk_level else None,
        "content_text_length": len(contract.content_text) if contract.content_text else 0,
        "review_result_keys": list(contract.review_result.keys()) if contract.review_result else None,
        "review_error": contract.review_error,
        "contract_type": contract.contract_type.value if contract.contract_type else None,
        "document_id": None,
        "document_version_id": None,
        "document_status": "not_started",
        "status": contract.review_status.value,
        "current_stage": None,
        "stage_label": None,
        "progress": 100 if contract.review_status == ReviewStatusEnum.completed else 0,
        "steps": [],
    }


@router.get("/{contract_id}/understanding")
async def get_contract_understanding(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同理解分析结果"""
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.analysis.understanding import understanding_service
    understanding = await understanding_service.get_understanding(contract.id)

    if not understanding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到理解分析结果，请稍后重试"
        )

    return understanding


@router.get("/{contract_id}/clause-locations")
async def get_clause_locations(
    contract: Contract = Depends(verify_contract_access)
):
    """获取条款 PDF 定位信息"""
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from sqlalchemy import select
    from app.models.clause_location import ClauseLocation

    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract.id)
            .order_by(ClauseLocation.page_number)
        )
        locations = result.scalars().all()

        return [
            {
                "clause_title": loc.clause_title,
                "clause_text": loc.clause_text,
                "risk_level": loc.risk_level,
                "page": loc.page_number,
                "bbox": loc.bbox,
                "similarity": loc.similarity,
                "match_type": loc.match_type,
                "evidence_id": (loc.extra_data or {}).get("evidence_id"),
                "document_id": (loc.extra_data or {}).get("document_id"),
                "version_id": (loc.extra_data or {}).get("version_id"),
                "coord_system": "pdf_top_left",
                "resolution_status": "resolved" if loc.bbox else "page_only",
                "locations": [{"page": loc.page_number, "bbox": loc.bbox, "coord_system": "pdf_top_left",
                               "resolution_status": "resolved" if loc.bbox else "page_only"}],
            }
            for loc in locations
        ]


@router.get("/{contract_id}/evidence/{evidence_id}")
async def get_evidence_location(
    evidence_id: str,
    contract: Contract = Depends(verify_contract_access),
):
    """Resolve one review evidence ID to all of its PDF locations."""
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="合同尚未完成审查")
    from app.services.document.evidence_navigation import get_evidence_locations
    return await get_evidence_locations(contract.id, evidence_id)


@router.get("/{contract_id}/pdf-positions")
async def get_pdf_text_positions(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取 PDF 文本位置信息（用于前端渲染高亮）

    返回:
    - text_positions: 文本位置列表
    - clause_locations: 条款高亮位置
    """
    if not contract.file_path.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 文件"
        )

    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.pdf.reader import pdf_reader
    from sqlalchemy import select
    from app.models.clause_location import ClauseLocation

    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    # 提取 PDF 文本和位置
    pdf_data = pdf_reader.extract_text_with_positions(resolved_file_path)

    # 如果文本过少，尝试 OCR
    if pdf_data.get("needs_ocr"):
        pdf_data = await pdf_reader.extract_with_ocr(resolved_file_path)

    # 获取条款定位
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract.id)
        )
        locations = result.scalars().all()

    return {
        "text_positions": pdf_data.get("text_positions", []),
        "pages": pdf_data.get("pages", 0),
        "has_text": pdf_data.get("has_text", False),
        "needs_ocr": pdf_data.get("needs_ocr", True),
        "source": pdf_data.get("source", "pymupdf"),
        "clause_locations": [
            {
                "clause_title": loc.clause_title,
                "clause_text": loc.clause_text,
                "risk_level": loc.risk_level,
                "page": loc.page_number,
                "bbox": loc.bbox,
                "evidence_id": (loc.extra_data or {}).get("evidence_id"),
                "document_id": (loc.extra_data or {}).get("document_id"),
                "version_id": (loc.extra_data or {}).get("version_id"),
                "coord_system": "pdf_top_left",
                "resolution_status": "resolved" if loc.bbox else "page_only",
                "locations": [{"page": loc.page_number, "bbox": loc.bbox, "coord_system": "pdf_top_left",
                               "resolution_status": "resolved" if loc.bbox else "page_only"}],
            }
            for loc in locations
        ]
    }


@router.get("/{contract_id}/highlighted-pdf")
async def get_highlighted_pdf(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取高亮 PDF 文件流

    用于在线查看高亮后的 PDF
    """
    if not contract.file_path.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 文件"
        )

    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.pdf.highlighter import pdf_highlighter
    from sqlalchemy import select
    from app.models.clause_location import ClauseLocation

    # 获取条款定位
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract.id)
        )
        locations = result.scalars().all()

    # 构建高亮位置列表
    clause_positions = []
    for loc in locations:
        bbox = loc.bbox
        if bbox:
            clause_positions.append({
                "text": loc.clause_text,
                "page": loc.page_number,
                "bbox": bbox,
                "risk_level": loc.risk_level,
                "clause_id": loc.id,
            })

    # 生成高亮 PDF
    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    if clause_positions:
        pdf_bytes = pdf_highlighter.highlight_clauses(
            resolved_file_path,
            clause_positions
        )
    else:
        # 无定位信息，返回原始 PDF
        with open(resolved_file_path, "rb") as f:
            pdf_bytes = f.read()

    from fastapi.responses import StreamingResponse
    import io

    # 使用纯英文文件名避免编码问题
    safe_filename = "highlighted_contract.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={safe_filename}"
        }
    )


# ========== Word 辅助编辑 API ==========

@router.get("/{contract_id}/word-paragraphs")
async def get_word_paragraphs(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取 Word 文档的段落列表（带索引）

    用于前端渲染原文并进行风险高亮定位
    """
    if not contract.file_path.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word (.docx) 文件"
        )

    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.word import word_indexer

    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    result = await word_indexer.parse_word_paragraphs(
        resolved_file_path,
        contract.id
    )

    return result


@router.post("/{contract_id}/apply-suggestions")
async def apply_word_suggestions(
    suggestions: List[Dict[str, Any]],
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """
    采纳建议并生成修订后的 Word 文档

    Request Body:
        suggestions: 采纳的建议列表
            [{
                "paragraph_index": 5,
                "original_text": "原文本",
                "new_text": "修改后文本",
                "risk_description": "风险描述",
                "accepted": true
            }]

    Returns:
        生成后的修订 Word 文件字节流
    """
    if not contract.file_path.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word (.docx) 文件"
        )

    # 过滤已采纳的建议
    accepted_suggestions = [
        s for s in suggestions if s.get("accepted", False)
    ]

    if not accepted_suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有需要采纳的建议"
        )

    from app.services.word import revision_doc_generator

    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    # 生成修订文档
    revised_bytes = revision_doc_generator.apply_suggestions_to_document(
        resolved_file_path,
        accepted_suggestions
    )

    # 临时保存修订文档（可选，也可以直接返回）
    import uuid
    revised_file_name = f"revised_{uuid.uuid4().hex[:8]}_{contract.file_name}"
    revised_file_path = Path(settings.STORAGE_PATH) / "revisions" / revised_file_name
    revised_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(revised_file_path, "wb") as f:
        f.write(revised_bytes)

    # 更新合同记录修订文件路径（可选）
    # contract.revised_file_path = str(revised_file_path)
    # await db.commit()

    from fastapi.responses import StreamingResponse
    import io
    from urllib.parse import quote

    # URL-encode filename for Content-Disposition header
    encoded_filename = quote(revised_file_name)

    return StreamingResponse(
        io.BytesIO(revised_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/{contract_id}/revised-word")
async def get_revised_word(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取已生成的修订 Word 文档

    如果有已采纳的建议，返回修订后的文档流
    """
    if not contract.file_path.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word (.docx) 文件"
        )

    # 检查是否存在修订文档
    revised_dir = Path(settings.STORAGE_PATH) / "revisions"
    revised_pattern = f"revised_*_{contract.file_name}"

    revised_files = list(revised_dir.glob(revised_pattern))

    if not revised_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到修订文档，请先采纳建议并生成"
        )

    # 返回最新的修订文档
    latest_revised = max(revised_files, key=lambda p: p.stat().st_mtime)

    with open(latest_revised, "rb") as f:
        revised_bytes = f.read()

    from fastapi.responses import StreamingResponse
    import io

    revised_file_name = f"修订版_{contract.file_name}"

    from urllib.parse import quote
    encoded_filename = quote(revised_file_name)

    return StreamingResponse(
        io.BytesIO(revised_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.post("/{contract_id}/export-review-report")
async def export_review_report(
    options: Dict[str, Any],
    contract: Contract = Depends(verify_contract_access)
):
    """
    导出审查报告为 Word 文档

    支持两种导出模式:
    - export_type="review_report": 结构化审查报告（默认）
    - export_type="original_with_comments": 原文+审批批注（仅限.docx文件）

    审查报告模式支持:
    - 风险条款
    - 缺失条款
    - 修改建议
    - 规则判定结果
    - 政策参考
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

    from fastapi.responses import StreamingResponse
    import io
    from urllib.parse import quote
    import logging

    logger = logging.getLogger(__name__)

    export_type = options.get("export_type", "review_report")
    logger.info(f"[Export] export_type={export_type}, file_path={contract.file_path}")

    # 原文+审批批注模式（仅限.docx文件）
    if export_type == "original_with_comments":
        if not contract.file_path.endswith(".docx"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原文+审批批注功能仅支持 Word (.docx) 文件"
            )

        from app.services.word import revision_doc_generator
        from app.api.v1.endpoints.contracts import resolve_contract_file_path

        # 解析文件路径
        resolved_file_path = str(resolve_contract_file_path(contract.file_path))

        # 生成带批注的文档
        revised_bytes = revision_doc_generator.add_review_comments_to_document(
            resolved_file_path,
            contract.review_result
        )

        # 生成文件名
        safe_filename = f"批注版_{contract.file_name}"
        encoded_filename = quote(safe_filename)

        return StreamingResponse(
            io.BytesIO(revised_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    # 默认：审查报告模式
    from app.services.word import review_report_exporter

    # 生成审查报告
    report_bytes = review_report_exporter.generate_review_report(
        contract.file_name,
        contract.review_result,
        options
    )

    # 生成报告文件名
    safe_filename = f"审查报告_{contract.file_name.replace('.pdf', '').replace('.docx', '')}.docx"
    encoded_filename = quote(safe_filename)

    return StreamingResponse(
        io.BytesIO(report_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
