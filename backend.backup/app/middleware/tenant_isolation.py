"""
租户隔离中间件

确保所有 API 请求只能访问当前租户的数据。
通过 FastAPI 依赖注入实现租户上下文提取和权限验证。
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.models.user import User as UserModel
from app.models.tenant import Tenant
from app.api.v1.endpoints.auth import get_current_user


class TenantIsolationError(HTTPException):
    """租户隔离验证失败异常"""
    def __init__(self, detail: str = "无权访问该资源"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_current_tenant(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """
    获取当前用户所属的租户

    验证租户是否存在且有效。
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="租户不存在"
        )

    return tenant


def require_tenant_match(resource_tenant_id_attr: str = "tenant_id"):
    """
    验证资源属于当前用户所在的租户

    用于单资源访问场景（如获取合同详情、删除工作区等）。

    Args:
        resource_tenant_id_attr: 资源对象中表示租户 ID 的属性名

    Returns:
        依赖注入函数，验证通过后返回资源对象
    """
    async def validator(
        resource: any,
        current_user: UserModel = Depends(get_current_user)
    ) -> any:
        """验证资源租户 ID 与当前用户租户 ID 匹配"""
        resource_tenant_id = getattr(resource, resource_tenant_id_attr, None)

        if resource_tenant_id is None:
            raise TenantIsolationError("资源缺少租户标识")

        if str(resource_tenant_id) != str(current_user.tenant_id):
            raise TenantIsolationError("无权访问其他租户的资源")

        return resource

    return validator


async def verify_workspace_access(
    workspace_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> any:
    """
    验证用户是否有权访问指定工作区

    自动在查询中加入租户隔离条件，防止 ID 遍历攻击。
    """
    from app.models.workspace import Workspace

    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.tenant_id == current_user.tenant_id
        )
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作区不存在或无权访问"
        )

    return workspace


async def verify_contract_access(
    contract_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> any:
    """
    验证用户是否有权访问指定合同

    自动在查询中加入租户隔离条件（通过工作区关联）。
    """
    from app.models.contract import Contract
    from app.models.workspace import Workspace

    # 通过工作区关联确保租户隔离
    result = await db.execute(
        select(Contract)
        .join(Workspace)
        .where(
            Contract.id == contract_id,
            Workspace.tenant_id == current_user.tenant_id
        )
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在或无权访问"
        )

    return contract


def get_tenant_query_filter(
    current_user: UserModel = Depends(get_current_user)
) -> any:
    """
    获取租户过滤条件

    用于列表查询场景，确保只返回当前租户的数据。

    使用示例:
        filter_fn = get_tenant_query_filter(current_user)
        # 在查询中使用
        result = await db.execute(
            select(Contract).where(filter_fn(Contract))
        )
    """
    def filter_by_tenant(model_class: any) -> any:
        """返回适用于该模型的租户过滤条件"""
        if hasattr(model_class, "tenant_id"):
            return model_class.tenant_id == current_user.tenant_id
        elif hasattr(model_class, "workspace_id"):
            # 对于合同等通过工作区关联的模型
            from app.models.workspace import Workspace
            return model_class.workspace_id.in_(
                select(Workspace.id).where(
                    Workspace.tenant_id == current_user.tenant_id
                )
            )
        else:
            raise TenantIsolationError(f"模型 {model_class.__name__} 不支持租户隔离")

    return filter_by_tenant
