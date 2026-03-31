"""
数据库模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


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


class ContentType(str, Enum):
    law = "law"
    case = "case"
    template = "template"
    rule = "rule"


# === Pydantic Models ===
class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plan: TenantPlan = TenantPlan.free


class TenantCreate(TenantBase):
    pass


class Tenant(TenantBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceCreate(WorkspaceBase):
    tenant_id: str


class Workspace(WorkspaceBase):
    id: str
    tenant_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.member


class UserCreate(UserBase):
    tenant_id: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class User(UserBase):
    id: str
    tenant_id: str
    wx_openid: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContractBase(BaseModel):
    file_name: str
    contract_type: Optional[ContractType] = None


class ContractCreate(ContractBase):
    workspace_id: str
    file_path: str
    file_hash: Optional[str] = None


class ContractUpdate(BaseModel):
    review_status: Optional[ReviewStatus] = None
    review_result: Optional[dict] = None
    risk_level: Optional[RiskLevel] = None


class Contract(ContractBase):
    id: str
    workspace_id: str
    user_id: str
    file_path: str
    file_hash: Optional[str] = None
    content_text: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.pending
    review_result: Optional[dict] = None
    risk_level: Optional[RiskLevel] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
