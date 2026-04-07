"""
用户模型
"""
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """用户角色"""
    admin = "admin"
    member = "member"


class User(Base, UUIDMixin, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="租户 ID"
    )
    email = Column(String(255), unique=True, nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    role = Column(
        Enum(UserRole),
        default=UserRole.member,
        nullable=False,
        comment="用户角色"
    )
    wx_openid = Column(String(100), nullable=True, comment="微信 OpenID（预留）")

    # 关联关系
    tenant = relationship("Tenant", back_populates="users")
    contracts = relationship("Contract", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
