"""
Pydantic schemas
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# === Base Config for Pydantic v2 ===
class BaseSchema(BaseModel):
    """基础 Schema，配置 Pydantic v2 行为"""
    model_config = ConfigDict(
        extra='ignore'  # 忽略额外字段
    )


# === Enums ===
class TenantPlan(str, Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class UserRole(str, Enum):
    admin = "admin"
    member = "member"


class ContractType(str, Enum):
    nda = "NDA"
    labor = "劳动合同"
    purchase = "采购合同"
    sales = "销售合同"
    service = "服务合同"
    other = "其他"


class ReviewStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# === Tenant Schemas ===
class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plan: TenantPlan = TenantPlan.free


class TenantCreate(TenantBase):
    pass


class TenantResponse(TenantBase):
    id: str
    contract_quota: int
    created_at: datetime

    class Config:
        from_attributes = True


# === Workspace Schemas ===
class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceCreate(WorkspaceBase):
    tenant_id: str


class WorkspaceResponse(WorkspaceBase):
    id: str
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# === User Schemas ===
class UserBase(BaseSchema):
    email: str
    role: UserRole = UserRole.member


class UserCreate(BaseSchema):
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseSchema):
    email: str
    password: str


class UserResponse(UserBase):
    id: str
    tenant_id: str
    created_at: datetime
    tenant: Optional[TenantResponse] = None

    class Config:
        from_attributes = True


# === Contract Schemas ===
class ContractBase(BaseModel):
    file_name: str
    contract_type: Optional[ContractType] = None


class ContractCreate(ContractBase):
    workspace_id: str
    file_path: str


class ContractUpdate(BaseModel):
    review_status: Optional[ReviewStatus] = None
    review_result: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None


class ContractResponse(ContractBase):
    id: str
    workspace_id: str
    user_id: Optional[str] = None
    file_path: str
    content_text: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.pending
    review_result: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Auth Schemas ===
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
