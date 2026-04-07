"""
工作区模型
"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Workspace(Base, UUIDMixin, TimestampMixin):
    """工作区表 - 每个租户默认一个工作区"""

    __tablename__ = "workspaces"

    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="租户 ID（1:1）"
    )
    name = Column(String(255), default="默认工作区", nullable=False, comment="工作区名称")

    # 关联关系
    tenant = relationship("Tenant", back_populates="workspace")
    contracts = relationship("Contract", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workspace(id={self.id}, name={self.name})>"
