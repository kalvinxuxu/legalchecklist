"""
合同模型
"""
from sqlalchemy import Column, String, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, UUIDMixin, TimestampMixin


class ContractType(str, enum.Enum):
    """合同类型"""
    nda = "NDA"
    labor = "劳动合同"
    purchase = "采购合同"
    sales = "销售合同"
    service = "服务合同"
    other = "其他"


class ReviewStatus(str, enum.Enum):
    """审查状态"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RiskLevel(str, enum.Enum):
    """风险等级"""
    low = "low"
    medium = "medium"
    high = "high"


class Contract(Base, UUIDMixin, TimestampMixin):
    """合同表"""

    __tablename__ = "contracts"

    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        comment="工作区 ID"
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="上传用户 ID"
    )
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_hash = Column(String(64), nullable=True, index=True, comment="文件哈希（去重）")
    content_text = Column(Text, nullable=True, comment="解析后的文本内容")
    clauses_json = Column(JSON, nullable=True, comment="结构化条款（JSON）")
    contract_type = Column(Enum(ContractType), nullable=True, comment="合同类型")
    review_status = Column(
        Enum(ReviewStatus),
        default=ReviewStatus.pending,
        nullable=False,
        comment="审查状态"
    )
    review_result = Column(JSON, nullable=True, comment="审查结果（JSON）")
    review_error = Column(Text, nullable=True, comment="审查失败错误信息")
    risk_level = Column(Enum(RiskLevel), nullable=True, comment="风险等级")

    # 关联关系
    workspace = relationship("Workspace", back_populates="contracts")
    user = relationship("User", back_populates="contracts")
    understanding = relationship(
        "ContractUnderstanding",
        back_populates="contract",
        uselist=False,
        cascade="all, delete-orphan"
    )
    clause_locations = relationship(
        "ClauseLocation",
        back_populates="contract",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Contract(id={self.id}, file_name={self.file_name})>"
