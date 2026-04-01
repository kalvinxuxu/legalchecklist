"""
合同管理 API

使用租户隔离中间件确保所有操作都在当前租户范围内。
"""
import uuid
import hashlib
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db, db
from app.schemas import ContractResponse, ContractCreate, ReviewStatus, ContractType
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant_isolation import verify_contract_access, verify_workspace_access
from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum
from app.models.workspace import Workspace
from app.models.user import User as UserModel
from app.core.config import settings
from app.services.document.parser import document_parser
from app.services.review import review_service

# Celery 任务导入（条件导入）
if settings.USE_CELERY:
    from app.services.review.tasks import process_contract_review_task

router = APIRouter()


def calculate_file_hash(file_bytes: bytes) -> str:
    """计算文件哈希值（用于去重）"""
    return hashlib.sha256(file_bytes).hexdigest()


def trigger_contract_review(contract_id: str, file_path: str) -> None:
    """
    触发合同审查任务

    根据配置使用 Celery 或 asyncio 后台任务
    """
    if settings.USE_CELERY:
        # 使用 Celery 异步任务
        process_contract_review_task.delay(contract_id, file_path)
    else:
        # 使用 asyncio 后台任务（开发环境）
        import asyncio
        asyncio.create_task(process_contract_upload(contract_id, file_path))


async def process_contract_upload(
    contract_id: str,
    file_path: str
):
    """
    处理合同上传：解析和审查

    后续将迁移到 Celery 异步任务
    """
    # 创建新的数据库会话
    async with db.async_session_maker() as session:
        try:
            # 查询合同
            result = await session.execute(
                select(Contract).where(Contract.id == contract_id)
            )
            contract = result.scalar_one_or_none()

            if not contract:
                return

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

        except Exception as e:
            # 处理失败
            if contract:
                contract.review_status = ReviewStatusEnum.failed
                contract.review_error = str(e)
                await session.commit()
            raise e


@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    contract_type: str | None = Form(None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传合同文件"""
    # 验证文件类型
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
            trigger_contract_review(existing_contract.id, existing_contract.file_path)
        return existing_contract

    # 保存文件（本地存储，生产环境使用 OSS）
    upload_dir = Path(settings.STORAGE_PATH) / workspace_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    file_path = upload_dir / f"{file_id}.{file_extension}"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 解析合同类型
    contract_type_enum = None
    if contract_type:
        try:
            contract_type_enum = ContractTypeEnum(contract_type)
        except ValueError:
            contract_type_enum = ContractTypeEnum.other

    # 创建合同记录
    contract = Contract(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        user_id=current_user.id,
        file_name=file.filename,
        file_path=str(file_path),
        file_hash=file_hash,
        contract_type=contract_type_enum,
        review_status=ReviewStatusEnum.pending,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    # 异步处理合同（解析 + 审查）
    # 使用 Celery 或 asyncio 后台任务
    trigger_contract_review(contract.id, str(file_path))

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


@router.delete("/{contract_id}")
async def delete_contract(
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """删除合同"""
    await db.delete(contract)
    await db.commit()
    return {"message": "删除成功"}


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
