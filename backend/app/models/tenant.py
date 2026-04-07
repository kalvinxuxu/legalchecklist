"""
租户模型
"""
from sqlalchemy import Column, String, Integer, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class TenantPlan(str, enum.Enum):
    """租户套餐类型"""
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class Tenant(Base, UUIDMixin, TimestampMixin):
    """租户表 - 每个企业客户"""

    __tablename__ = "tenants"

    name = Column(String(255), nullable=False, comment="租户名称")
    plan = Column(
        Enum(TenantPlan),
        default=TenantPlan.free,
        nullable=False,
        comment="套餐类型"
    )
    contract_quota = Column(Integer, default=10, nullable=False, comment="合同数量限制")

    # 关联关系
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    workspace = relationship("Workspace", back_populates="tenant", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, plan={self.plan})>"
