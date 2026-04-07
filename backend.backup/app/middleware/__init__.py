"""
租户隔离中间件

提供租户上下文提取和权限验证的依赖注入函数。
"""
from app.middleware.tenant_isolation import (
    TenantIsolationError,
    get_current_tenant,
    require_tenant_match,
    verify_workspace_access,
    verify_contract_access,
    get_tenant_query_filter,
)

__all__ = [
    "TenantIsolationError",
    "get_current_tenant",
    "require_tenant_match",
    "verify_workspace_access",
    "verify_contract_access",
    "get_tenant_query_filter",
]
