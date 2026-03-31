"""
认证相关 API
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import aiomysql

from app.core.security import create_access_token, get_password_hash, decode_access_token
from app.db.session import get_db
from app.schemas import (
    UserCreate, UserLogin, User, Token,
    TenantCreate, Tenant, WorkspaceCreate, Workspace
)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: aiomysql.Connection = Depends(get_db)
) -> dict:
    """获取当前登录用户"""
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

    async with db.cursor() as cursor:
        await cursor.execute(
            "SELECT id, tenant_id, email, role, wx_openid FROM users WHERE id = %s",
            (user_id,)
        )
        user = await cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )

    return dict(user)


@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate,
    db: aiomysql.Connection = Depends(get_db)
):
    """用户注册"""
    async with db.cursor() as cursor:
        # 检查邮箱是否已存在
        await cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (user_in.email,)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        user_id = str(uuid.uuid4())
        password_hash = get_password_hash(user_in.password)

        await cursor.execute(
            """
            INSERT INTO users (id, tenant_id, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, user_in.tenant_id, user_in.email, password_hash, user_in.role.value)
        )
        await db.commit()

    # 生成 Token
    access_token = create_access_token(data={"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: aiomysql.Connection = Depends(get_db)
):
    """用户登录"""
    from app.core.security import verify_password

    async with db.cursor() as cursor:
        await cursor.execute(
            "SELECT id, password_hash FROM users WHERE email = %s",
            (credentials.email,)
        )
        user = await cursor.fetchone()

        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )

    # 生成 Token
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user
