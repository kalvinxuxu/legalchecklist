"""
认证相关 API
"""
import uuid
import traceback
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
from app.db.session import get_db
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.models.tenant import Tenant, TenantPlan
from app.models.user import User as UserModel, UserRole
from app.models.workspace import Workspace

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    """获取当前登录用户"""
    from app.core.security import decode_access_token

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效"
        )

    # 查询用户
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.tenant))
        .where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


@router.get("/test-llm")
async def test_llm_connection():
    """
    测试 LLM API 连接（无需认证）

    用于诊断审查报告无法生成的问题
    """
    from app.services.llm.client import zhipu_llm

    try:
        result = await zhipu_llm.chat_with_json_output([
            {"role": "user", "content": '{"status": "ok", "message": "LLM connection successful"}'}
        ])
        return {
            "status": "success",
            "message": "LLM API connection successful",
            "result": result
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"LLM API call failed: {str(e)}",
            "traceback": traceback.format_exc()
        }


@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册 - 自动创建租户"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # 检查邮箱是否已存在
        result = await db.execute(
            select(UserModel).where(UserModel.email == user_in.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 生成 ID
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        logger.info(f"Registering new user: {user_in.email}, tenant_id: {tenant_id}")

        password_hash = get_password_hash(user_in.password)

        # 创建租户
        tenant = Tenant(
            id=tenant_id,
            name=f"{user_in.email.split('@')[0]} 的租户",  # 默认租户名
            plan=TenantPlan.free,
            contract_quota=10,
        )
        db.add(tenant)

        # 创建用户
        user = UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=user_in.email,
            password_hash=password_hash,
            role=UserRole.admin,  # 首个用户为管理员
        )
        db.add(user)

        # 创建默认工作区
        workspace = Workspace(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name="默认工作区",
        )
        db.add(workspace)

        # 提交事务
        await db.commit()
        logger.info(f"User registered successfully: {user_in.email}")

        # 生成 Token
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed for {user_in.email}: {e}\n{traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    from app.core.security import verify_password

    # 查询用户
    result = await db.execute(
        select(UserModel).where(UserModel.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 生成 Token
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserModel = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user
