"""
合同管理 API
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
import aiomysql
import hashlib

from app.db.session import get_db
from app.schemas import Contract, ContractCreate, ContractUpdate, ReviewStatus
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def calculate_file_hash(file_bytes: bytes) -> str:
    """计算文件哈希值（用于去重）"""
    return hashlib.sha256(file_bytes).hexdigest()


@router.post("/upload", response_model=Contract)
async def upload_contract(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    contract_type: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: aiomysql.Connection = Depends(get_db)
):
    """上传合同文件"""
    # 验证工作区权限
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            SELECT w.id FROM workspaces w
            JOIN users u ON u.tenant_id = w.tenant_id
            WHERE w.id = %s AND u.id = %s
            """,
            (workspace_id, current_user["id"])
        )
        if not await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该工作区"
            )

    # 读取文件内容
    file_bytes = await file.read()
    file_hash = calculate_file_hash(file_bytes)

    # 检查是否已存在相同文件
    async with db.cursor() as cursor:
        await cursor.execute(
            "SELECT id FROM contracts WHERE file_hash = %s AND workspace_id = %s",
            (file_hash, workspace_id)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该文件已上传过"
            )

    # 保存文件（本地存储，生产环境使用 OSS）
    from app.core.config import settings
    import os
    from pathlib import Path

    upload_dir = Path(settings.STORAGE_PATH) / workspace_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 创建合同记录
    contract_id = str(uuid.uuid4())

    async with db.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO contracts
            (id, workspace_id, user_id, file_name, file_path, file_hash, contract_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                contract_id, workspace_id, current_user["id"],
                file.filename, str(file_path), file_hash, contract_type
            )
        )
        await db.commit()

    return {
        "id": contract_id,
        "workspace_id": workspace_id,
        "user_id": current_user["id"],
        "file_name": file.filename,
        "file_path": str(file_path),
        "file_hash": file_hash,
        "contract_type": contract_type,
        "review_status": ReviewStatus.pending,
        "created_at": None,
        "updated_at": None,
    }


@router.get("/", response_model=List[Contract])
async def list_contracts(
    workspace_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: aiomysql.Connection = Depends(get_db)
):
    """获取合同列表"""
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            SELECT c.* FROM contracts c
            JOIN workspaces w ON c.workspace_id = w.id
            JOIN users u ON u.tenant_id = w.tenant_id
            WHERE w.id = %s AND u.id = %s
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (workspace_id, current_user["id"], limit, offset)
        )
        contracts = await cursor.fetchall()

    return [dict(c) for c in contracts]


@router.get("/{contract_id}", response_model=Contract)
async def get_contract(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
    db: aiomysql.Connection = Depends(get_db)
):
    """获取合同详情"""
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            SELECT c.* FROM contracts c
            JOIN workspaces w ON c.workspace_id = w.id
            JOIN users u ON u.tenant_id = w.tenant_id
            WHERE c.id = %s AND w.id = %s AND u.id = %s
            """,
            (contract_id, current_user.get("workspace_id"), current_user["id"])
        )
        contract = await cursor.fetchone()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权访问"
            )

    return dict(contract)
