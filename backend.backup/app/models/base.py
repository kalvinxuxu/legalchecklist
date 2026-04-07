"""
SQLAlchemy 基础类
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import VARCHAR


Base = declarative_base()


class TimestampMixin:
    """时间戳混合类"""
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )


class UUIDMixin:
    """UUID 主键混合类"""
    id = Column(
        VARCHAR(36),
        primary_key=True,
        default=lambda: __import__('uuid').uuid4().__str__(),
        comment="主键 ID"
    )
