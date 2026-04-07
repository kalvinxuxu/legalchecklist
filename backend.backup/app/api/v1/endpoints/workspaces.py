"""
工作区管理 API

使用租户隔离中间件确保所有操作都在当前租户范围内。
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas import WorkspaceResponse, WorkspaceCreate
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant_isolation import verify_workspace_access
from app.models.workspace import Workspace
from app.models.user import User as UserModel

router = APIRouter()


@router.get("/", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前租户下的所有工作区"""
    result = await db.execute(
        select(Workspace).where(Workspace.tenant_id == current_user.tenant_id)
    )
    workspaces = result.scalars().all()
    return workspaces


@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建工作区"""
    # 验证租户 ID 是否匹配
    if workspace_in.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权在该租户下创建工作区"
        )

    workspace = Workspace(
        id=str(uuid.uuid4()),
        tenant_id=workspace_in.tenant_id,
        name=workspace_in.name,
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace: Workspace = Depends(verify_workspace_access)
):
    """获取工作区详情"""
    return workspace
