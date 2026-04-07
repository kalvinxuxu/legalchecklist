"""
租户隔离中间件测试

验证跨租户访问被正确阻止。
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant, TenantPlan
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.models.contract import Contract
from app.core.security import get_password_hash


@pytest.fixture
async def test_tenant_a(db_session: AsyncSession):
    """创建测试租户 A"""
    tenant = Tenant(
        id="tenant-a-0000-0000-000000000000",
        name="测试租户 A",
        plan=TenantPlan.free,
        contract_quota=10,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_tenant_b(db_session: AsyncSession):
    """创建测试租户 B"""
    tenant = Tenant(
        id="tenant-b-0000-0000-000000000000",
        name="测试租户 B",
        plan=TenantPlan.free,
        contract_quota=10,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user_a(db_session: AsyncSession, test_tenant_a):
    """创建租户 A 的用户"""
    user = User(
        id="user-a-0000-0000-0000-000000000000",
        tenant_id=test_tenant_a.id,
        email="user_a@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_b(db_session: AsyncSession, test_tenant_b):
    """创建租户 B 的用户"""
    user = User(
        id="user-b-0000-0000-000000000000",
        tenant_id=test_tenant_b.id,
        email="user_b@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_workspace_a(db_session: AsyncSession, test_tenant_a):
    """创建租户 A 的工作区"""
    workspace = Workspace(
        id="workspace-a-0000-0000-000000000000",
        tenant_id=test_tenant_a.id,
        name="租户 A 工作区",
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest.fixture
async def test_workspace_b(db_session: AsyncSession, test_tenant_b):
    """创建租户 B 的工作区"""
    workspace = Workspace(
        id="workspace-b-0000-0000-000000000000",
        tenant_id=test_tenant_b.id,
        name="租户 B 工作区",
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest.fixture
async def test_contract_a(db_session: AsyncSession, test_workspace_a, test_user_a):
    """创建租户 A 的合同"""
    from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum

    contract = Contract(
        id="contract-a-0000-0000-000000000000",
        workspace_id=test_workspace_a.id,
        user_id=test_user_a.id,
        file_name="租户 A 合同.pdf",
        file_path="/path/to/contract_a.pdf",
        file_hash="hash_a",
        contract_type=ContractTypeEnum.other,
        review_status=ReviewStatusEnum.completed,
        review_result={"risk_clauses": []},
        risk_level="low",
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


@pytest.fixture
async def test_contract_b(db_session: AsyncSession, test_workspace_b, test_user_b):
    """创建租户 B 的合同"""
    from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum

    contract = Contract(
        id="contract-b-0000-0000-000000000000",
        workspace_id=test_workspace_b.id,
        user_id=test_user_b.id,
        file_name="租户 B 合同.pdf",
        file_path="/path/to/contract_b.pdf",
        file_hash="hash_b",
        contract_type=ContractTypeEnum.other,
        review_status=ReviewStatusEnum.completed,
        review_result={"risk_clauses": []},
        risk_level="low",
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user_a):
    """获取租户 A 用户的认证头"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_a.email,
            "password": "password123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestTenantIsolation:
    """测试租户隔离功能"""

    async def test_user_cannot_access_other_tenant_workspace(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_workspace_b: Workspace
    ):
        """测试租户 A 用户无法访问租户 B 的工作区"""
        response = await client.get(
            f"/api/v1/workspaces/{test_workspace_b.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "无权访问" in response.json()["detail"]

    async def test_user_can_access_own_tenant_workspace(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_workspace_a: Workspace
    ):
        """测试租户 A 用户可以访问租户 A 的工作区"""
        response = await client.get(
            f"/api/v1/workspaces/{test_workspace_a.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == test_workspace_a.id

    async def test_user_cannot_create_workspace_in_other_tenant(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_tenant_b: Tenant
    ):
        """测试租户 A 用户无法在租户 B 下创建工作区"""
        response = await client.post(
            "/api/v1/workspaces/",
            headers=auth_headers,
            json={
                "tenant_id": test_tenant_b.id,
                "name": "非法工作区"
            }
        )
        assert response.status_code == 403

    async def test_list_workspaces_only_returns_own_tenant(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_workspace_a: Workspace,
        test_workspace_b: Workspace
    ):
        """测试工作区列表只返回当前租户的数据"""
        response = await client.get(
            "/api/v1/workspaces/",
            headers=auth_headers
        )
        assert response.status_code == 200
        workspaces = response.json()
        workspace_ids = [w["id"] for w in workspaces]

        assert test_workspace_a.id in workspace_ids
        assert test_workspace_b.id not in workspace_ids

    async def test_unauthorized_access_returns_401(
        self,
        client: AsyncClient,
        test_workspace_a: Workspace
    ):
        """测试未授权访问返回 401/403"""
        response = await client.get(
            f"/api/v1/workspaces/{test_workspace_a.id}"
        )
        # FastAPI 的 HTTPBearer 在未提供 token 时返回 403
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestContractTenantIsolation:
    """测试合同 API 的租户隔离功能"""

    async def test_user_cannot_access_other_tenant_contract(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_contract_b: Contract
    ):
        """测试租户 A 用户无法访问租户 B 的合同"""
        response = await client.get(
            f"/api/v1/contracts/{test_contract_b.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "无权访问" in response.json()["detail"]

    async def test_user_can_access_own_tenant_contract(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_contract_a: Contract
    ):
        """测试租户 A 用户可以访问租户 A 的合同"""
        response = await client.get(
            f"/api/v1/contracts/{test_contract_a.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == test_contract_a.id

    async def test_user_cannot_delete_other_tenant_contract(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_contract_b: Contract
    ):
        """测试租户 A 用户无法删除租户 B 的合同"""
        response = await client.delete(
            f"/api/v1/contracts/{test_contract_b.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "无权访问" in response.json()["detail"]

    async def test_list_contracts_only_returns_own_tenant(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_contract_a: Contract,
        test_contract_b: Contract
    ):
        """测试合同列表只返回当前租户的数据"""
        response = await client.get(
            "/api/v1/contracts/",
            headers=auth_headers
        )
        assert response.status_code == 200
        contracts = response.json()
        contract_ids = [c["id"] for c in contracts]

        assert test_contract_a.id in contract_ids
        assert test_contract_b.id not in contract_ids

    async def test_user_cannot_access_other_tenant_review_result(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_contract_b: Contract
    ):
        """测试租户 A 用户无法访问租户 B 合同的审查结果"""
        response = await client.get(
            f"/api/v1/contracts/{test_contract_b.id}/review",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "无权访问" in response.json()["detail"]


@pytest.mark.asyncio
class TestAuthTenantIsolation:
    """测试认证 API 的租户隔离功能"""

    async def test_get_me_returns_own_tenant_info(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user_a: User
    ):
        """测试获取用户信息返回正确的租户信息"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["tenant_id"] == test_user_a.tenant_id
        assert user_data["email"] == test_user_a.email

    async def test_unauthorized_access_to_me(
        self,
        client: AsyncClient
    ):
        """测试未授权访问 /me 端点"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]
