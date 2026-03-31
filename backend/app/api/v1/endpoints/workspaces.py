"""
工作区管理 API
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import aiomysql

from app.db.session import get_db
from app.schemas import Workspace, WorkspaceCreate
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[Workspace])
async def list_workspaces(
    current_user: dict = Depends(get_current_user),
    db: aiomysql.Connection = Depends(get_db)
):
    """获取当前租户下的所有工作区"""
    tenant_id = current_user["tenant_id"]

    async with db.cursor() as cursor:
        await cursor.execute(
            "SELECT id, tenant_id, name, created_at FROM workspaces WHERE tenant_id = %s",
            (tenant_id,)
        )
        workspaces = await cursor.fetchall()

    return [dict(ws) for ws in workspaces]


@router.post("/", response_model=Workspace)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: dict = Depends(get_current_user),
    db: aiomysql.Connection = Depends(get_db)
):
    """创建工作区"""
    # 验证租户 ID 是否匹配
    if workspace_in.tenant_id != current_user["tenant_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权在该租户下创建工作区"
        )

    workspace_id = str(uuid.uuid4())

    async with db.cursor() as cursor:
        await cursor.execute(
            """
            INSERT INTO workspaces (id, tenant_id, name)
            VALUES (%s, %s, %s)
            """,
            (workspace_id, workspace_in.tenant_id, workspace_in.name)
        )
        await db.commit()

    return {
        "id": workspace_id,
        "tenant_id": workspace_in.tenant_id,
        "name": workspace_in.name,
        "created_at": None  # 可从数据库重新查询
    }


@router.get("/{workspace_id}", response_model=Workspace)
async def get_workspace(
    workspace_id: str,
    current_user: dict = Depends(get_current_user),
    db: aiomysql.Connection = Depends(get_db)
):
    """获取工作区详情"""
    async with db.cursor() as cursor:
        await cursor.execute(
            """
            SELECT w.id, w.tenant_id, w.name, w.created_at
            FROM workspaces w
            JOIN users u ON u.tenant_id = w.tenant_id
            WHERE w.id = %s AND u.id = %s
            """,
            (workspace_id, current_user["id"])
        )
        workspace = await cursor.fetchone()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作区不存在或无权访问"
            )

    return dict(workspace)
