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
    name: Optional[str] = None
    role: UserRole = UserRole.member


class UserCreate(BaseSchema):
    email: str
    password: str = Field(..., min_length=6)
    name: Optional[str] = Field(None, max_length=100, description="用户姓名")
    company_name: Optional[str] = Field(None, max_length=255, description="公司名称")


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


# === Review Config Schema (审查立场配置) ===
class ReviewConfig(BaseModel):
    """审查立场配置 - 用于「站在你这边的 AI 法务」功能"""
    party_position: Optional[str] = Field(
        default=None,
        description="甲乙方立场：party_a=甲方，party_b=乙方"
    )
    contract_amount: Optional[float] = Field(
        default=None,
        description="合同金额（元）"
    )
    risk_preference: Optional[str] = Field(
        default=None,
        description="风险偏好：low=低，medium=中，high=高"
    )

    class Config:
        from_attributes = True


# === Auth Schemas ===
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserWithTenant(UserBase):
    """包含租户信息的用户模型"""
    id: str
    tenant_id: str
    created_at: datetime
    tenant: Optional["TenantResponse"] = None

    class Config:
        from_attributes = True


class TokenWithUser(BaseModel):
    """包含用户信息的 Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserWithTenant  # 直接引用，不使用前向引用


class TokenData(BaseModel):
    user_id: Optional[str] = None


# === Export Review Report Schema ===
class ExportReviewOptions(BaseModel):
    """导出审查报告选项"""
    include_risk_clauses: bool = Field(default=True, description="包含风险条款批注")
    include_missing_clauses: bool = Field(default=True, description="包含缺失条款批注")
    include_suggestions: bool = Field(default=True, description="包含修改建议批注")
    include_rule_judgments: bool = Field(default=True, description="包含规则判定结果")
    include_policy_references: bool = Field(default=True, description="包含政策参考")
    comment_format: str = Field(default="standard", description="批注格式: standard | compact")

    class Config:
        from_attributes = True


